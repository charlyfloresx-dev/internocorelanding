import { Component, Inject, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ToastService } from '../../../../core/services/toast.service';
import { TicketService } from '../../../../core/services/ticket.service';

@Component({
  selector: 'app-ticket-assign-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="bg-surface-card rounded-2xl shadow-2xl max-w-md w-full">
      <!-- Header -->
      <div class="px-6 py-5 border-b border-surface-border flex items-start justify-between">
        <div>
          <h2 class="text-lg font-black text-surface-text">Asignar Ticket</h2>
          <p class="text-xs text-surface-text-muted mt-1">{{ data.ticket?.reference_code }}</p>
        </div>
        <button (click)="onCancel()" class="p-1 hover:bg-surface-text/10 rounded-lg transition-colors">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <!-- Content -->
      <div class="px-6 py-6 space-y-4">
        <!-- Collaborator Selection -->
        <div>
          <label class="block text-xs font-black text-surface-text-muted uppercase tracking-widest mb-2">
            Seleccionar Colaborador
          </label>
          <select [(ngModel)]="selectedCollaboratorId"
                  class="w-full bg-surface-card border border-surface-border text-surface-text text-sm rounded-lg px-3 py-2 focus:ring-primary focus:border-primary">
            <option value="">— Elegir colaborador —</option>
            @for (collab of collaborators(); track collab.id) {
              <option [value]="collab.id">{{ collab.name }} ({{ collab.role_name }})</option>
            }
          </select>
        </div>

        <!-- Department Selection (Optional) -->
        <div>
          <label class="block text-xs font-black text-surface-text-muted uppercase tracking-widest mb-2">
            Departamento (Opcional)
          </label>
          <select [(ngModel)]="selectedDepartmentId"
                  class="w-full bg-surface-card border border-surface-border text-surface-text text-sm rounded-lg px-3 py-2 focus:ring-primary focus:border-primary">
            <option value="">— Sin departamento —</option>
            @for (dept of departments(); track dept.id) {
              <option [value]="dept.id">{{ dept.name }}</option>
            }
          </select>
        </div>

        <!-- Notes -->
        <div>
          <label class="block text-xs font-black text-surface-text-muted uppercase tracking-widest mb-2">
            Notas de Asignación
          </label>
          <textarea [(ngModel)]="notes" rows="3"
                    placeholder="Describe qué necesita este colaborador..."
                    class="w-full bg-surface-card border border-surface-border text-surface-text text-xs rounded-lg px-3 py-2 focus:ring-primary focus:border-primary">
          </textarea>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-surface-border flex gap-3 justify-end">
        <button (click)="onCancel()"
                class="px-4 py-2 rounded-lg text-xs font-black uppercase tracking-widest text-surface-text-muted hover:bg-surface-text/10 transition-colors">
          Cancelar
        </button>
        <button (click)="onAssign()"
                [disabled]="!selectedCollaboratorId || isSubmitting()"
                class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-xs font-black uppercase tracking-widest rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
          @if (isSubmitting()) {
            <mat-icon class="animate-spin text-sm">refresh</mat-icon>
          } @else {
            <mat-icon class="text-sm">assignment_ind</mat-icon>
          }
          Asignar
        </button>
      </div>
    </div>
  `,
  styles: []
})
export class TicketAssignModalComponent {
  @Inject(MAT_DIALOG_DATA) data: any;

  private dialogRef = inject(MatDialogRef<TicketAssignModalComponent>);
  private ticketSvc = inject(TicketService);
  private toastSvc = inject(ToastService);

  selectedCollaboratorId = signal<string>('');
  selectedDepartmentId = signal<string>('');
  notes = signal<string>('');
  isSubmitting = signal(false);

  // Placeholder: In real app, fetch from API
  collaborators = signal<any[]>([
    { id: 'user-1', name: 'Carlos Rodriguez', role_name: 'Supervisor' },
    { id: 'user-2', name: 'María García', role_name: 'Técnico' },
    { id: 'user-3', name: 'Juan López', role_name: 'Operador' }
  ]);

  departments = signal<any[]>([
    { id: 'dept-1', name: 'Mantenimiento' },
    { id: 'dept-2', name: 'Producción' },
    { id: 'dept-3', name: 'Calidad' }
  ]);

  onAssign(): void {
    if (!this.selectedCollaboratorId()) return;

    this.isSubmitting.set(true);
    const ticketId = this.data.ticket?.id;
    const assignmentData = {
      collaborator_id: this.selectedCollaboratorId(),
      assigned_department_id: this.selectedDepartmentId() || undefined
    };

    this.ticketSvc.assignTicket(ticketId, assignmentData).subscribe({
      next: () => {
        this.toastSvc.success('Asignación Exitosa', `Ticket asignado a ${this.getCollaboratorName()}`);
        this.dialogRef.close(true);
      },
      error: (err) => {
        this.toastSvc.error('Error', 'No se pudo asignar el ticket');
        console.error('Assignment error:', err);
        this.isSubmitting.set(false);
      }
    });
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }

  private getCollaboratorName(): string {
    const collab = this.collaborators().find(c => c.id === this.selectedCollaboratorId());
    return collab?.name || 'colaborador';
  }
}
