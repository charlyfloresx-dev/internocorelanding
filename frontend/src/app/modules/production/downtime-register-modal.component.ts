import { Component, inject, signal, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ProductionDataService } from '@services/production-data.service';
import { CreateDowntimeCommand } from '@models/api.types';

@Component({
  selector: 'app-downtime-register-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in">
      <div class="w-full max-w-md bg-slate-900 rounded-2xl border border-slate-700 shadow-2xl overflow-hidden animate-fade-in-up mx-4">
        
        <!-- Header -->
        <div class="p-6 bg-slate-950 border-b border-slate-800 flex justify-between items-center">
          <h3 class="text-xl font-bold text-white flex items-center gap-2">
            <i class="fa-solid fa-triangle-exclamation text-red-500"></i> Registrar Paro
          </h3>
          <button (click)="close.emit()" class="text-slate-500 hover:text-white transition-colors">
            <i class="fa-solid fa-times text-xl"></i>
          </button>
        </div>

        <!-- Body -->
        <div class="p-6 space-y-4">
          
          <!-- Issue Selector -->
          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Motivo del Paro</label>
            <select [(ngModel)]="data.issueId" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-red-500 outline-none">
              <option value="" disabled selected>Seleccione una causa...</option>
              @for (issue of service.issuesCatalog(); track issue.id) {
                <option [value]="issue.id">{{ issue.name }} ({{ issue.category }})</option>
              }
            </select>
          </div>

          <!-- Description -->
          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Observaciones</label>
            <textarea [(ngModel)]="data.description" rows="3" 
                      class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-red-500 outline-none resize-none"
                      placeholder="Detalles adicionales..."></textarea>
          </div>

          <!-- Ticket Number (Optional) -->
          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Ticket Mantenimiento (Opcional)</label>
            <input type="number" [(ngModel)]="data.requestNumber" 
                   class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-red-500 outline-none"
                   placeholder="Ej. 1024">
          </div>

        </div>

        <!-- Footer -->
        <div class="p-6 bg-slate-950 border-t border-slate-800 flex justify-end gap-3">
          <button (click)="close.emit()" class="px-4 py-2 rounded-lg text-slate-400 hover:text-white font-medium transition-colors">
            Cancelar
          </button>
          <button (click)="submit()" [disabled]="!isValid() || isSubmitting()"
                  class="px-6 py-2 bg-red-600 hover:bg-red-500 text-white font-bold rounded-lg shadow-lg shadow-red-900/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
            @if (isSubmitting()) { <i class="fa-solid fa-circle-notch fa-spin"></i> }
            Registrar Evento
          </button>
        </div>

      </div>
    </div>
  `
})
export class DowntimeRegisterModalComponent {
  public service = inject(ProductionDataService);
  
  close = output<void>();
  saved = output<void>();

  data: CreateDowntimeCommand = {
    lineId: 'ENS-01', // Default for MVP
    issueId: '',
    description: ''
  };

  isSubmitting = signal(false);

  isValid(): boolean {
    return !!this.data.issueId && this.data.issueId !== '';
  }

  submit() {
    if (!this.isValid()) return;
    this.isSubmitting.set(true);
    
    // Aquí se llamaría al método real del servicio
    // Por ahora simulamos el cierre
    setTimeout(() => {
      this.isSubmitting.set(false);
      this.saved.emit();
      this.close.emit();
    }, 500);
  }
}