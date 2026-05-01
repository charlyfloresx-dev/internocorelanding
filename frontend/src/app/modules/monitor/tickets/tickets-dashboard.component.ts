import { Component, OnInit, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SupportService as TicketService } from '../../../core/services/support.service';
import { Ticket, TicketStatus, TicketPriority, ApiResponse } from '../../../core/models/support.types';
import { MatIconModule } from '@angular/material/icon';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-tickets-dashboard',
  standalone: true,
  imports: [CommonModule, MatIconModule, TranslatePipe],
  template: `
    <div class="p-6 space-y-6">
      <!-- Header -->
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-white flex items-center gap-2 uppercase tracking-tighter">
            <mat-icon class="text-blue-400">confirmation_number</mat-icon>
            {{ 'support.dashboard.title' | translate:'Centro de Soporte Industrial' }}
          </h1>
          <p class="text-[10px] text-slate-500 font-black uppercase tracking-widest">{{ 'support.dashboard.subtitle' | translate:'Gestión de tickets, escalaciones y mantenimiento preventivo.' }}</p>
        </div>
        <button class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-blue-900/20 uppercase text-xs font-black tracking-widest">
          <mat-icon class="text-sm">add</mat-icon>
          {{ 'support.new_ticket' | translate:'Nuevo Ticket' }}
        </button>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl backdrop-blur-sm relative overflow-hidden group">
          <div class="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full -mr-12 -mt-12 group-hover:scale-110 transition-transform"></div>
          <div class="flex justify-between items-start relative z-10">
            <div>
              <p class="text-[10px] text-slate-500 font-black uppercase tracking-widest">{{ 'support.dashboard.open_tickets' | translate:'Tickets Abiertos' }}</p>
              <h3 class="text-3xl font-black text-white mt-1">{{ openCount() }}</h3>
            </div>
            <div class="bg-blue-500/10 p-3 rounded-xl">
              <mat-icon class="text-blue-400">schedule</mat-icon>
            </div>
          </div>
        </div>
        
        <div class="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl backdrop-blur-sm relative overflow-hidden group">
          <div class="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full -mr-12 -mt-12 group-hover:scale-110 transition-transform"></div>
          <div class="flex justify-between items-start relative z-10">
            <div>
              <p class="text-[10px] text-slate-500 font-black uppercase tracking-widest">{{ 'support.dashboard.in_progress' | translate:'En Proceso' }}</p>
              <h3 class="text-3xl font-black text-amber-400 mt-1">{{ inProgressCount() }}</h3>
            </div>
            <div class="bg-amber-500/10 p-3 rounded-xl">
              <mat-icon class="text-amber-400">engineering</mat-icon>
            </div>
          </div>
        </div>

        <div class="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl backdrop-blur-sm relative overflow-hidden group">
          <div class="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full -mr-12 -mt-12 group-hover:scale-110 transition-transform"></div>
          <div class="flex justify-between items-start relative z-10">
            <div>
              <p class="text-[10px] text-slate-500 font-black uppercase tracking-widest">{{ 'support.dashboard.resolved_today' | translate:'Resueltos Hoy' }}</p>
              <h3 class="text-3xl font-black text-emerald-400 mt-1">{{ resolvedTodayCount() }}</h3>
            </div>
            <div class="bg-emerald-500/10 p-3 rounded-xl">
              <mat-icon class="text-emerald-400">check_circle</mat-icon>
            </div>
          </div>
        </div>

        <div class="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl backdrop-blur-sm relative overflow-hidden group">
          <div class="absolute top-0 right-0 w-24 h-24 bg-rose-500/5 rounded-full -mr-12 -mt-12 group-hover:scale-110 transition-transform"></div>
          <div class="flex justify-between items-start relative z-10">
            <div>
              <p class="text-[10px] text-slate-500 font-black uppercase tracking-widest">{{ 'support.dashboard.sla_risk' | translate:'SLA en Riesgo' }}</p>
              <h3 class="text-3xl font-black text-rose-400 mt-1">{{ slaRiskCount() }}</h3>
            </div>
            <div class="bg-rose-500/10 p-3 rounded-xl">
              <mat-icon class="text-rose-400">priority_high</mat-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters & Search -->
      <div class="flex flex-col md:flex-row gap-4 bg-slate-900/30 p-4 rounded-2xl border border-slate-800/50 backdrop-blur-md">
        <div class="relative flex-1">
          <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">search</mat-icon>
          <input 
            type="text" 
            [placeholder]="'support.dashboard.search_placeholder' | translate:'Buscar por folio o descripción...'" 
            class="w-full bg-slate-950/50 border border-slate-800 rounded-xl py-3 pl-12 pr-4 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all placeholder:text-slate-700"
          >
        </div>
        <div class="flex gap-2">
          <select class="bg-slate-950/50 border border-slate-800 text-slate-400 rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all">
            <option value="">{{ 'support.dashboard.filter_priority' | translate:'Prioridad: Todas' }}</option>
            <option value="CRITICAL">{{ 'support.priority.critical' | translate:'Crítica' }}</option>
            <option value="HIGH">{{ 'support.priority.high' | translate:'Alta' }}</option>
            <option value="MEDIUM">{{ 'support.priority.medium' | translate:'Media' }}</option>
            <option value="LOW">{{ 'support.priority.low' | translate:'Baja' }}</option>
          </select>
          <select class="bg-slate-950/50 border border-slate-800 text-slate-400 rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all">
            <option value="">{{ 'support.dashboard.filter_status' | translate:'Estado: Todos' }}</option>
            <option value="NEW">{{ 'support.status.new' | translate:'Nuevo' }}</option>
            <option value="IN_PROGRESS">{{ 'support.status.in_progress' | translate:'En Proceso' }}</option>
            <option value="RESOLVED">{{ 'support.status.resolved' | translate:'Resuelto' }}</option>
          </select>
        </div>
      </div>

      <!-- Tickets Grid -->
      <div class="grid grid-cols-1 gap-4 pb-12">
        @for (ticket of tickets(); track ticket.id) {
          <div class="bg-slate-900/40 border border-slate-800/60 p-5 rounded-2xl hover:bg-slate-900/60 hover:border-slate-700 transition-all cursor-pointer group relative overflow-hidden">
            <div class="absolute top-0 left-0 w-1 h-full" [class]="getPriorityBorderClass(ticket.priority)"></div>
            
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
              <div class="flex items-start gap-5">
                <div [class]="getPriorityClass(ticket.priority)" class="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 shadow-xl transition-transform group-hover:scale-105">
                  <mat-icon>{{ getTicketTypeIcon(ticket.id) }}</mat-icon>
                </div>
                <div class="space-y-1">
                  <div class="flex items-center gap-3">
                    <span class="text-[10px] font-black text-slate-500 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 uppercase tracking-[0.2em]">
                      {{ ticket.reference_code }}
                    </span>
                    <span [class]="getStatusClass(ticket.status)" class="text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest">
                      {{ 'support.status.' + ticket.status.toLowerCase() | translate:ticket.status }}
                    </span>
                  </div>
                  <h4 class="text-white font-bold text-lg group-hover:text-blue-400 transition-colors uppercase tracking-tight">{{ ticket.title }}</h4>
                  <p class="text-slate-500 text-sm line-clamp-1 font-medium italic">{{ ticket.description }}</p>
                </div>
              </div>
              
              <div class="flex items-center gap-8 text-[10px] border-t md:border-t-0 border-slate-800/50 pt-4 md:pt-0">
                <div class="flex flex-col items-end">
                  <span class="text-slate-600 font-black uppercase tracking-[0.2em] mb-1">Responsable</span>
                  <div class="flex items-center gap-2">
                    <div class="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
                       <mat-icon class="text-[14px]">person</mat-icon>
                    </div>
                    <span class="text-slate-300 font-bold uppercase tracking-tighter">{{ ticket.assigned_to_id || 'PENDIENTE' }}</span>
                  </div>
                </div>
                <div class="flex flex-col items-end min-w-[100px]">
                  <span class="text-slate-600 font-black uppercase tracking-[0.2em] mb-1">Registro</span>
                  <span class="text-slate-400 font-mono">{{ ticket.created_at | date:'dd/MM/yyyy HH:mm' }}</span>
                </div>
                <mat-icon class="text-slate-700 group-hover:text-blue-500 transition-colors">chevron_right</mat-icon>
              </div>
            </div>
          </div>
        } @empty {
          <div class="text-center py-24 bg-slate-900/10 border-2 border-dashed border-slate-800/50 rounded-[2rem] backdrop-blur-sm">
            <div class="w-20 h-20 bg-slate-800/30 rounded-full flex items-center justify-center mx-auto mb-6">
              <mat-icon class="text-4xl text-slate-700">find_in_page</mat-icon>
            </div>
            <h3 class="text-xl font-black text-slate-500 uppercase tracking-tighter">No hay tickets activos</h3>
            <p class="text-slate-600 text-[10px] font-black uppercase tracking-widest mt-2 max-w-xs mx-auto leading-relaxed">
              El sistema de monitoreo está limpio. Los paros operativos y solicitudes de mantenimiento aparecerán aquí.
            </p>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; min-height: 100vh; background: transparent; }
    .industrial-card {
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.5) 0%, rgba(2, 6, 23, 0.7) 100%);
    }
  `]
})
export class TicketsDashboardComponent implements OnInit {
  private ticketService = inject(TicketService);

