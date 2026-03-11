import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { TicketService } from '@services/ticket.service';
import { AuthService } from '@services/auth.service';
import { TicketStatus, TicketPriority, TicketType, CreateTicketCommand, UpdateTicketCommand } from '@models/api.types';

@Component({
    selector: 'app-ticket-editor',
    standalone: true,
    imports: [CommonModule, FormsModule, ReactiveFormsModule],
    template: `
    <div class="min-h-screen bg-slate-950 pb-20">
      
      <!-- Top Bar / Header Block -->
      <div class="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6 sticky top-0 z-40">
        <div class="flex items-center gap-4">
          <button (click)="goBack()" class="w-8 h-8 rounded-full hover:bg-slate-800 text-slate-400 flex items-center justify-center transition-colors">
            <i class="ki-filled ki-arrow-left"></i>
          </button>
          <div class="flex items-center gap-3">
            <h1 class="text-xl font-bold text-white">{{ isEdit ? 'Detalle de Ticket' : 'Nueva Solicitud' }}</h1>
            @if (isEdit && service.currentTicket(); as t) {
              <span class="text-sky-400 font-mono font-bold">{{ t.reference_code }}</span>
              <span [class]="getStatusClass(t.status)" class="badge badge-outline text-[10px] font-bold">
                {{ t.status }}
              </span>
              @if (isLocked()) {
                <span class="bg-amber-500/10 text-amber-500 text-[10px] font-bold uppercase px-2 py-1 rounded border border-amber-500/20 flex items-center gap-1">
                  <i class="ki-filled ki-lock text-[10px]"></i> Bloqueado
                </span>
              }
            }
          </div>
        </div>
        <div class="flex items-center gap-3">
          @if (!isLocked()) {
            <button (click)="save()" [disabled]="form.invalid || service.loading()" 
                    class="btn btn-primary shadow-lg shadow-blue-900/20">
               <i class="ki-filled ki-check"></i> {{ isEdit ? 'Guardar Cambios' : 'Enviar Ticket' }}
            </button>
          }
        </div>
      </div>

      <div class="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- LEFT COL: FORM / DETAILS -->
        <div class="lg:col-span-8 space-y-6">
          
          <!-- Data Block: Form -->
          <div class="card bg-slate-900 border-slate-800 p-6 shadow-lg">
            <div class="card-header border-slate-800 pb-4 mb-6">
               <h3 class="text-slate-400 text-xs font-bold uppercase tracking-widest">Información de la Solicitud</h3>
            </div>
            
            <form [formGroup]="form" class="space-y-6">
              <div>
                 <label class="block text-slate-300 text-sm font-bold mb-2">Título del Ticket *</label>
                 <input type="text" formControlName="title" placeholder="Ej: Error al procesar pago, Olvido de contraseña..." 
                        class="input w-full bg-slate-950 border-slate-700 text-white focus:border-sky-500">
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                 <div>
                    <label class="block text-slate-300 text-xs font-bold mb-2">Tipo de Solicitud</label>
                    <select formControlName="ticket_type" class="select w-full bg-slate-950 border-slate-700 text-white focus:border-sky-500">
                       <option value="Support">Soporte Tecnico</option>
                       <option value="Incident">Incidencia / Bug</option>
                       <option value="Improvement">Mejora</option>
                       <option value="Task">Tarea Operativa</option>
                    </select>
                 </div>
                 <div>
                    <label class="block text-slate-300 text-xs font-bold mb-2">Prioridad</label>
                    <select formControlName="priority" class="select w-full bg-slate-950 border-slate-700 text-white focus:border-sky-500">
                       <option value="Low">Baja</option>
                       <option value="Medium">Media</option>
                       <option value="High">Alta</option>
                       <option value="Critical">Crítica</option>
                    </select>
                 </div>
              </div>

              @if (isEdit && !isLocked()) {
                <div>
                    <label class="block text-slate-300 text-xs font-bold mb-2">Estado Activo</label>
                    <select formControlName="status" class="select w-full bg-slate-950 border-slate-700 text-white focus:border-sky-500">
                       <option value="New">Nuevo</option>
                       <option value="InProgress">En Progreso</option>
                       <option value="OnHold">En Espera</option>
                       <option value="Resolved">Resuelto</option>
                       <option value="Closed">Cerrado</option>
                       <option value="Canceled">Cancelado</option>
                    </select>
                </div>
              }

              <div>
                 <label class="block text-slate-300 text-sm font-bold mb-2">Descripción Detallada *</label>
                 <textarea formControlName="description" rows="6" placeholder="Describa el problema o solicitud con el mayor detalle posible..."
                        class="textarea w-full bg-slate-950 border-slate-700 text-white focus:border-sky-500"></textarea>
              </div>
            </form>
          </div>

          <!-- History / Comments Block (Only if Edit) -->
          @if (isEdit && service.currentTicket(); as t) {
            <div class="card bg-slate-900 border-slate-800 p-6 shadow-lg">
               <div class="card-header border-slate-800 pb-4 mb-6 flex justify-between items-center">
                  <h3 class="text-slate-400 text-xs font-bold uppercase tracking-widest">Conversación y Auditoría</h3>
               </div>
               
               <!-- Comments List -->
               <div class="space-y-4 mb-8">
                  @for (comm of t.comments || []; track comm.id) {
                    <div class="flex gap-4">
                       <div class="w-8 h-8 rounded-full bg-slate-800 flex-shrink-0 flex items-center justify-center text-xs font-bold text-sky-400">
                          {{ comm.author_id.substring(0, 2).toUpperCase() }}
                       </div>
                       <div class="bg-slate-950 border border-slate-800 rounded-2xl p-4 flex-1">
                          <div class="flex justify-between items-center mb-2">
                             <span class="text-xs font-bold text-slate-500 italic">Agente / Usuario</span>
                             <span class="text-[10px] text-slate-600">{{ comm.created_at | date:'short' }}</span>
                          </div>
                          <p class="text-white text-sm whitespace-pre-wrap">{{ comm.content }}</p>
                       </div>
                    </div>
                  } @empty {
                    <div class="text-center py-10 text-slate-600 bg-slate-950/50 rounded-xl border border-dashed border-slate-800">
                       <i class="ki-filled ki-messages text-2xl mb-2 opacity-20"></i>
                       <p class="text-xs">No hay comentarios en este ticket aún.</p>
                    </div>
                  }
               </div>

               <!-- New Comment Form -->
               @if (!isLocked()) {
                 <div class="flex gap-4 items-start">
                    <div class="w-8 h-8 rounded-full bg-sky-500/20 flex-shrink-0 flex items-center justify-center">
                       <i class="ki-filled ki-pencil text-sky-500 text-xs"></i>
                    </div>
                    <div class="flex-1 space-y-3">
                       <textarea [(ngModel)]="newComment" rows="3" placeholder="Escriba una respuesta..."
                               class="textarea w-full bg-slate-950 border-slate-800 text-white text-sm focus:border-sky-500"></textarea>
                       <div class="flex justify-end">
                          <button (click)="postComment()" [disabled]="!newComment.trim()" class="btn btn-sm btn-primary">
                             Enviar Respuesta
                          </button>
                       </div>
                    </div>
                 </div>
               }
            </div>
          }
        </div>

        <!-- RIGHT COL: STATS / ACTIONS -->
        <div class="lg:col-span-4 space-y-6">
           
           <!-- Validation Block: Information -->
           <div class="card bg-slate-900 border-slate-800 p-6 shadow-lg">
              <h4 class="text-white font-bold mb-4">Metadatos del Ticket</h4>
              <div class="space-y-4">
                 <div class="flex justify-between items-center">
                    <span class="text-slate-500 text-xs uppercase font-bold">Solicitante</span>
                    @if (isEdit && service.currentTicket(); as t) {
                      <span class="text-slate-300 text-sm">{{ t.created_by.substring(0, 8) }}</span>
                    } @else {
                      <span class="text-slate-300 text-sm">Actual Usuario</span>
                    }
                 </div>
                 <div class="flex justify-between items-center">
                    <span class="text-slate-500 text-xs uppercase font-bold">Fecha Creación</span>
                    @if (isEdit && service.currentTicket(); as t) {
                      <span class="text-slate-300 text-sm">{{ t.created_at | date:'dd MMM yyyy' }}</span>
                    } @else {
                      <span class="text-slate-300 text-sm">-- / -- / --</span>
                    }
                 </div>
                 <div class="border-t border-slate-800 pt-4">
                    <div class="text-slate-500 text-xs uppercase font-bold mb-2">Asignado a:</div>
                    @if (isEdit && service.currentTicket(); as t) {
                       <div class="flex items-center gap-2 p-2 bg-slate-950 rounded-lg border border-slate-800">
                          <i class="ki-filled ki-user text-sky-500"></i>
                          <span class="text-sm text-white">{{ t.assigned_to_id ? 'Agente ' + t.assigned_to_id.substring(0, 4) : 'Pendiente Asignación' }}</span>
                       </div>
                    } @else {
                       <div class="text-slate-600 text-xs italic">Se asignará automáticamente al equipo de guardia.</div>
                    }
                 </div>
              </div>
           </div>

           <!-- Audit Log Snippet -->
           @if (isEdit && service.currentTicket(); as t) {
             <div class="card bg-slate-900 border-slate-800 p-6 shadow-lg">
                <h4 class="text-white font-bold mb-4">Historial de Auditoría</h4>
                <div class="space-y-4">
                   @for (h of t.history || []; track h.id) {
                     <div class="relative pl-6 border-l border-slate-800 py-1">
                        <div class="absolute -left-[5px] top-2 w-2 h-2 rounded-full bg-slate-700"></div>
                        <div class="text-[10px] text-slate-500 uppercase font-bold">{{ h.change_type }}</div>
                        <div class="text-xs text-white">
                           De <span class="text-slate-400">{{ h.old_value || 'N/A' }}</span> a <span class="text-sky-400">{{ h.new_value }}</span>
                        </div>
                        <div class="text-[10px] text-slate-600 mt-1">{{ h.created_at | date:'short' }}</div>
                     </div>
                   }
                </div>
             </div>
           }
        </div>

      </div>
    </div>
  `
})
export class TicketEditorComponent implements OnInit {
    service = inject(TicketService);
    auth = inject(AuthService);
    fb = inject(FormBuilder);
    router = inject(Router);
    route = inject(ActivatedRoute);

