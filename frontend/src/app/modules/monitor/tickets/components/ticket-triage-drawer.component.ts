import { Component, Input, Output, EventEmitter, inject, signal, effect, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { TranslatePipe } from '../../../../shared/pipes/translate.pipe';
import { Ticket, TicketStatus } from '../../../../core/models/support.types';
import { SupportService } from '../../../../core/services/support.service';
import { AdminUser, AdminService } from '../../../../core/services/admin.service';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-ticket-triage-drawer',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, TranslatePipe],
  template: `
    @if (ticket) {
      <div class="fixed inset-0 z-[999] overflow-hidden" aria-labelledby="slide-over-title" role="dialog" aria-modal="true">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-surface-bg/30 backdrop-blur-sm transition-opacity" (click)="close.emit()" aria-hidden="true"></div>

        <div class="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
          <div class="pointer-events-auto w-screen max-w-md transform transition-transform ease-in-out duration-300 translate-x-0 bg-surface-card border-l border-surface-border shadow-2xl flex flex-col h-full overflow-hidden">
            
            <!-- Header -->
            <div class="px-6 py-5 border-b border-surface-border bg-surface-card/50 backdrop-blur-md flex items-start justify-between">
              <div>
                <div class="flex items-center gap-2 mb-1">
                  <h2 class="text-lg font-black text-surface-text" id="slide-over-title">
                    {{ ticket.reference_code || ('#TKT-' + ticket.id.slice(-4).toUpperCase()) }}
                  </h2>
                  <span class="px-2 py-0.5 rounded-md text-[9px] font-black tracking-widest uppercase"
                        [ngClass]="{
                          'bg-sky-500/10 text-sky-500 border border-sky-500/20': ticket.status === TicketStatus.NEW,
                          'bg-amber-500/10 text-amber-500 border border-amber-500/20': ticket.status === TicketStatus.PENDING_APPROVAL
                        }">
                    {{ ticket.status }}
                  </span>
                </div>
                <p class="text-xs text-surface-text-muted italic">{{ ticket.title }}</p>
              </div>
              <div class="ml-3 flex h-7 items-center">
                <button type="button" class="rounded-md text-surface-text-muted hover:text-surface-text focus:outline-none" (click)="close.emit()">
                  <span class="sr-only">Close panel</span>
                  <mat-icon>close</mat-icon>
                </button>
              </div>
            </div>

            <!-- Content -->
            <div class="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar flex flex-col gap-6">
              
              <!-- Detalles del Ticket -->
              <div class="bg-surface-text/[0.02] border border-surface-border rounded-xl p-4">
                <h3 class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest mb-3">
                  {{ 'support.dashboard.details' | translate:'DETALLES DE INCIDENCIA' }}
                </h3>
                <p class="text-sm text-surface-text leading-relaxed mb-4">{{ ticket.description }}</p>
                <div class="flex flex-wrap gap-4 text-xs">
                  <div>
                    <span class="block text-[9px] font-black text-surface-text-muted uppercase tracking-widest mb-1">Prioridad</span>
                    <span class="font-bold" [ngClass]="getPriorityColor(ticket.priority)">{{ ticket.priority }}</span>
                  </div>
                  <div>
                    <span class="block text-[9px] font-black text-surface-text-muted uppercase tracking-widest mb-1">Tipo</span>
                    <span class="font-bold text-surface-text">{{ ticket.ticket_type }}</span>
                  </div>
                </div>
              </div>

              <!-- Sección de Triaje -->
              @if (isTriageable) {
                <div>
                  <h3 class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest mb-3 flex items-center gap-1">
                    <mat-icon class="text-[14px]">psychology</mat-icon> 
                    {{ 'support.dashboard.triage_action' | translate:'TRIAJE OPERATIVO' }}
                  </h3>

                  @if (ticket.status === TicketStatus.PENDING_APPROVAL) {
                    <!-- Aprobar Solicitud Existente -->
                    <div class="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 flex flex-col gap-4">
                      <p class="text-xs text-surface-text">Este ticket fue creado con un técnico sugerido. ¿Deseas aprobar la asignación?</p>
                      <button (click)="submitTriage('APPROVE')" [disabled]="isSubmitting()"
                              class="w-full py-2.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-black uppercase tracking-widest rounded-lg transition-all active:scale-95 disabled:opacity-50 flex justify-center items-center gap-2 shadow-lg shadow-amber-500/20">
                        @if (isSubmitting()) { <mat-icon class="animate-spin text-[16px]">refresh</mat-icon> }
                        @else { <mat-icon class="text-[16px]">check_circle</mat-icon> }
                        Aprobar Asignación
                      </button>
                    </div>
                  } @else {
                    <!-- Asignación Nueva -->
                    <div class="flex flex-col gap-4">
                      <!-- Dropdown de Técnicos -->
                      <div class="relative">
                        <label class="block text-[10px] font-black text-surface-text-muted uppercase tracking-widest mb-2">
                          Asignar Técnico Responsable
                        </label>
                        <select [(ngModel)]="selectedTechnicianId" 
                                class="w-full bg-surface-card border border-surface-border text-surface-text text-sm rounded-xl focus:ring-primary focus:border-primary block p-3 appearance-none shadow-sm">
                          <option [value]="null">-- Seleccionar Técnico --</option>
                          @for (tech of filteredTechnicians(); track tech.id) {
                            <option [value]="tech.id">
                              {{ tech.full_name }} ({{ workload()[tech.id] || 0 }} tickets activos)
                            </option>
                          }
                        </select>
                        <mat-icon class="absolute right-3 top-[34px] text-surface-text-muted pointer-events-none">expand_more</mat-icon>
                      </div>

                      <!-- Visualización de Carga del Técnico Seleccionado -->
                      @if (selectedTechnicianId()) {
                        <div class="flex items-center gap-3 p-3 rounded-xl border border-surface-border bg-surface-text/[0.02]">
                          <div class="h-8 w-8 rounded-lg flex items-center justify-center border" [ngClass]="getWorkloadColorClass(selectedTechWorkload())">
                            <mat-icon class="text-[16px]">{{ getWorkloadIcon(selectedTechWorkload()) }}</mat-icon>
                          </div>
                          <div>
                            <p class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted">Carga Actual</p>
                            <p class="text-xs font-bold flex items-center gap-1" [ngClass]="getWorkloadTextColorClass(selectedTechWorkload())">
                              {{ selectedTechWorkload() }} Tickets Activos
                              <span class="text-[10px] font-normal ml-1">
                                ({{ selectedTechWorkload() <= 2 ? 'Ligera' : (selectedTechWorkload() <= 5 ? 'Media' : 'Saturada') }})
                              </span>
                            </p>
                          </div>
                        </div>
                      }

                      <!-- Comentarios -->
                      <div>
                        <label class="block text-[10px] font-black text-surface-text-muted uppercase tracking-widest mb-2">
                          Instrucciones (Opcional)
                        </label>
                        <textarea [(ngModel)]="triageComment" rows="3"
                                  class="block p-3 w-full text-sm text-surface-text bg-surface-card rounded-xl border border-surface-border focus:ring-primary focus:border-primary shadow-sm custom-scrollbar"
                                  placeholder="Ej: Revisar primero la línea 4..."></textarea>
                      </div>

                      <!-- Botón de Confirmación -->
                      <button (click)="submitTriage('REASSIGN')" 
                              [disabled]="!selectedTechnicianId() || isSubmitting()"
                              class="w-full py-3 bg-primary hover:bg-primary-hover text-white text-xs font-black uppercase tracking-widest rounded-xl transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100 flex justify-center items-center gap-2 shadow-lg shadow-primary/20 mt-2">
                        @if (isSubmitting()) { <mat-icon class="animate-spin text-[16px]">refresh</mat-icon> }
                        @else { <mat-icon class="text-[16px]">send</mat-icon> }
                        Confirmar Despacho
                      </button>
                    </div>
                  }
                </div>
              } @else {
                <div class="bg-surface-text/[0.02] border border-surface-border rounded-xl p-6 text-center">
                  <mat-icon class="text-3xl text-surface-text-muted mb-2 opacity-50">verified</mat-icon>
                  <p class="text-xs text-surface-text-muted">Este ticket ya superó la fase de triaje operativo.</p>
                </div>
              }
              
            </div>
            
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    .custom-scrollbar::-webkit-scrollbar { height: 6px; width: 6px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.3); border-radius: 10px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.6); }
  `]
})
export class TicketTriageDrawerComponent {
  TicketStatus = TicketStatus;
  