  tickets = signal<Ticket[]>([]);
  openCount = signal(0);
  inProgressCount = signal(0);
  resolvedTodayCount = signal(0);
  slaRiskCount = signal(0);

  constructor() {
    effect(() => {
      const ts = this.ticketService.tickets();
      this.tickets.set(ts);
      this.calculateStats(ts);
    });
  }

  ngOnInit() {
    this.ticketService.loadTickets();
  }


  calculateStats(tickets: Ticket[]) {
    this.openCount.set(tickets.filter(t => t.status === TicketStatus.NEW).length);
    this.inProgressCount.set(tickets.filter(t => t.status === TicketStatus.IN_PROGRESS).length);
    this.resolvedTodayCount.set(tickets.filter(t => t.status === TicketStatus.RESOLVED).length);
    this.slaRiskCount.set(tickets.filter(t => t.priority === TicketPriority.CRITICAL && t.status !== TicketStatus.CLOSED).length);
  }

  getPriorityClass(priority: TicketPriority): string {
    switch (priority) {
      case TicketPriority.CRITICAL: return 'bg-rose-500/20 text-rose-500 border border-rose-500/30';
      case TicketPriority.HIGH: return 'bg-orange-500/20 text-orange-500 border border-orange-500/30';
      case TicketPriority.MEDIUM: return 'bg-blue-500/20 text-blue-500 border border-blue-500/30';
      default: return 'bg-slate-800 text-slate-500 border border-slate-700';
    }
  }

  getPriorityBorderClass(priority: TicketPriority): string {
    switch (priority) {
      case TicketPriority.CRITICAL: return 'bg-rose-500';
      case TicketPriority.HIGH: return 'bg-orange-500';
      case TicketPriority.MEDIUM: return 'bg-blue-500';
      default: return 'bg-slate-700';
    }
  }

  getStatusClass(status: TicketStatus): string {
    switch (status) {
      case TicketStatus.NEW: return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
      case TicketStatus.IN_PROGRESS: return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
      case TicketStatus.RESOLVED: return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      case TicketStatus.CLOSED: return 'bg-slate-500/10 text-slate-500 border border-slate-500/20';
      default: return 'bg-slate-500/10 text-slate-400';
    }
  }

  getTicketTypeIcon(id: string): string {
    return 'confirmation_number';
  }
}