    isEdit = false;
    ticketId: string | null = null;
    newComment = '';

    form = this.fb.group({
        title: ['', [Validators.required, Validators.minLength(5)]],
        description: ['', [Validators.required, Validators.minLength(20)]],
        ticket_type: ['Support', Validators.required],
        priority: ['Medium', Validators.required],
        status: ['New']
    });

    isLocked = computed(() => {
        if (!this.isEdit) return false;
        const t = this.service.currentTicket();
        if (!t) return false;
        // Locked if Closed, Resolved or Canceled
        return ['Resolved', 'Closed', 'Canceled'].includes(t.status);
    });

    ngOnInit() {
        this.route.params.subscribe(params => {
            if (params['id']) {
                this.isEdit = true;
                this.ticketId = params['id'];
                this.loadTicket(params['id']);
            }
        });
    }

    async loadTicket(id: string) {
        await this.service.loadTicket(id);
        const t = this.service.currentTicket();
        if (t) {
            this.form.patchValue({
                title: t.title,
                description: t.description,
                ticket_type: t.ticket_type,
                priority: t.priority,
                status: t.status
            });
            if (this.isLocked()) {
                this.form.disable();
            }
        }
    }

    async save() {
        if (this.form.invalid) return;

        if (this.isEdit && this.ticketId) {
            const cmd: UpdateTicketCommand = {
                title: this.form.value.title!,
                description: this.form.value.description!,
                priority: this.form.value.priority as TicketPriority,
                status: this.form.value.status as TicketStatus
            };
            const success = await this.service.updateTicket(this.ticketId, cmd);
            if (success) this.goBack();
        } else {
            const cmd: CreateTicketCommand = {
                company_id: this.auth.currentContext()?.companyId!,
                title: this.form.value.title!,
                description: this.form.value.description!,
                ticket_type: this.form.value.ticket_type as TicketType,
                priority: this.form.value.priority as TicketPriority
            };
            const success = await this.service.createTicket(cmd);
            if (success) this.goBack();
        }
    }

    async postComment() {
        if (!this.newComment.trim() || !this.ticketId) return;
        const success = await this.service.addComment(this.ticketId, this.newComment);
        if (success) {
            this.newComment = '';
        }
    }

    goBack() {
        this.router.navigate(['/tickets']);
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
