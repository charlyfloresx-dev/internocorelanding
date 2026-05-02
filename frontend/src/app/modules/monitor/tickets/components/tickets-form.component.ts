import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
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
  imports: [CommonModule, ReactiveFormsModule, MatIconModule, TranslatePipe],
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
            <div *ngFor="let t of tickets()" class="border border-slate-200 rounded-2xl p-5 bg-white hover:border-slate-300 transition-all cursor-pointer shadow-sm hover:shadow-md">
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

        <!-- ================= FORM VIEW ================= -->
        <ng-container *ngIf="view() === 'form'">
          <!-- Back button -->
          <button 
            (click)="switchView('list')"
            class="flex items-center gap-2 text-slate-500 font-bold text-[11px] uppercase tracking-widest hover:text-slate-800 transition-colors mb-8"
          >
            <mat-icon class="text-lg">arrow_back</mat-icon>
            {{ 'support.back_to_history' | translate:'VOLVER AL HISTORIAL' }}
          </button>

          <div *ngIf="isLoadingConstants()" class="flex justify-center items-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-400"></div>
          </div>

          <form *ngIf="!isLoadingConstants()" [formGroup]="ticketForm" (ngSubmit)="save()" class="space-y-6">
            
            <!-- SUBJECT -->
            <div class="space-y-2">
              <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">{{ 'support.subject_label' | translate:'ASUNTO' }}</label>
              <input 
                type="text" 
                formControlName="title"
                placeholder="Ej: Problema con inventario"
                class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-400/10 transition-all placeholder:text-slate-300"
              >
            </div>

            <!-- PRIORIDAD -->
            <div class="space-y-2">
              <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">{{ 'support.priority_label' | translate:'PRIORIDAD' }}</label>
              <select 
                formControlName="priority"
                class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-400/10 transition-all cursor-pointer appearance-none"
              >
                <option value="" disabled selected>Media</option>
                <option value="Baja">Baja</option>
                <option value="Media">Media</option>
                <option value="Alta">Alta</option>
                <option value="Crítica">Crítica</option>
              </select>
            </div>

            <!-- HIDDEN FIELDS (Defaulted for simplified UI) -->
            <input type="hidden" formControlName="ticket_type">
            
            <!-- DEPARTAMENTO DESTINO (Área) -->
            <div class="space-y-2">
              <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">{{ 'support.area_label' | translate:'DEPARTAMENTO DESTINO' }}</label>
              <select 
                formControlName="area"
                class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-400/10 transition-all cursor-pointer appearance-none"
              >
                <option value="Sistemas">Sistemas (IT)</option>
                <option value="Mantenimiento">Mantenimiento</option>
                <option value="Producción">Producción</option>
                <option value="Calidad">Calidad</option>
                <option value="Recursos Humanos">Recursos Humanos</option>
              </select>
            </div>

            <!-- DESCRIPCIÓN -->
            <div class="space-y-2 pt-2">
              <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">{{ 'support.description_label' | translate:'DESCRIPCIÓN' }}</label>
              <textarea 
                formControlName="description"
                rows="6"
                placeholder="Describe detalladamente el problema..."
                class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-400/10 transition-all resize-none placeholder:text-slate-300"
              ></textarea>
            </div>

            <!-- Submit Button -->
            <div class="pt-6">
              <button 
                type="submit"
                [disabled]="ticketForm.invalid || isSaving() || isLoadingConstants()"
                class="w-full py-4 bg-[#87C2E0] hover:bg-[#72AECF] text-white rounded-[1rem] text-[13px] font-black uppercase tracking-[0.2em] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {{ isSaving() ? ('support.sending' | translate:'ENVIANDO...') : ('support.create_ticket' | translate:'CREAR TICKET') }}
              </button>
            </div>
          </form>
        </ng-container>

      </div>

      <!-- Sticky Footer / MCP Status -->
      <div class="py-5 border-t border-slate-100 flex justify-center items-center gap-2 bg-white mt-auto z-10">
        <div class="w-1.5 h-1.5 rounded-full bg-[#00E59B] animate-pulse shadow-[0_0_8px_rgba(0,229,155,0.6)]"></div>
        <span class="text-[10px] font-black text-[#00E59B] uppercase tracking-[0.2em]">{{ 'support.service_active' | translate:'SERVICIO UNIFICADO ACTIVO' }}</span>
      </div>

    </div>
  `,
  styles: [`
    .animate-fade-in {
      animation: fadeIn 0.3s ease-in-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-4px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class TicketsFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private supportService = inject(SupportService);
  private notifications = inject(NotificationService);
  drawerService = inject(SideDrawerService);

  // Data receiving interface from SideDrawer setup (if any init data is passed)
  set data(val: any) {
    // Currently purely for creation
  }

  // View State
  view = signal<'list' | 'form'>('list');
  
  // Data States
  tickets = signal<any[]>([]);
  isLoadingTickets = signal<boolean>(false);
  isLoadingConstants = signal<boolean>(true);
  isSaving = signal<boolean>(false);
  constants = signal<any>(null);

  // Computed signals for reactive UI logic
  isMaintenance = computed(() => this.ticketForm.get('ticket_type')?.value === 'Mantenimiento');
  isSupport = computed(() => this.ticketForm.get('ticket_type')?.value === 'Soporte');

  ticketForm: FormGroup = this.fb.group({
    title: ['', [Validators.required, Validators.minLength(5)]],
    description: ['', [Validators.required, Validators.minLength(10)]],
    ticket_type: ['Soporte'], // Defaulted as requested by simplified UI
    priority: ['Media', Validators.required],
    area: ['Sistemas'], // Defaulted
    station_id: ['']
  });

  ngOnInit(): void {
    // Ya no dependemos de cargar constantes vía HTTP porque ahora las definimos estáticamente o las provee el SupportService.
    this.isLoadingConstants.set(false);
    this.loadTickets();

    // Reactive validation logic for Contextual Fields
    this.ticketForm.get('ticket_type')?.valueChanges.subscribe(type => {
      const stationCtrl = this.ticketForm.get('station_id');
      if (type === 'Mantenimiento') {
        stationCtrl?.setValidators([Validators.required]);
      } else {
        stationCtrl?.clearValidators();
      }
      stationCtrl?.updateValueAndValidity();
    });
  }

  switchView(newView: 'list' | 'form') {
    this.view.set(newView);
    if (newView === 'form') {
      this.ticketForm.reset({
        ticket_type: 'Soporte',
        priority: 'Media',
        area: 'Sistemas'
      });
    }
  }

  private async loadTickets() {
    this.isLoadingTickets.set(true);
    try {
      await this.supportService.loadTickets();
      const ts = this.supportService.tickets();
      // Filtrar pendientes
      const pendingTickets = ts.filter(t => 
        t.status !== TicketStatus.RESOLVED && 
        t.status !== TicketStatus.CLOSED && 
        t.status !== TicketStatus.CANCELED
      );
      this.tickets.set(pendingTickets);
    } catch (error) {
      this.notifications.error('Error', 'No se pudieron cargar los tickets.');
    } finally {
      this.isLoadingTickets.set(false);
    }
  }

  getPriorityColor(priority: string): string {
    if (!priority) return 'bg-slate-400';
    const p = priority.toUpperCase();
    if (p.includes('ALTA') || p.includes('HIGH') || p.includes('CRITICAL')) return 'bg-orange-500';
    if (p.includes('MEDIA') || p.includes('MEDIUM')) return 'bg-blue-500';
    return 'bg-emerald-500';
  }



  async save() {
    if (this.ticketForm.invalid || this.isSaving()) {
      this.ticketForm.markAllAsTouched();
      return;
    }

    this.isSaving.set(true);

    const formValues = this.ticketForm.value;

    try {
      // Map priority to uppercase enum value expected by the backend
      const priorityMap: any = {
        'Baja': 'Baja',
        'Media': 'Media',
        'Alta': 'Alta',
        'Crítica': 'Crítica'
      };

      await this.supportService.createTicket(
        formValues.title,
        formValues.description,
        priorityMap[formValues.priority] || 'MEDIUM',
        formValues.area
      );
      
      this.notifications.success('Éxito', 'Ticket creado correctamente.');
      this.loadTickets(); // Refresh list inside the drawer
      this.switchView('list'); // Return to list view instead of closing drawer
      this.drawerService.notifyRefresh(); // Tells the parent dashboard to refresh
    } catch (err: any) {
      const msg = err.error?.message || err.error?.detail || 'Error de conexión con el servidor.';
      this.notifications.error('Error', msg);
    } finally {
      this.isSaving.set(false);
    }
  }
}
