import { Component, OnInit, inject, signal, effect, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { SupportService as TicketService } from '../../../core/services/support.service';
import { AuthService } from '../../../core/services/auth.service';
import { Ticket, TicketStatus, TicketPriority } from '../../../core/models/support.types';
import { MatIconModule } from '@angular/material/icon';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocalDatePipe } from '../../../shared/pipes/local-date.pipe';
import { SideDrawerService } from '../../../core/services/side-drawer.service';
import { TicketsFormComponent } from './components/tickets-form.component';
import { AdminService, AdminUser } from '../../../core/services/admin.service';
import { ToastService } from '../../../core/services/toast.service';
import { MatMenuModule } from '@angular/material/menu';
import { MatButtonModule } from '@angular/material/button';
import { TicketTriageDrawerComponent } from './components/ticket-triage-drawer.component';

@Component({
  selector: 'app-tickets-dashboard',
  standalone: true,
  imports: [CommonModule, MatIconModule, TranslatePipe, MatMenuModule, MatButtonModule, TicketTriageDrawerComponent, RouterModule, LocalDatePipe],
  template: `
    <div class="p-6 animate-fade-in flex flex-col min-h-full w-full">
      
      <!-- Compact Industrial Header (Filter Bar) -->
      <header class="mb-6 flex flex-wrap justify-between items-center bg-surface-card border border-surface-border rounded-2xl px-6 py-3 shadow-sm backdrop-blur-md no-print z-50">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
            <mat-icon class="text-xl text-primary">support_agent</mat-icon>
          </div>
          <div class="flex flex-col">
            <h1 class="text-lg font-black tracking-tight text-surface-text leading-none">
              Support <span class="text-primary">Tickets</span>
            </h1>
            <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] mt-1">
              {{ 'support.dashboard.kanban' | translate:'TICKETS KANBAN DASHBOARD' }}
            </span>
          </div>
        </div>

        <div class="flex items-center gap-6">
          
          <!-- View Toggle (Supervisors only) -->
          <div *ngIf="isSupervisor()" class="hidden md:flex bg-surface-text/[0.05] p-1 rounded-xl">
            <button 
              (click)="viewFilter.set('MINE')"
              [class.bg-white]="viewFilter() === 'MINE'"
              [class.text-surface-text]="viewFilter() === 'MINE'"
              [class.shadow-sm]="viewFilter() === 'MINE'"
              [class.text-surface-text-muted]="viewFilter() !== 'MINE'"
              class="px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all">
              {{ 'support.dashboard.my_tickets' | translate:'MIS TICKETS' }}
            </button>
            <button 
              (click)="viewFilter.set('ALL')"
              [class.bg-white]="viewFilter() === 'ALL'"
              [class.text-surface-text]="viewFilter() === 'ALL'"
              [class.shadow-sm]="viewFilter() === 'ALL'"
              [class.text-surface-text-muted]="viewFilter() !== 'ALL'"
              class="px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all">
              {{ 'support.dashboard.dept_tickets' | translate:'DEPARTAMENTO' }}
            </button>
          </div>

          <div class="hidden sm:block h-8 w-px bg-surface-border/60"></div>
          
          <div class="flex items-center gap-3 relative">
             <span class="hidden sm:inline text-[9px] font-black text-surface-text-muted uppercase tracking-widest">{{ 'support.dashboard.sla_compliance' | translate:'SLA CUMPLIMIENTO:' }}</span>
             <span class="text-sm font-black text-surface-text">98.5%</span>
             <mat-icon class="text-emerald-500 text-sm">trending_up</mat-icon>
          </div>
          <div class="hidden sm:block h-8 w-px bg-surface-border/60"></div>
          <button [routerLink]="['/monitor/flows']" class="bg-surface-text/5 hover:bg-surface-text/10 text-surface-text rounded-xl px-4 py-2 flex items-center gap-2 transition-all border border-surface-border">
            <mat-icon class="text-[18px]">account_tree</mat-icon>
            <span class="text-[10px] font-black uppercase tracking-wider">Simulador</span>
          </button>
          <button (click)="openNewTicket()" class="bg-primary hover:bg-primary-dark text-white rounded-xl px-4 py-2 flex items-center gap-2 transition-all shadow-lg shadow-primary/20 hover:scale-105 active:scale-95">
            <mat-icon class="text-[18px]">add</mat-icon>
            <span class="text-[10px] font-black uppercase tracking-wider">{{ 'support.dashboard.new_ticket' | translate:'NUEVO TICKET' }}</span>
          </button>
        </div>
      </header>

      <!-- Kanban Board -->
      <div class="flex-1 flex flex-col lg:flex-row gap-6 w-full pb-10 custom-scrollbar overflow-x-auto">
        
        <!-- COLUMN 1: DETECTADAS (NUEVOS + PENDING APPROVAL) -->
        <div class="lg:flex flex-1 flex-col min-w-0 transition-all animate-fade-in !overflow-visible min-w-[340px]"
             (dragover)="onDragOver($event)"
             (drop)="onDrop($event, 'NEW')">
          <div class="flex justify-between items-center px-4 mb-3">
            <div class="flex items-center gap-2">
              <div class="h-2 w-2 rounded-full bg-primary"></div>
              <h2 class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">{{ 'support.status.new_plural' | translate:'NUEVOS' }}</h2>
            </div>
            <span class="text-[10px] font-black text-surface-text-muted px-2 py-0.5 rounded-md bg-surface-text/5 border border-surface-border">{{ ticketsNew().length }}</span>
          </div>
          
          <div class="flex-1 bg-surface-text/[0.02] dark:bg-white/[0.02] border border-surface-border/50 rounded-2xl p-4 flex flex-col gap-5 transition-all duration-300 min-h-[400px]">
            @for (ticket of ticketsNew(); track ticket.id) {
              <div draggable="true" 
                   (click)="openTriage(ticket)"
                   (dragstart)="onDragStart($event, ticket)" 
                   [class.border-l-primary]="ticket.status !== TicketStatus.PENDING_APPROVAL"
                   [class.border-l-amber-500]="ticket.status === TicketStatus.PENDING_APPROVAL"
                   [class.ring-2]="ticket.status === TicketStatus.PENDING_APPROVAL"
                   [class.ring-amber-500/30]="ticket.status === TicketStatus.PENDING_APPROVAL"
                   [class.bg-amber-500/[0.02]]="ticket.status === TicketStatus.PENDING_APPROVAL"
                   class="bg-surface-card border border-surface-border border-l-[4px] rounded-xl p-4 shadow-sm hover:border-primary/50 transition-all cursor-pointer active:cursor-grabbing relative overflow-hidden group w-full">
                
                <div class="flex justify-between items-start mb-4">
                  <div>
                    <p class="text-[8px] font-black text-surface-text-muted uppercase tracking-[0.2em] mb-1">{{ 'support.dashboard.ticket_folio' | translate:'FOLIO TICKET' }}</p>
                    <h4 class="text-[13px] font-black text-surface-text">{{ ticket.reference_code || ('#TKT-' + ticket.id.slice(-4).toUpperCase()) }}</h4>
                  </div>
                  <span class="text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded-md border"
                        [ngClass]="ticket.status === TicketStatus.PENDING_APPROVAL ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' : 'bg-primary/10 text-primary border-primary/20'">
                    {{ ticket.status }}
                  </span>
                </div>
                
                <div class="flex items-start gap-3 mb-6">
                  <mat-icon class="text-surface-text-muted text-[16px] mt-0.5">engineering</mat-icon>
                  <div>
                    <h5 class="text-[11px] font-black text-surface-text leading-snug uppercase">{{ ticket.title }}</h5>
                    <p class="text-[9px] text-surface-text-muted mt-1 line-clamp-2 leading-relaxed italic">{{ ticket.description }}</p>
                  </div>
                </div>
                
                <div class="flex justify-between items-end border-t border-surface-border/50 pt-3">
                  <div>
                    <p class="text-[7px] font-black text-surface-text-muted uppercase tracking-widest mb-1">{{ 'support.dashboard.priority_type' | translate:'PRIORIDAD' }}</p>
                    <p class="text-[11px] font-black" [ngClass]="getPriorityTextColor(ticket.priority)">{{ ticket.priority }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-[7px] font-black text-surface-text-muted uppercase tracking-widest mb-1 flex items-center gap-1 justify-end">
                      <mat-icon class="text-[8px]">event</mat-icon> {{ 'support.dashboard.registered_at' | translate:'REGISTRO' }}
                    </p>
                    <p class="text-[11px] font-black text-surface-text">{{ ticket.created_at | localDate:'dd/MM/yyyy' }}</p>
                  </div>
                </div>

                <!-- Supervision Action Row -->
                <div *ngIf="isSupervisor() && (ticket.status === TicketStatus.PENDING_APPROVAL || !ticket.assigned_to_id)" class="mt-4 pt-3 border-t border-dashed border-primary/20">
                  <div class="flex items-center justify-between gap-2">
                    <div class="flex flex-col">
                      <span class="text-[7px] font-black text-primary uppercase tracking-widest">{{ 'support.dashboard.quick_triage' | translate:'TRIAJE RÁPIDO' }}</span>
                    </div>
                    <div class="flex gap-2">
                      <button *ngIf="ticket.status === TicketStatus.PENDING_APPROVAL" 
                              (click)="handleQuickApprove(ticket)"
                              [disabled]="isLoadingTriage()"
                              class="bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg px-3 py-1.5 flex items-center gap-1 transition-all shadow-sm active:scale-95 disabled:opacity-50">
                        <mat-icon class="text-[14px]">check_circle</mat-icon>
                        <span class="text-[9px] font-black uppercase">{{ 'common.approve' | translate:'APROBAR' }}</span>
                      </button>
                      
                      <button [matMenuTriggerFor]="techMenu"
                              [disabled]="isLoadingTriage()"
                              class="bg-primary/10 hover:bg-primary/20 text-primary rounded-lg px-3 py-1.5 flex items-center gap-1 transition-all border border-primary/20 active:scale-95 disabled:opacity-50">
                        <mat-icon class="text-[14px]">person_add</mat-icon>
                        <span class="text-[9px] font-black uppercase">{{ 'common.assign' | translate:'ASIGNAR' }}</span>
                      </button>

                      <mat-menu #techMenu="matMenu">
                        <div class="px-3 py-2 border-b border-surface-border">
                          <p class="text-[8px] font-black text-surface-text-muted uppercase tracking-widest">SELECCIONAR TÉCNICO</p>
                        </div>
                        <button mat-menu-item *ngFor="let tech of technicians()" (click)="handleQuickAssign(ticket, tech.id)">
                          <div class="flex flex-col py-1">
                            <span class="text-xs font-black text-surface-text">{{ tech.full_name }}</span>
                            <span class="text-[9px] text-surface-text-muted flex items-center gap-1">
                              <mat-icon class="text-[10px]" [ngClass]="getTechWorkload(tech.id) > 3 ? 'text-amber-500' : 'text-emerald-500'">task_alt</mat-icon>
                              {{ getTechWorkload(tech.id) }} tickets activos
                            </span>
                          </div>
                        </button>
                      </mat-menu>
                    </div>
                  </div>
                </div>
              </div>
            }
            @if (ticketsNew().length === 0) {
              <div class="flex-1 flex flex-col items-center justify-center text-surface-text-muted opacity-30 select-none">
                <mat-icon class="text-4xl mb-2">dashboard_customize</mat-icon>
                <p class="text-[8px] font-black uppercase tracking-[0.3em]">{{ 'support.dashboard.no_tickets' | translate:'SIN TICKETS' }}</p>
              </div>
            }
          </div>
        </div>

        <!-- COLUMN 2: EN PROCESO -->
        <div class="lg:flex flex-1 flex-col min-w-0 transition-all animate-fade-in !overflow-visible min-w-[340px]"
             (dragover)="onDragOver($event)"
             (drop)="onDrop($event, 'IN_PROGRESS')">
          <div class="flex justify-between items-center px-4 mb-3">
            <div class="flex items-center gap-2">
              <div class="h-2 w-2 rounded-full bg-amber-500"></div>
              <h2 class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">{{ 'support.status.in_progress' | translate:'EN PROCESO' }}</h2>
            </div>
            <span class="text-[10px] font-black text-surface-text-muted px-2 py-0.5 rounded-md bg-surface-text/5 border border-surface-border">{{ ticketsInProgress().length }}</span>
          </div>
          
          <div class="flex-1 bg-surface-text/[0.02] dark:bg-white/[0.02] border border-surface-border/50 rounded-2xl p-4 flex flex-col gap-5 transition-all duration-300 min-h-[400px]">
            @for (ticket of ticketsInProgress(); track ticket.id) {
              <div draggable="true" (click)="openTriage(ticket)" (dragstart)="onDragStart($event, ticket)" class="bg-surface-card border border-surface-border border-l-[4px] border-l-amber-500 rounded-xl p-4 shadow-sm hover:border-amber-500/50 transition-all cursor-pointer active:cursor-grabbing relative overflow-hidden group w-full">
                <div class="flex justify-between items-start mb-4">
                  <div>
                    <p class="text-[8px] font-black text-surface-text-muted uppercase tracking-[0.2em] mb-1">{{ 'support.dashboard.ticket_folio' | translate:'FOLIO TICKET' }}</p>
                    <h4 class="text-[13px] font-black text-surface-text">{{ ticket.reference_code || ('#TKT-' + ticket.id.slice(-4).toUpperCase()) }}</h4>
                  </div>
                  <span class="bg-amber-500/10 text-amber-500 text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded-md border border-amber-500/20">
                    {{ ticket.status }}
                  </span>
                </div>
                
                <div class="flex items-start gap-3 mb-6">
                  <mat-icon class="text-surface-text-muted text-[16px] mt-0.5">engineering</mat-icon>
                  <div>
                    <h5 class="text-[11px] font-black text-surface-text leading-snug uppercase">{{ ticket.title }}</h5>
                    <p class="text-[9px] text-surface-text-muted mt-1 line-clamp-2 leading-relaxed italic">{{ ticket.description }}</p>
                  </div>
                </div>
                
                <div class="flex justify-between items-end border-t border-surface-border/50 pt-3">
                  <div>
                    <p class="text-[7px] font-black text-surface-text-muted uppercase tracking-widest mb-1">{{ 'support.dashboard.priority_type' | translate:'PRIORIDAD' }}</p>
                    <p class="text-[11px] font-black" [ngClass]="getPriorityTextColor(ticket.priority)">{{ ticket.priority }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-[7px] font-black text-surface-text-muted uppercase tracking-widest mb-1 flex items-center gap-1 justify-end">
                      <mat-icon class="text-[8px]">people</mat-icon> {{ 'support.dashboard.responsible' | translate:'RESPONSABLE' }}
                    </p>
                    <div class="flex flex-wrap gap-1 justify-end mt-1">
                      @for (label of getAssignedLabels(ticket); track label.id) {
                        <span class="text-[9px] font-black px-1.5 py-0.5 rounded-md border"
                              [ngClass]="label.css">{{ label.name }}</span>
                      }
                      @if (getAssignedLabels(ticket).length === 0) {
                        <span class="text-[10px] font-black text-surface-text-muted">PENDIENTE</span>
                      }
                    </div>
                  </div>
                </div>
              </div>
            }
          </div>
        </div>

        <!-- COLUMN 3: RESUELTOS -->
        <div class="lg:flex flex-1 flex-col min-w-0 transition-all animate-fade-in !overflow-visible min-w-[340px]"
             (dragover)="onDragOver($event)"
             (drop)="onDrop($event, 'RESOLVED')">
          <div class="flex justify-between items-center px-4 mb-3">
            <div class="flex items-center gap-2">
              <div class="h-2 w-2 rounded-full bg-emerald-500"></div>
              <h2 class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">{{ 'support.status.resolved_plural' | translate:'RESUELTOS' }}</h2>
            </div>
            <span class="text-[10px] font-black text-surface-text-muted px-2 py-0.5 rounded-md bg-surface-text/5 border border-surface-border">{{ ticketsResolved().length }}</span>
          </div>
          
          <div class="flex-1 bg-surface-text/[0.02] dark:bg-white/[0.02] border border-surface-border/50 rounded-2xl p-4 flex flex-col gap-5 transition-all duration-300 min-h-[400px]">
            @for (ticket of ticketsResolved(); track ticket.id) {
              <div draggable="true" (click)="openTriage(ticket)" (dragstart)="onDragStart($event, ticket)" class="bg-surface-card border border-surface-border border-l-[4px] border-l-emerald-500 rounded-xl p-4 shadow-sm hover:border-emerald-500/50 transition-all cursor-pointer active:cursor-grabbing relative overflow-hidden group opacity-75 hover:opacity-100 w-full">
                <div class="flex justify-between items-start mb-4">
                  <div>
                    <p class="text-[8px] font-black text-surface-text-muted uppercase tracking-[0.2em] mb-1">{{ 'support.dashboard.ticket_folio' | translate:'FOLIO TICKET' }}</p>
                    <h4 class="text-[13px] font-black text-surface-text line-through decoration-surface-border">{{ ticket.reference_code || ('#TKT-' + ticket.id.slice(-4).toUpperCase()) }}</h4>
                  </div>
                  <span class="bg-emerald-500/10 text-emerald-500 text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded-md border border-emerald-500/20">
                    {{ ticket.status }}
                  </span>
                </div>
                
                <div class="flex items-start gap-3 mb-6">
                  <mat-icon class="text-surface-text-muted text-[16px] mt-0.5">check_circle</mat-icon>
                  <div>
                    <h5 class="text-[11px] font-black text-surface-text leading-snug uppercase">{{ ticket.title }}</h5>
                    <p class="text-[9px] text-surface-text-muted mt-1 line-clamp-1 italic">{{ ticket.description }}</p>
                  </div>
                </div>
              </div>
            }
          </div>
        </div>

      </div>
    </div>
    
    <!-- Triage Drawer -->
    <app-ticket-triage-drawer 
      [ticket]="selectedTicket()" 
      (close)="selectedTicket.set(null)">
    </app-ticket-triage-drawer>
  `,
  styles: [`
    :host { display: block; }
    .custom-scrollbar::-webkit-scrollbar { height: 6px; width: 6px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.3); border-radius: 10px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.6); }
  `]
})
export class TicketsDashboardComponent implements OnInit {
  private ticketService = inject(TicketService);
  private drawerService = inject(SideDrawerService);
  private authService = inject(AuthService);
  private adminService = inject(AdminService);
  private toastService = inject(ToastService);
  private route = inject(ActivatedRoute);