  @Input() ticket: Ticket | null = null;
  @Output() close = new EventEmitter<void>();

  private supportService = inject(SupportService);
  private adminService = inject(AdminService);
  private toastService = inject(ToastService);

  technicians = signal<AdminUser[]>([]);
  workload = signal<Record<string, number>>({});
  
  selectedTechnicianId = signal<string | null>(null);
  triageComment = signal<string>('');
  isSubmitting = signal<boolean>(false);

  // Derivados
  filteredTechnicians = computed(() => {
    // Filtrar por area/company_id podría hacerse aquí si adminService trae todo.
    // Asumimos que adminService ya trae los usuarios del tenant actual por el interceptor.
    return this.technicians().filter(u => 
      u.role_name.toLowerCase().includes('technician') || 
      u.role_name.toLowerCase().includes('user') ||
      u.role_name.toLowerCase().includes('oper')
    );
  });

  selectedTechWorkload = computed(() => {
    const id = this.selectedTechnicianId();
    if (!id) return 0;
    return this.workload()[id] || 0;
  });

  get isTriageable(): boolean {
    if (!this.ticket) return false;
    return this.ticket.status === TicketStatus.NEW || this.ticket.status === TicketStatus.PENDING_APPROVAL;
  }

  constructor() {
    effect(() => {
      if (this.ticket) {
        this.loadSupervisionData();
        // Limpiar el estado interno al abrir otro ticket
        this.selectedTechnicianId.set(null);
        this.triageComment.set('');
      }
    });
  }

