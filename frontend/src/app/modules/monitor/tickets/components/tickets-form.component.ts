import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { SupportService } from '../../../../core/services/support.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { SideDrawerService } from '../../../../core/services/side-drawer.service';
import { MatIconModule } from '@angular/material/icon';
import { finalize } from 'rxjs/operators';
import { TranslatePipe } from '../../../../shared/pipes/translate.pipe';
import { TicketStatus } from '../../../../core/models/support.types';

@Component({
  selector: 'app-tickets-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule, MatIconModule, TranslatePipe],
  template: `
    <div class="flex flex-col h-full bg-white animate-fade-in relative">
      
      <!-- Body -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-8">
        
        <!-- ================= LIST VIEW ================= -->
        <ng-container *ngIf="view() === 'list'">
          <div class="flex items-center justify-between mb-6">
            <div class="flex flex-col gap-1">
              <h3 class="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em]">{{ 'support.my_tickets' | translate:'MIS TICKETS' }}</h3>
              <a routerLink="kanban" (click)="drawerService.close()" class="text-[9px] font-bold text-sky-500 hover:text-sky-600 hover:underline uppercase tracking-widest flex items-center gap-1 cursor-pointer">
                {{ 'support.open_full_kanban' | translate:'ABRIR KANBAN COMPLETO' }} <mat-icon class="text-[10px] w-[10px] h-[10px]">launch</mat-icon>
              </a>
            </div>
            <button 
              (click)="switchView('form')"
              class="px-4 py-2 bg-sky-50 text-sky-500 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-sky-100 transition-colors"
            >
              {{ 'support.new_ticket' | translate:'NUEVO TICKET' }} +
            </button>
          </div>

          <div *ngIf="isLoadingTickets()" class="flex justify-center items-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-400"></div>
          </div>

          <div *ngIf="!isLoadingTickets()" class="space-y-4">
            <div *ngFor="let t of tickets()" (click)="openTriage(t)" class="border border-slate-200 rounded-2xl p-5 bg-white hover:border-slate-300 transition-all cursor-pointer shadow-sm hover:shadow-md">
              <div class="flex justify-between items-start mb-3">
                <span class="text-sky-500 font-black text-xs tracking-widest">{{ t.reference_code || ('#TKT-' + t.id.slice(-4).toUpperCase()) }}</span>
                <span class="bg-slate-100 text-slate-500 px-2.5 py-1 rounded-md text-[9px] font-black uppercase tracking-widest">
                  {{ t.status }}
                </span>
              </div>
              <h4 class="font-bold text-slate-800 text-sm mb-1 line-clamp-1">{{ t.title }}</h4>
              <p class="text-slate-500 text-[11px] mb-5 line-clamp-2 leading-relaxed">{{ t.description }}</p>
              <div class="flex justify-between items-center text-[9px] font-black text-slate-400 uppercase tracking-widest">
                <span>{{ t.created_at | date:'M/d/yy, h:mm a' }}</span>
                <span class="flex items-center gap-1.5 font-bold text-slate-600">
                  <div class="w-1.5 h-1.5 rounded-full" [ngClass]="getPriorityColor(t.priority)"></div> 
                  {{ t.priority }}
                </span>
              </div>
            </div>

            <div *ngIf="tickets().length === 0" class="text-center py-12 border-2 border-dashed border-slate-100 rounded-2xl">
              <mat-icon class="text-slate-300 text-4xl mb-2">assignment</mat-icon>
              <p class="text-slate-400 text-xs font-bold">{{ 'support.no_tickets' | translate:'No se encontraron tickets.' }}</p>
            </div>
          </div>
        </ng-container>

        <!-- ================= FORM VIEW (CREATE) ================= -->
        <ng-container *ngIf="view() === 'form'">
          <button (click)="switchView('list')" class="flex items-center gap-2 text-slate-500 font-bold text-[11px] uppercase tracking-widest hover:text-slate-800 transition-colors mb-8">
            <mat-icon class="text-lg">arrow_back</mat-icon>
            {{ 'support.back_to_history' | translate:'VOLVER AL HISTORIAL' }}
          </button>

          <form [formGroup]="ticketForm" (ngSubmit)="save()" class="space-y-6">
            <div class="space-y-2">
              <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">ASUNTO</label>
              <input type="text" formControlName="title" placeholder="Ej: Problema con inventario" class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 transition-all">
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">PRIORIDAD</label>
                <select formControlName="priority" class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 appearance-none">
                  <option value="Baja">Baja</option>
                  <option value="Media">Media</option>
                  <option value="Alta">Alta</option>
                  <option value="Crítica">Crítica</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">ÁREA</label>
                <select formControlName="area" class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 appearance-none">
                  <option value="Sistemas">Sistemas</option>
                  <option value="Mantenimiento">Mantenimiento</option>
                  <option value="Producción">Producción</option>
                </select>
              </div>
            </div>

            <div class="space-y-2">
              <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">DESCRIPCIÓN</label>
              <textarea formControlName="description" rows="5" placeholder="Describe el problema..." class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 resize-none"></textarea>
            </div>

            <button type="submit" [disabled]="ticketForm.invalid || isSaving()" class="w-full py-4 bg-sky-500 hover:bg-sky-600 text-white rounded-2xl text-[12px] font-black uppercase tracking-[0.2em] shadow-lg shadow-sky-200 transition-all">
              {{ isSaving() ? 'ENVIANDO...' : 'CREAR TICKET' }}
            </button>
          </form>
        </ng-container>

        <!-- ================= TRIAGE VIEW ================= -->
        <ng-container *ngIf="view() === 'triage'">
          <div (click)="switchView('list')" class="flex items-center gap-2 text-slate-500 font-bold text-[11px] uppercase tracking-widest hover:text-slate-800 transition-colors mb-8 cursor-pointer">
            <mat-icon class="text-lg">arrow_back</mat-icon>
            {{ 'support.back_to_list' | translate:'VOLVER AL LISTADO' }}
          </div>

          <div *ngIf="selectedTicket()" class="space-y-6">
            <div class="p-6 bg-slate-50 rounded-2xl border border-slate-100">
               <span class="text-sky-500 font-black text-xs tracking-widest block mb-2">{{ selectedTicket().reference_code }}</span>
               <h3 class="text-lg font-bold text-slate-800 leading-tight mb-2">{{ selectedTicket().title }}</h3>
               <p class="text-slate-500 text-xs leading-relaxed mb-4">{{ selectedTicket().description }}</p>
               <div class="flex gap-2">
                 <span class="px-2 py-1 rounded bg-slate-200 text-slate-600 text-[9px] font-bold uppercase tracking-widest">{{ selectedTicket().status }}</span>
                 <div class="flex items-center gap-1 px-2 py-1 rounded text-[9px] font-bold uppercase tracking-widest" [ngClass]="getPriorityColorClass(selectedTicket().priority)">
                   <div class="w-1 h-1 rounded-full bg-current"></div>
                   {{ selectedTicket().priority }}
                 </div>
               </div>
            </div>

            <!-- ASIGNACIÓN TRIPLE -->
            <div class="space-y-4">
              <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">ASIGNAR RESPONSABLE</label>
              
              <div class="relative">
                <div class="flex items-center bg-slate-50 border border-slate-200 rounded-2xl p-1 transition-all focus-within:border-sky-400">
                  <mat-icon class="ml-3 text-slate-400">search</mat-icon>
                  <input 
                    type="text" 
                    [ngModel]="techSearchQuery()"
                    (ngModelChange)="onTechSearchChange($event)"
                    placeholder="Buscar técnico, operario o proveedor..."
                    class="flex-1 bg-transparent border-none p-3 text-sm font-medium text-slate-800 outline-none placeholder:text-slate-300"
                  >
                  @if (selectedIdentity()) {
                    <button (click)="clearTechSelection()" class="mr-3 text-slate-400 hover:text-red-500 transition-colors">
                      <mat-icon class="text-lg">cancel</mat-icon>
                    </button>
                  }
                </div>

                @if (showTechDropdown() && typeaheadIdentities().length > 0) {
                  <div class="absolute z-[100] w-full mt-2 bg-white border border-slate-200 rounded-2xl shadow-xl max-h-64 overflow-y-auto custom-scrollbar">
                    @for (identity of typeaheadIdentities(); track (identity.id + identity.type)) {
                      <div (mousedown)="selectIdentity(identity)" 
                           class="px-4 py-3 hover:bg-slate-50 cursor-pointer border-b border-slate-100 last:border-0 flex items-center gap-3 transition-colors">
                        <div class="w-8 h-8 rounded-lg flex items-center justify-center" 
                             [ngClass]="{
                               'bg-sky-100 text-sky-500': identity.type === 'INTERNAL',
                               'bg-amber-100 text-amber-500': identity.type === 'PLANTA',
                               'bg-purple-100 text-purple-500': identity.type === 'EXTERNO'
                             }">
                          <mat-icon class="text-[18px]">
                            {{ identity.type === 'INTERNAL' ? 'person' : (identity.type === 'PLANTA' ? 'engineering' : 'business_center') }}
                          </mat-icon>
                        </div>
                        <div class="flex flex-col flex-1">
                          <span class="text-[11px] font-bold text-slate-800 uppercase tracking-tight">{{ identity.label }}</span>
                          <span class="text-[9px] text-slate-400 font-bold uppercase">{{ identity.type }} • {{ identity.sub }}</span>
                        </div>
                      </div>
                    }
                  </div>
                }
              </div>

              <!-- Banner Externo -->
              @if (selectedIdentity()?.type === 'EXTERNO') {
                <div class="p-4 rounded-2xl border border-purple-100 bg-purple-50/30 flex items-start gap-3 animate-fade-in">
                  <mat-icon class="text-purple-500 text-sm mt-0.5">verified_user</mat-icon>
                  <div class="flex-1">
                    <p class="text-[10px] font-black uppercase text-purple-600 tracking-widest mb-1">Acceso Externo (SLA 72h)</p>
                    <p class="text-[10px] text-slate-500 leading-tight">
                      Se generará un Bridge Seguro para el proveedor.
                    </p>
                  </div>
                </div>
              }

              <!-- COMENTARIO -->
              <div class="space-y-2 pt-2">
                <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">INSTRUCCIONES / NOTAS</label>
                <textarea 
                  [(ngModel)]="triageComment"
                  placeholder="Instrucciones adicionales para el responsable..."
                  rows="3"
                  class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 transition-all resize-none placeholder:text-slate-300"
                ></textarea>
              </div>

              <button 
                (click)="submitTriage()"
                [disabled]="!selectedIdentity() || isSaving()"
                class="w-full py-4 bg-slate-800 hover:bg-slate-900 text-white rounded-2xl text-[12px] font-black uppercase tracking-[0.2em] transition-all disabled:opacity-50 flex justify-center items-center gap-2"
              >
                {{ isSaving() ? 'PROCESANDO...' : 'CONFIRMAR DESPACHO' }}
              </button>
            </div>
          </div>
        </ng-container>

      </div>

      <!-- Footer -->
      <div class="py-5 border-t border-slate-100 flex justify-center items-center gap-2 bg-white mt-auto z-10">
        <div class="w-1.5 h-1.5 rounded-full bg-[#00E59B] animate-pulse"></div>
        <span class="text-[10px] font-black text-[#00E59B] uppercase tracking-[0.2em]">SISTEMA DE GESTIÓN UNIFICADA</span>
      </div>

    </div>
  `,
  styles: [`
    .animate-fade-in { animation: fadeIn 0.3s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
    .custom-scrollbar::-webkit-scrollbar { width: 4px; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: #E2E8F0; border-radius: 10px; }
  `]
})
export class TicketsFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private supportService = inject(SupportService);
  private notifications = inject(NotificationService);
  drawerService = inject(SideDrawerService);

  // View State
  view = signal<'list' | 'form' | 'triage'>('list');
  
  // Data States
  tickets = signal<any[]>([]);
  selectedTicket = signal<any | null>(null);
  isLoadingTickets = signal<boolean>(false);
  isSaving = signal<boolean>(false);

  // Identity Search state
  techSearchQuery = signal<string>('');
  showTechDropdown = signal<boolean>(false);
  typeaheadIdentities = signal<any[]>([]);
  selectedIdentity = signal<any | null>(null);

  selectedTechnicianId = signal<string | null>(null);
  selectedCollaboratorId = signal<string | null>(null);
  selectedExternalContactId = signal<string | null>(null);

  triageComment = signal<string>('');
  private searchTimeout: any;

  ticketForm: FormGroup = this.fb.group({
    title: ['', [Validators.required, Validators.minLength(5)]],
    description: ['', [Validators.required, Validators.minLength(10)]],
    priority: ['Media', Validators.required],
    area: ['Sistemas', Validators.required]
  });

  // Data receiving interface from SideDrawer setup
  set data(val: any) {
    if (val && val.id) {
      this.selectedTicket.set(val);
      this.view.set('triage');
    }
  }

  ngOnInit(): void {
    this.loadTickets();
  }

  switchView(newView: 'list' | 'form' | 'triage') {
    this.view.set(newView);
    if (newView === 'form') {
      this.ticketForm.reset({ priority: 'Media', area: 'Sistemas' });
    }
  }

  async loadTickets() {
    this.isLoadingTickets.set(true);
    try {
      await this.supportService.loadTickets();
      this.tickets.set(this.supportService.tickets());
    } catch (error) {
      this.notifications.error('Error', 'No se pudieron cargar los tickets.');
    } finally {
      this.isLoadingTickets.set(false);
    }
  }

  openTriage(ticket: any) {
    this.selectedTicket.set(ticket);
    this.view.set('triage');
    this.clearTechSelection();
    this.triageComment.set('');
  }

  async onTechSearchChange(value: string) {
    this.techSearchQuery.set(value);
    if (!value) {
      this.clearTechSelection();
    } else {
      if (this.searchTimeout) clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(async () => {
        const results = await this.supportService.searchIdentities(value);
        this.typeaheadIdentities.set(results);
      }, 300);
    }
    this.showTechDropdown.set(true);
  }

  selectIdentity(identity: any) {
    this.selectedIdentity.set(identity);
    this.techSearchQuery.set(identity.label);
    this.showTechDropdown.set(false);

    this.selectedTechnicianId.set(identity.type === 'INTERNAL' ? identity.id : null);
    this.selectedCollaboratorId.set(identity.type === 'PLANTA' ? identity.id : null);
    this.selectedExternalContactId.set(identity.type === 'EXTERNO' ? identity.id : null);
  }

  clearTechSelection() {
    this.selectedIdentity.set(null);
    this.selectedTechnicianId.set(null);
    this.selectedCollaboratorId.set(null);
    this.selectedExternalContactId.set(null);
    this.techSearchQuery.set('');
    this.typeaheadIdentities.set([]);
  }

  async submitTriage() {
    const ticket = this.selectedTicket();
    if (!ticket || !this.selectedIdentity()) return;

    this.isSaving.set(true);
    try {
      await this.supportService.triageTicket(
        ticket.id,
        'REASSIGN',
        this.selectedTechnicianId() || undefined,
        this.triageComment(),
        this.selectedCollaboratorId() || undefined,
        this.selectedExternalContactId() || undefined
      );

      this.notifications.success('Éxito', 'Ticket despachado correctamente.');
      this.loadTickets();
      this.switchView('list');
      this.drawerService.notifyRefresh();
    } catch (err: any) {
      this.notifications.error('Error', err.message || 'Error al procesar triaje');
    } finally {
      this.isSaving.set(false);
    }
  }

  getPriorityColor(priority: string): string {
    const p = (priority || '').toUpperCase();
    if (p.includes('ALTA') || p.includes('CRIT')) return 'bg-red-500';
    if (p.includes('MEDIA')) return 'bg-amber-500';
    return 'bg-emerald-500';
  }

  getPriorityColorClass(priority: string): string {
    const p = (priority || '').toUpperCase();
    if (p.includes('ALTA') || p.includes('CRIT')) return 'bg-red-50 text-red-600';
    if (p.includes('MEDIA')) return 'bg-amber-50 text-amber-600';
    return 'bg-emerald-50 text-emerald-600';
  }

  async save() {
    if (this.ticketForm.invalid || this.isSaving()) return;
    this.isSaving.set(true);
    try {
      await this.supportService.createTicket(
        this.ticketForm.value.title,
        this.ticketForm.value.description,
        this.ticketForm.value.priority,
        this.ticketForm.value.area
      );
      this.notifications.success('Éxito', 'Ticket creado correctamente.');
      this.loadTickets();
      this.switchView('list');
      this.drawerService.notifyRefresh();
    } catch (err: any) {
      this.notifications.error('Error', 'No se pudo crear el ticket.');
    } finally {
      this.isSaving.set(false);
    }
  }
}
