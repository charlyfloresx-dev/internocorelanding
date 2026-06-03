import { Component, Inject, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { TicketService } from '../../../../core/services/ticket.service';
import { ToastService } from '../../../../core/services/toast.service';

interface NewTicketInput {
  stationId: string;
  stationCode?: string;
}

interface Collaborator {
  id: string;
  name: string;
}

@Component({
  selector: 'app-new-ticket-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="w-full max-w-2xl">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-surface-border flex items-center justify-between">
        <div class="flex items-center gap-2">
          <mat-icon>add_circle</mat-icon>
          <h2 class="text-sm font-black text-surface-text uppercase tracking-widest">Nuevo Ticket</h2>
        </div>
        <button (click)="dialogRef.close()"
                class="p-1 hover:bg-surface-text/10 rounded-lg transition-colors">
          <mat-icon class="text-sm">close</mat-icon>
        </button>
      </div>

      <!-- Form -->
      <div class="px-6 py-6 space-y-5">

        <!-- Estación (read-only) -->
        <div>
          <label class="text-[10px] font-black text-surface-text uppercase tracking-widest block mb-2">
            Estación
          </label>
          <div class="px-3 py-2 bg-surface-text/5 border border-surface-border rounded-lg text-xs text-surface-text">
            {{ stationCode }}
          </div>
        </div>

        <!-- Título -->
        <div>
          <label for="title" class="text-[10px] font-black text-surface-text uppercase tracking-widest block mb-2">
            Título <span class="text-red-400">*</span>
          </label>
          <input type="text"
                 id="title"
                 [(ngModel)]="form.title"
                 placeholder="Ej: Máquina CELDA-58D con alerta crítica"
                 maxlength="100"
                 class="w-full px-3 py-2 bg-surface-card border border-surface-border text-surface-text text-xs rounded-lg
                        focus:ring-primary focus:border-primary" />
          <p class="text-[9px] text-surface-text-muted mt-1">
            {{ form.title.length }}/100 caracteres
          </p>
        </div>

        <!-- Descripción -->
        <div>
          <label for="description" class="text-[10px] font-black text-surface-text uppercase tracking-widest block mb-2">
            Descripción <span class="text-red-400">*</span>
          </label>
          <textarea id="description"
                    [(ngModel)]="form.description"
                    placeholder="Describe el problema con detalle..."
                    rows="4"
                    class="w-full px-3 py-2 bg-surface-card border border-surface-border text-surface-text text-xs rounded-lg
                          focus:ring-primary focus:border-primary resize-none"></textarea>
          <p class="text-[9px] text-surface-text-muted mt-1">
            {{ form.description.length }}/500 caracteres (mín. 10)
          </p>
        </div>

        <!-- Prioridad -->
        <div>
          <label for="priority" class="text-[10px] font-black text-surface-text uppercase tracking-widest block mb-2">
            Prioridad
          </label>
          <select [(ngModel)]="form.priority"
                  id="priority"
                  class="w-full px-3 py-2 bg-surface-card border border-surface-border text-surface-text text-xs rounded-lg
                        focus:ring-primary focus:border-primary">
            <option value="BAJA">Baja</option>
            <option value="MEDIA" selected>Media</option>
            <option value="ALTA">Alta</option>
            <option value="CRÍTICA">Crítica</option>
          </select>
        </div>

        <!-- Asignado a (opcional) -->
        <div>
          <label for="assigned" class="text-[10px] font-black text-surface-text uppercase tracking-widest block mb-2">
            Asignar a (opcional)
          </label>
          <select [(ngModel)]="form.assignedToId"
                  id="assigned"
                  class="w-full px-3 py-2 bg-surface-card border border-surface-border text-surface-text text-xs rounded-lg
                        focus:ring-primary focus:border-primary">
            <option [value]="null">— Sin asignar —</option>
            <option *ngFor="let collab of mockCollaborators"
                    [value]="collab.id">
              {{ collab.name }}
            </option>
          </select>
        </div>

      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-surface-border flex items-center justify-end gap-3">
        <button (click)="dialogRef.close()"
                class="px-4 py-2 text-[10px] font-black uppercase tracking-widest
                      text-surface-text hover:bg-surface-text/5 rounded-lg transition-colors">
          Cancelar
        </button>
        <button (click)="onCreate()"
                [disabled]="!isFormValid() || isSubmitting()"
                class="px-4 py-2 text-[10px] font-black uppercase tracking-widest
                      bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors
                      disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
          @if (isSubmitting()) {
            <mat-icon class="animate-spin text-sm">refresh</mat-icon>
          } @else {
            <mat-icon class="text-sm">add</mat-icon>
          }
          Crear Ticket
        </button>
      </div>

    </div>
  `,
  styles: [`
    :host {
      display: block;
      background: var(--surface-card);
      color: var(--surface-text);
    }
  `]
})
export class NewTicketDialogComponent {
  readonly dialogRef = inject(MatDialogRef<NewTicketDialogComponent>);
  private ticketSvc = inject(TicketService);
  private toastSvc = inject(ToastService);
  @Inject(MAT_DIALOG_DATA) readonly data: NewTicketInput = { stationId: '', stationCode: '' };

  stationCode = '';
  isSubmitting = signal(false);

  form = {
    title: '',
    description: '',
    priority: 'MEDIA',
    assignedToId: null as string | null
  };

  mockCollaborators: Collaborator[] = [
    { id: 'usr-001', name: 'Carlos Montoya (Supervisor)' },
    { id: 'usr-002', name: 'Ana García (Técnico MES)' },
    { id: 'usr-003', name: 'José López (Mantenimiento)' },
    { id: 'usr-004', name: 'María Ruiz (Calidad)' }
  ];

  constructor() {
    this.stationCode = this.data?.stationCode || this.data?.stationId || '—';
  }

  isFormValid(): boolean {
    return (
      this.form.title.length >= 5 &&
      this.form.title.length <= 100 &&
      this.form.description.length >= 10 &&
      this.form.description.length <= 500 &&
      ['BAJA', 'MEDIA', 'ALTA', 'CRÍTICA'].includes(this.form.priority)
    );
  }

  async onCreate(): Promise<void> {
    if (!this.isFormValid() || !this.data?.stationId) return;

    this.isSubmitting.set(true);
    try {
      const payload: any = {
        title: this.form.title,
        description: this.form.description,
        priority: this.form.priority,
        ticket_type: 'SUPPORT',
        station_id: this.data.stationId,
        company_id: 'TODO: from JWT', // TODO: Inject auth context
        source_service: 'MANUAL'
      };

      // Add assignment if selected
      if (this.form.assignedToId) {
        payload.assigned_to_id = this.form.assignedToId;
      }

      const result = await new Promise((resolve, reject) => {
        this.ticketSvc.createTicket(payload).subscribe({
          next: resolve,
          error: reject
        });
      });

      this.toastSvc.success('✅ Ticket Creado', `Ticket #${(result as any)?.data?.id} creado exitosamente`);
      this.dialogRef.close(result);
    } catch (err) {
      this.toastSvc.error('❌ Error', 'No se pudo crear el ticket. Intenta de nuevo.');
      console.error('Create ticket error:', err);
    } finally {
      this.isSubmitting.set(false);
    }
  }
}
