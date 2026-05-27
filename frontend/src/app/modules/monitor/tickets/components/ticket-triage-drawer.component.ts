import { Component, Input, Output, EventEmitter, inject, signal, effect, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { TranslatePipe } from '../../../../shared/pipes/translate.pipe';
import { Ticket, TicketStatus, TicketComment } from '../../../../core/models/support.types';
import { SupportService } from '../../../../core/services/support.service';
import { AdminUser, AdminService } from '../../../../core/services/admin.service';
import { ToastService } from '../../../../core/services/toast.service';
import { AuthService } from '../../../../core/services/auth.service';

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
          <div class="pointer-events-auto w-screen max-w-3xl transform transition-transform ease-in-out duration-300 translate-x-0 bg-surface-card border-l border-surface-border shadow-2xl flex flex-col h-full overflow-hidden">
            
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

            <!-- Two-column Content -->
            <div class="flex flex-1 overflow-hidden">

              <!-- LEFT: Detalles + Triaje -->
              <div class="w-80 flex-shrink-0 overflow-y-auto px-6 py-6 flex flex-col gap-6 border-r border-surface-border custom-scrollbar">

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
                      <!-- Typeahead de Técnicos -->
                      <div class="relative w-full">
                        <label class="block text-[10px] font-black text-surface-text-muted uppercase tracking-widest mb-2">
                          Asignar Responsables
                        </label>

                        <!-- Chips seleccionados -->
                        @if (selectedIdentities().length > 0) {
                          <div class="flex flex-wrap gap-1.5 mb-2">
                            @for (p of selectedIdentities(); track (p.id + p.type)) {
                              <div class="flex items-center gap-1 px-2 py-1 rounded-lg text-[9px] font-black uppercase tracking-tight border"
                                   [ngClass]="{
                                     'bg-sky-500/10 border-sky-500/20 text-sky-400': p.type === 'INTERNAL',
                                     'bg-amber-500/10 border-amber-500/20 text-amber-400': p.type === 'PLANTA',
                                     'bg-purple-500/10 border-purple-500/20 text-purple-400': p.type === 'EXTERNO'
                                   }">
                                <mat-icon class="text-[11px]">{{ p.type === 'INTERNAL' ? 'person' : (p.type === 'PLANTA' ? 'engineering' : 'business_center') }}</mat-icon>
                                {{ p.label }}
                                <button (mousedown)="removeIdentity(p)" class="ml-0.5 hover:opacity-60 transition-opacity flex items-center">
                                  <mat-icon class="text-[11px]">close</mat-icon>
                                </button>
                              </div>
                            }
                          </div>
                        }

                        <div class="relative">
                          <mat-icon class="absolute left-3 top-[10px] text-surface-text-muted text-[20px]">search</mat-icon>
                          <input type="text"
                                 [ngModel]="techSearchQuery()"
                                 (ngModelChange)="onTechSearchChange($event)"
                                 (focus)="showTechDropdown.set(true)"
                                 (blur)="onTechBlur()"
                                 placeholder="Buscar por nombre o correo..."
                                 class="w-full bg-surface-card border border-surface-border text-surface-text text-sm rounded-xl focus:ring-primary focus:border-primary block p-3 pl-10 pr-10 shadow-sm transition-all" />
                          <mat-icon class="absolute right-3 top-[10px] text-surface-text-muted text-[20px] pointer-events-none transition-transform" [class.rotate-180]="showTechDropdown()">expand_more</mat-icon>
                        </div>

                        @if (showTechDropdown() && typeaheadIdentities().length > 0) {
                          <div class="absolute z-[100] w-full mt-2 bg-surface-card border border-surface-border rounded-xl shadow-2xl max-h-64 overflow-y-auto custom-scrollbar animate-fade-in origin-top">
                            @for (identity of typeaheadIdentities(); track (identity.id + identity.type)) {
                              <!-- Header de Categoría (opcional si se desea separar visualmente) -->
                              <div (mousedown)="selectIdentity(identity)" 
                                   class="px-4 py-3 hover:bg-surface-text/[0.05] cursor-pointer border-b border-surface-border/50 last:border-0 flex justify-between items-center transition-colors">
                                <div class="flex items-center gap-3">
                                  <div class="w-8 h-8 rounded-lg flex items-center justify-center" 
                                       [ngClass]="{
                                         'bg-sky-500/10 text-sky-500': identity.type === 'INTERNAL',
                                         'bg-amber-500/10 text-amber-500': identity.type === 'PLANTA',
                                         'bg-purple-500/10 text-purple-500': identity.type === 'EXTERNO'
                                       }">
                                    <mat-icon class="text-[18px]">
                                      {{ identity.type === 'INTERNAL' ? 'person' : (identity.type === 'PLANTA' ? 'engineering' : 'business_center') }}
                                    </mat-icon>
                                  </div>
                                  <div class="flex flex-col">
                                    <span class="text-[11px] font-bold text-surface-text uppercase tracking-tight">{{ identity.label }}</span>
                                    <span class="text-[9px] text-surface-text-muted flex items-center gap-1">
                                      <span class="font-black uppercase text-[8px] opacity-70">{{ identity.type }}</span> • {{ identity.sub }}
                                    </span>
                                  </div>
                                </div>
                                
                                @if (identity.type === 'INTERNAL') {
                                  <div class="text-[8px] font-black uppercase px-2 py-1 rounded-md"
                                       [ngClass]="getWorkloadColorClass(workload()[identity.id] || 0)">
                                    {{ workload()[identity.id] || 0 }} tickets
                                  </div>
                                }
                              </div>
                            }
                          </div>
                        }
                      </div>

                      <!-- Banner Informativo para Externos -->
                      @if (selectedIdentities().some(i => i.type === 'EXTERNO')) {
                        <div class="p-3 rounded-xl border border-purple-500/20 bg-purple-500/5 flex items-start gap-3 animate-fade-in">
                          <mat-icon class="text-purple-500 text-sm mt-0.5">info</mat-icon>
                          <div class="flex-1">
                            <p class="text-[10px] font-black uppercase text-purple-500 tracking-widest mb-1">SLA Externo: 72 Horas</p>
                            <p class="text-[10px] text-surface-text-muted leading-tight">
                              Se enviará un enlace de acceso seguro a <b>{{ selectedIdentities().find(i => i.type === 'EXTERNO')?.sub }}</b>.
                              El proveedor podrá interactuar sin consumir licencias.
                            </p>
                          </div>
                        </div>
                      }

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

                      <!-- Comentarios e Instrucciones -->
                      <div>
                        <label class="block text-[10px] font-black text-surface-text-muted uppercase tracking-widest mb-2">
                          Comentarios / Instrucciones
                        </label>
                        <textarea [(ngModel)]="triageComment" rows="3"
                                  class="block p-3 w-full text-sm text-surface-text bg-surface-card rounded-xl border border-surface-border focus:ring-primary focus:border-primary shadow-sm custom-scrollbar"
                                  placeholder="Ej: Revisar primero la línea 4..."></textarea>
                      </div>

                      <!-- Fecha Compromiso -->
                      <div>
                        <label class="block text-[10px] font-black text-surface-text-muted uppercase tracking-widest mb-2">
                          Fecha Compromiso (SLA)
                        </label>
                        <div class="relative">
                          <input type="date" [(ngModel)]="commitmentDate"
                                 class="w-full bg-surface-card border border-surface-border text-surface-text text-sm rounded-xl focus:ring-primary focus:border-primary block p-3 shadow-sm">
                        </div>
                      </div>

                      <!-- Subir Adjunto -->
                      <div>
                        <label class="block text-[10px] font-black text-surface-text-muted uppercase tracking-widest mb-2">
                          Adjuntar Evidencia
                        </label>
                        <div class="flex items-center justify-center w-full">
                          <label class="flex flex-col items-center justify-center w-full h-20 border-2 border-surface-border border-dashed rounded-xl cursor-pointer bg-surface-card hover:bg-surface-text/[0.02] transition-colors">
                            <div class="flex flex-col items-center justify-center pt-3 pb-3">
                              <mat-icon class="text-surface-text-muted mb-1 text-xl">cloud_upload</mat-icon>
                              <p class="mb-1 text-[10px] font-black uppercase text-surface-text-muted text-center px-4">
                                @if(attachmentName()) { <span class="text-primary truncate block">{{ attachmentName() }}</span> }
                                @else { Haz clic para subir o arrastra el archivo }
                              </p>
                            </div>
                            <input type="file" class="hidden" (change)="onFileSelected($event)" />
                          </label>
                        </div>
                      </div>

                      <!-- Botón de Confirmación -->
                      <button (click)="submitTriage('REASSIGN')" 
                              [disabled]="selectedIdentities().length === 0 || isSubmitting()"
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

              </div><!-- end LEFT column -->

              <!-- RIGHT: Comentarios -->
              <div class="flex-1 flex flex-col overflow-hidden">

                <!-- Chat header -->
                <div class="px-5 py-4 border-b border-surface-border flex-shrink-0 flex items-center gap-2">
                  <mat-icon class="text-[14px] text-surface-text-muted">chat</mat-icon>
                  <h3 class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest">Comentarios</h3>
                  @if (comments().length > 0) {
                    <span class="text-[9px] bg-surface-text/10 px-1.5 py-0.5 rounded-full text-surface-text-muted">{{ comments().length }}</span>
                  }
                  <button class="ml-auto p-1 rounded-lg hover:bg-surface-text/[0.05] transition-colors" (click)="loadComments()" title="Actualizar">
                    <mat-icon class="text-[14px] text-surface-text-muted" [class.animate-spin]="isLoadingComments()">refresh</mat-icon>
                  </button>
                </div>

                <!-- Messages -->
                <div class="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-3 custom-scrollbar">
                  @if (isLoadingComments()) {
                    <div class="flex items-center justify-center py-8">
                      <mat-icon class="animate-spin text-surface-text-muted">refresh</mat-icon>
                    </div>
                  } @else if (comments().length === 0) {
                    <div class="flex flex-col items-center justify-center h-full gap-2 opacity-40">
                      <mat-icon class="text-4xl text-surface-text-muted">chat_bubble_outline</mat-icon>
                      <p class="text-xs text-surface-text-muted">Sin comentarios aún</p>
                    </div>
                  } @else {
                    @for (comment of comments(); track comment.id) {
                      @if (comment.author_id === SYSTEM_USER_ID) {
                        <!-- Bot -->
                        <div class="flex gap-2 items-start">
                          <div class="w-7 h-7 rounded-lg bg-primary/10 flex-shrink-0 flex items-center justify-center">
                            <mat-icon class="text-[14px] text-primary">smart_toy</mat-icon>
                          </div>
                          <div class="bg-surface-text/[0.03] border border-surface-border/60 rounded-xl rounded-tl-none px-3 py-2 max-w-[90%]">
                            <p class="text-[9px] font-black text-primary uppercase tracking-widest mb-1">Interno AI Assistant</p>
                            <p class="text-xs text-surface-text whitespace-pre-line leading-relaxed">{{ comment.content }}</p>
                            <p class="text-[9px] text-surface-text-muted mt-1 text-right">{{ formatCommentTime(comment.created_at) }}</p>
                          </div>
                        </div>
                      } @else if (comment.author_id === currentUserId()) {
                        <!-- Me -->
                        <div class="flex justify-end">
                          <div class="bg-primary/10 border border-primary/20 rounded-xl rounded-tr-none px-3 py-2 max-w-[90%]">
                            <p class="text-xs text-surface-text leading-relaxed">{{ comment.content }}</p>
                            <p class="text-[9px] text-surface-text-muted mt-1 text-right">{{ formatCommentTime(comment.created_at) }}</p>
                          </div>
                        </div>
                      } @else {
                        <!-- Other -->
                        <div class="flex gap-2 items-start">
                          <div class="w-7 h-7 rounded-full bg-surface-text/10 flex-shrink-0 flex items-center justify-center">
                            <mat-icon class="text-[14px] text-surface-text-muted">person</mat-icon>
                          </div>
                          <div class="bg-surface-text/[0.03] border border-surface-border/60 rounded-xl rounded-tl-none px-3 py-2 max-w-[90%]">
                            <p class="text-xs text-surface-text leading-relaxed">{{ comment.content }}</p>
                            <p class="text-[9px] text-surface-text-muted mt-1 text-right">{{ formatCommentTime(comment.created_at) }}</p>
                          </div>
                        </div>
                      }
                    }
                  }
                </div>

                <!-- Input bar -->
                <div class="px-5 py-4 border-t border-surface-border flex-shrink-0 flex gap-2">
                  <input type="text" [(ngModel)]="newCommentText"
                         (keyup.enter)="sendComment()"
                         placeholder="Escribe un comentario..."
                         class="flex-1 bg-surface-card border border-surface-border text-surface-text text-xs rounded-xl focus:ring-primary focus:border-primary block p-2.5 shadow-sm" />
                  <button (click)="sendComment()"
                          [disabled]="!newCommentText.trim() || isAddingComment()"
                          class="p-2.5 bg-primary hover:bg-primary-hover text-white rounded-xl transition-all active:scale-95 disabled:opacity-50 shadow-lg shadow-primary/20 flex-shrink-0">
                    @if (isAddingComment()) {
                      <mat-icon class="animate-spin text-[16px]">refresh</mat-icon>
                    } @else {
                      <mat-icon class="text-[16px]">send</mat-icon>
                    }
                  </button>
                </div>

              </div><!-- end RIGHT column -->

            </div><!-- end two-column -->
            
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
  readonly SYSTEM_USER_ID = '00000000-0000-0000-0000-000000000000';

  @Input() ticket: Ticket | null = null;
  @Output() close = new EventEmitter<void>();

  private supportService = inject(SupportService);
  private adminService = inject(AdminService);
  private toastService = inject(ToastService);
  private authService = inject(AuthService);

  private searchTimeout: any;

  technicians = signal<AdminUser[]>([]);
  workload = signal<Record<string, number>>({});
  isSubmitting = signal<boolean>(false);
  
  // Unified Identity Search state
  techSearchQuery = signal<string>('');
  showTechDropdown = signal<boolean>(false);
  typeaheadIdentities = signal<any[]>([]);
  selectedIdentity = signal<any | null>(null); // kept for blur logic only
  selectedIdentities = signal<any[]>([]);

  selectedTechnicianId = signal<string | null>(null);
  selectedCollaboratorId = signal<string | null>(null);
  selectedExternalContactId = signal<string | null>(null);

  triageComment = signal<string>('');
  commitmentDate = signal<string>('');
  attachmentName = signal<string | null>(null);

  comments = signal<TicketComment[]>([]);
  newCommentText = '';
  isAddingComment = signal<boolean>(false);
  isLoadingComments = signal<boolean>(false);

  currentUserId = computed(() => this.authService.session()?.user_id ?? '');

  // Derivados
  filteredTechnicians = computed(() => {
    return this.technicians().filter(u => {
      const role = (u.role_name || '').toLowerCase();
      return role.includes('technician') || 
             role.includes('user') ||
             role.includes('oper') ||
             role.includes('admin') ||
             role.includes('supervisor') ||
             role.includes('manager') ||
             role.includes('owner') ||
             role.includes('it');
    });
  });

  typeaheadTechnicians = computed(() => {
    return this.filteredTechnicians();
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
        this.loadComments();
        this.selectedIdentity.set(null);
        this.selectedIdentities.set([]);
        this.selectedTechnicianId.set(null);
        this.selectedCollaboratorId.set(null);
        this.selectedExternalContactId.set(null);
        this.techSearchQuery.set('');
        this.typeaheadIdentities.set([]);
        this.triageComment.set('');
        this.commitmentDate.set('');
        this.attachmentName.set(null);
        this.newCommentText = '';
      }
    });
  }

  async loadComments() {
    if (!this.ticket) return;
    this.isLoadingComments.set(true);
    try {
      const msgs = await this.supportService.getMessages(this.ticket.id);
      this.comments.set(msgs);
    } catch (err) {
      console.error('Error loading comments:', err);
    } finally {
      this.isLoadingComments.set(false);
    }
  }

  async sendComment() {
    if (!this.ticket || !this.newCommentText.trim()) return;
    this.isAddingComment.set(true);
    try {
      await this.supportService.addMessage(this.ticket.id, this.newCommentText.trim());
      this.newCommentText = '';
      await this.loadComments();
    } catch (err) {
      this.toastService.error('Error', 'No se pudo enviar el comentario.');
    } finally {
      this.isAddingComment.set(false);
    }
  }

  formatCommentTime(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
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

  async onTechSearchChange(value: string) {
    this.techSearchQuery.set(value);
    if (!value) {
      this.selectedIdentity.set(null);
      this.selectedTechnicianId.set(null);
      this.selectedCollaboratorId.set(null);
      this.selectedExternalContactId.set(null);
      this.typeaheadIdentities.set([]);
    } else {
      if (this.searchTimeout) clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(async () => {
        const results = await this.supportService.searchIdentities(value);
        this.typeaheadIdentities.set(results);
      }, 300);
    }
    this.showTechDropdown.set(true);
  }

  onTechBlur() {
    setTimeout(() => {
      this.showTechDropdown.set(false);
      if (!this.selectedIdentity()) {
        this.techSearchQuery.set('');
      } else {
        this.techSearchQuery.set(this.selectedIdentity().label);
      }
    }, 150);
  }

  selectIdentity(identity: any) {
    this.selectedIdentity.set(identity); // used by onTechBlur
    this.selectedIdentities.update(list => [...list.filter(i => i.type !== identity.type), identity]);
    this._syncIds();
    this.techSearchQuery.set('');
    this.typeaheadIdentities.set([]);
    this.showTechDropdown.set(false);
  }

  removeIdentity(identity: any) {
    this.selectedIdentities.update(list => list.filter(i => !(i.id === identity.id && i.type === identity.type)));
    this._syncIds();
    if (this.selectedIdentities().length === 0) this.selectedIdentity.set(null);
  }

  private _syncIds() {
    const all = this.selectedIdentities();
    this.selectedTechnicianId.set(all.find(i => i.type === 'INTERNAL')?.id ?? null);
    this.selectedCollaboratorId.set(all.find(i => i.type === 'PLANTA')?.id ?? null);
    this.selectedExternalContactId.set(all.find(i => i.type === 'EXTERNO')?.id ?? null);
  }

  clearTechSelection() {
    this.selectedIdentity.set(null);
    this.selectedIdentities.set([]);
    this.selectedTechnicianId.set(null);
    this.selectedCollaboratorId.set(null);
    this.selectedExternalContactId.set(null);
    this.techSearchQuery.set('');
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.attachmentName.set(file.name);
    }
  }

  async submitTriage(action: 'APPROVE' | 'REASSIGN') {
    if (!this.ticket) return;
    this.isSubmitting.set(true);
    try {
      let finalComment = this.triageComment();
      if (this.commitmentDate()) {
        finalComment += `\n\n[SLA/Fecha Compromiso]: ${this.commitmentDate()}`;
      }
      if (this.attachmentName()) {
        finalComment += `\n[Adjunto]: ${this.attachmentName()}`;
      }

      const assignees = this.selectedIdentities().map((id: any, idx: number) => ({
        identity_type: id.type as 'INTERNAL' | 'PLANTA' | 'EXTERNO',
        identity_id: id.id,
        is_lead: idx === 0,
      }));
      await this.supportService.triageTicket(
        this.ticket.id,
        action,
        assignees,
        finalComment || undefined
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