  TicketStatus = TicketStatus;
  tickets = signal<Ticket[]>([]);
  viewFilter = signal<'ALL' | 'MINE'>('ALL');
  selectedTicket = signal<Ticket | null>(null);

  // Supervision data
  allUsers = signal<AdminUser[]>([]);
  technicians = signal<AdminUser[]>([]);
  workload = signal<Record<string, number>>({});
  isLoadingTriage = signal<boolean>(false);

  isSupervisor = computed(() => {
    const roles = this.authService.roles();
    return roles.some((r: string) =>
      r.toLowerCase() === 'supervisor' ||
      r.toLowerCase().includes('admin') ||
      r.toLowerCase() === 'owner' ||
      r.toLowerCase().includes('manager')
    );
  });

  constructor() {
    effect(() => {
      let ts = this.ticketService.tickets();
      const session = this.authService.session();
      const userId = session?.user_id;

      if (this.viewFilter() === 'MINE' && userId) {
        // Incluir creados por o asignados a
        ts = ts.filter((t: Ticket) => t.assigned_to_id === userId || t.created_by === userId);
      }
      this.tickets.set(ts);
    });
  }

  // Kanban derived states
  ticketsNew = computed(() => this.tickets().filter(t => t.status === TicketStatus.NEW || t.status === TicketStatus.PENDING_APPROVAL));
  ticketsInProgress = computed(() => this.tickets().filter(t => t.status === TicketStatus.IN_PROGRESS || t.status === TicketStatus.ASSIGNED || t.status === TicketStatus.IN_REVIEW));
  ticketsResolved = computed(() => this.tickets().filter(t => t.status === TicketStatus.RESOLVED || t.status === TicketStatus.CLOSED));

