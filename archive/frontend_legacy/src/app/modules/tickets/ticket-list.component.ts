import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TicketService } from '@services/ticket.service';
import { TicketStatus, TicketPriority } from '@models/api.types';

@Component({
    selector: 'app-ticket-list',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="container-fixed py-10">
      
      <!-- Header Block -->
      <div class="flex justify-between items-center mb-8">
        <div>
          <h1 class="text-2xl font-bold text-white mb-2">Tickets de Soporte</h1>
          <p class="text-slate-400 text-sm">Gestione las incidencias y solicitudes de su organización</p>
        </div>
        <button (click)="createTicket()" class="btn btn-primary flex items-center gap-2">
          <i class="ki-filled ki-plus"></i> Nuevo Ticket
        </button>
      </div>

      <!-- Stats Block -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="card p-6 bg-slate-900 border-slate-800">
          <div class="text-slate-500 text-xs font-bold uppercase mb-2">Total Tickets</div>
          <div class="text-3xl font-bold text-white">{{ service.tickets().length }}</div>
        </div>
        <div class="card p-6 bg-slate-900 border-slate-800">
           <div class="text-slate-500 text-xs font-bold uppercase mb-2">Pendientes</div>
           <div class="text-3xl font-bold text-sky-400">{{ countByStatus('New') }}</div>
        </div>
        <div class="card p-6 bg-slate-900 border-slate-800">
           <div class="text-slate-500 text-xs font-bold uppercase mb-2">En Progreso</div>
           <div class="text-3xl font-bold text-amber-500">{{ countByStatus('InProgress') }}</div>
        </div>
        <div class="card p-6 bg-slate-900 border-slate-800">
           <div class="text-slate-500 text-xs font-bold uppercase mb-2">Resueltos</div>
           <div class="text-3xl font-bold text-green-500">{{ countByStatus('Resolved') }}</div>
        </div>
      </div>

      <!-- Data Block: Table -->
      <div class="card bg-slate-900 border-slate-800 shadow-sm overflow-hidden">
        <div class="card-header border-slate-800 py-4 px-6 flex justify-between items-center">
          <h3 class="text-white font-bold">Listado General</h3>
          <div class="flex gap-2">
             <span class="badge badge-outline text-[10px]">Actualizado hoy</span>
          </div>
        </div>
        <div class="table-responsive">
          <table class="table table-align-middle w-full text-slate-300">
            <thead class="bg-slate-950 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
              <tr>
                <th class="px-6 py-4 text-left">Referencia</th>
                <th class="px-6 py-4 text-left">Título</th>
                <th class="px-6 py-4 text-left">Prioridad</th>
                <th class="px-6 py-4 text-left">Estado</th>
                <th class="px-6 py-4 text-left">Asignado</th>
                <th class="px-6 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
              @for (t of service.tickets(); track t.id) {
                <tr class="hover:bg-slate-800/50 transition-colors">
                  <td class="px-6 py-4 font-mono text-sky-400 font-bold">{{ t.reference_code }}</td>
                  <td class="px-6 py-4">
                    <div class="text-white font-medium">{{ t.title }}</div>
                    <div class="text-slate-500 text-xs truncate max-w-xs">{{ t.description }}</div>
                  </td>
                  <td class="px-6 py-4">
                     <span [class]="getPriorityClass(t.priority)" class="badge text-[10px] font-bold">
                        {{ t.priority }}
                     </span>
                  </td>
                  <td class="px-6 py-4">
                     <span [class]="getStatusClass(t.status)" class="badge badge-outline text-[10px] font-bold">
                        {{ t.status }}
                     </span>
                  </td>
                  <td class="px-6 py-4 text-slate-400">
                    @if (t.assigned_to_id) {
                      <div class="flex items-center gap-2">
                        <div class="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-[10px]">
                          {{ t.assigned_to_id.substring(0, 2).toUpperCase() }}
                        </div>
                        {{ 'Agente ' + t.assigned_to_id.substring(0, 4) }}
                      </div>
                    } @else {
                      <span class="text-slate-600 italic">No asignado</span>
                    }
                  </td>
                  <td class="px-6 py-4 text-right">
                    <button (click)="viewTicket(t.id)" class="btn btn-sm btn-light">
                      <i class="ki-filled ki-eye"></i> Ver
                    </button>
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="6" class="px-6 py-20 text-center text-slate-500 italic">
                    <i class="ki-filled ki-information text-3xl mb-4 opacity-20"></i>
                    <p>No se encontraron tickets en esta compañía.</p>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

    </div>
  `
})
export class TicketListComponent implements OnInit {
    public service = inject(TicketService);
    router = inject(Router);

    ngOnInit() {
        this.service.loadTickets();
    }

    createTicket() {
        this.router.navigate(['/tickets/new']);
    }

    viewTicket(id: string) {
        this.router.navigate(['/tickets/detail', id]);
    }

    countByStatus(status: string): number {
        return this.service.tickets().filter(t => t.status === status).length;
    }

    getPriorityClass(p: string): string {
        switch (p) {
            case 'Critical': return 'bg-red-500/20 text-red-500 border border-red-500/30';
            case 'High': return 'bg-orange-500/20 text-orange-500 border border-orange-500/30';
            case 'Medium': return 'bg-sky-500/20 text-sky-500 border border-sky-500/30';
            default: return 'bg-slate-500/20 text-slate-400 border border-slate-500/30';
        }
    }

    getStatusClass(s: string): string {
        switch (s) {
            case 'New': return 'border-sky-500 text-sky-500';
            case 'InProgress': return 'border-amber-500 text-amber-500';
            case 'Resolved': return 'border-green-500 text-green-500';
            case 'Closed': return 'border-slate-500 text-slate-500 opacity-60';
            case 'Canceled': return 'border-red-500 text-red-500';
            default: return 'border-slate-500 text-slate-400';
        }
    }
}