  async loadSupervisionData() {
    this.adminService.getUsers().subscribe(res => {
      if (res.data) this.technicians.set(res.data);
    });
    try {
      const wl = await this.supportService.getTechniciansWorkload();
      this.workload.set(wl);
    } catch (err) {
      console.error('Error fetching workload:', err);
    }
  }

  async submitTriage(action: 'APPROVE' | 'REASSIGN') {
    if (!this.ticket) return;
    this.isSubmitting.set(true);
    try {
      await this.supportService.triageTicket(
        this.ticket.id, 
        action, 
        this.selectedTechnicianId() || undefined, 
        this.triageComment() || undefined
      );
      this.toastService.success('Triaje Completado', 'El ticket ha sido despachado exitosamente.');
      this.close.emit();
    } catch (err: any) {
      this.toastService.error('Error de Triaje', err.message || 'No se pudo despachar el ticket.');
    } finally {
      this.isSubmitting.set(false);
    }
  }

  getPriorityColor(priority: string | undefined): string {
    if (!priority) return 'text-surface-text';
    const p = priority.toLowerCase();
    if (p.includes('alta') || p.includes('high') || p.includes('crítica') || p.includes('critical')) return 'text-red-500';
    if (p.includes('media') || p.includes('medium')) return 'text-amber-500';
    return 'text-emerald-500';
  }

  getWorkloadColorClass(count: number): string {
    if (count <= 2) return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-500';
    if (count <= 5) return 'bg-amber-500/10 border-amber-500/30 text-amber-500';
    return 'bg-red-500/10 border-red-500/30 text-red-500';
  }

  getWorkloadTextColorClass(count: number): string {
    if (count <= 2) return 'text-emerald-500';
    if (count <= 5) return 'text-amber-500';
    return 'text-red-500';
  }

  getWorkloadIcon(count: number): string {
    if (count <= 2) return 'check_circle';
    if (count <= 5) return 'warning';
    return 'error';
  }
}