  // Drag and drop state
  draggedTicket: Ticket | null = null;

  ngOnInit() {
    this.ticketService.loadTickets();

    // Leer filtro desde URL (ej: /monitor/tickets?filter=mine)
    this.route.queryParamMap.subscribe(params => {
      const f = params.get('filter');
      if (f === 'mine') {
        this.viewFilter.set('MINE');
      }
    });

    this.loadSupervisionData(); // Always load users for name mapping
    if (this.isSupervisor()) {
      // additional supervisor logic if needed
    }

    // Escuchar recargas desde el drawer
    this.drawerService.refresh$.subscribe(() => {
      this.ticketService.loadTickets();
      this.loadSupervisionData();
    });
  }

  async loadSupervisionData() {
    try {
      this.adminService.getUsers().subscribe(res => {
        if (res.data) {
          this.allUsers.set(res.data);
          this.technicians.set(res.data.filter(u =>
            u.role_name.toLowerCase().includes('technician') ||
            u.role_name.toLowerCase().includes('user') ||
            u.role_name.toLowerCase().includes('oper') ||
            u.role_name.toLowerCase().includes('admin')
          ));
        }
      });

      const wl = await this.ticketService.getTechniciansWorkload();
      this.workload.set(wl);
    } catch (err) {
      console.error('Error loading supervision data:', err);
    }
  }

  async handleQuickApprove(ticket: Ticket) {
    this.isLoadingTriage.set(true);
    try {
      await this.ticketService.triageTicket(ticket.id, 'APPROVE', [], 'Aprobación rápida desde Dashboard');
      this.toastService.success('Ticket aprobado correctamente');
      this.loadSupervisionData();
    } catch (err: any) {
      this.toastService.error(err.message || 'Error al aprobar ticket');
    } finally {
      this.isLoadingTriage.set(false);
    }
  }

  async handleQuickAssign(ticket: Ticket, techId: string) {
    this.isLoadingTriage.set(true);
    try {
      await this.ticketService.triageTicket(ticket.id, 'REASSIGN', [{ identity_type: 'INTERNAL', identity_id: techId, is_lead: true }], 'Asignación rápida desde Dashboard');
      this.toastService.success('Ticket asignado correctamente');
      this.loadSupervisionData();
    } catch (err: any) {
      this.toastService.error(err.message || 'Error al asignar ticket');
    } finally {
      this.isLoadingTriage.set(false);
    }
  }

  getTechWorkload(techId: string): number {
    return this.workload()[techId] || 0;
  }

  getUserName(id: string | null | undefined): string {
    if (!id) return 'PENDIENTE';
    const user = this.allUsers().find(u => u.id === id);
    if (user) {
      return user.full_name || user.email;
    }
    return id.split('-')[0].toUpperCase(); // fallback to short uuid part
  }

  openTriage(ticket: Ticket) {
    this.drawerService.open(TicketsFormComponent, {
      title: 'GESTIÓN DE TICKET',
      subtitle: ticket.reference_code,
      icon: 'engineering',
      width: 'w-[900px]'
    }, ticket);
  }

  openNewTicket() {
    this.drawerService.open(TicketsFormComponent, {
      title: 'NUEVO TICKET',
      subtitle: 'CENTRO DE SOPORTE',
      icon: 'smart_toy',
      width: 'w-[500px]'
    }, null);
  }

  onDragStart(event: DragEvent, ticket: Ticket) {
    this.draggedTicket = ticket;
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move';
    }
  }

  onDrop(event: DragEvent, newStatusStr: string) {
    event.preventDefault();
    if (!this.draggedTicket) return;

    let newStatus = TicketStatus.NEW;
    if (newStatusStr === 'IN_PROGRESS') newStatus = TicketStatus.IN_PROGRESS;
    if (newStatusStr === 'RESOLVED') newStatus = TicketStatus.RESOLVED;

    if (this.draggedTicket.status !== newStatus) {
      const ticketId = this.draggedTicket.id;
      const updatedTickets = this.tickets().map(t =>
        t.id === ticketId ? { ...t, status: newStatus } : t
      );
      this.tickets.set(updatedTickets);

      this.ticketService.updateTicketStatus(ticketId, newStatus).catch(() => {
        this.ticketService.loadTickets();
      });
    }

    this.draggedTicket = null;
  }

  getAssignedLabels(ticket: Ticket): { id: string; name: string; css: string }[] {
    const assignees = ticket.assignees ?? [];
    if (assignees.length > 0) {
      return assignees.map(a => {
        if (a.identity_type === 'INTERNAL') {
          return { id: a.identity_id, name: this.getUserName(a.identity_id), css: 'bg-amber-500/10 text-amber-600 border-amber-500/20' };
        } else if (a.identity_type === 'PLANTA') {
          return { id: a.identity_id, name: 'PLANTA', css: 'bg-teal-500/10 text-teal-600 border-teal-500/20' };
        } else {
          return { id: a.identity_id, name: 'EXTERNO', css: 'bg-purple-500/10 text-purple-600 border-purple-500/20' };
        }
      });
    }
    // Fallback legacy
    const labels: { id: string; name: string; css: string }[] = [];
    if (ticket.assigned_to_id) labels.push({ id: ticket.assigned_to_id, name: this.getUserName(ticket.assigned_to_id), css: 'bg-amber-500/10 text-amber-600 border-amber-500/20' });
    if (ticket.collaborator_id) labels.push({ id: ticket.collaborator_id, name: 'PLANTA', css: 'bg-teal-500/10 text-teal-600 border-teal-500/20' });
    if (ticket.external_contact_id) labels.push({ id: ticket.external_contact_id, name: 'EXTERNO', css: 'bg-purple-500/10 text-purple-600 border-purple-500/20' });
    return labels;
  }

  getPriorityTextColor(priority: string): string {
    const p = (priority || '').toUpperCase();
    if (p.includes('CRITICAL') || p.includes('ALTA')) return 'text-rose-500';
    if (p.includes('HIGH')) return 'text-orange-500';
    if (p.includes('MEDIUM') || p.includes('MEDIA')) return 'text-sky-500';
    return 'text-emerald-500';
  }
}
