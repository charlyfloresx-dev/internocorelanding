import {Component, signal, computed} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatIconModule} from '@angular/material/icon';

@Component({
  selector: 'app-document-list',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="space-y-6 animate-fade-in-up">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-surface-text">Documentos de Inventario</h1>
          <p class="text-surface-text-muted">Gestión de movimientos y trazabilidad del ledger</p>
        </div>
        <button class="btn-primary">
          <mat-icon>add</mat-icon>
          Crear Documento
        </button>
      </div>

      <div class="industrial-card">
        <!-- Filters -->
        <div class="p-6 border-b border-surface-border flex flex-wrap gap-4 items-center justify-between">
          <div class="flex gap-2">
            <button 
              (click)="filter.set('ALL')"
              [class.bg-primary]="filter() === 'ALL'"
              [class.text-white]="filter() === 'ALL'"
              class="px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-widest border border-surface-border hover:bg-surface-text/5 transition-all"
            >
              Todos
            </button>
            <button 
              (click)="filter.set('ENTRADA')"
              [class.bg-primary]="filter() === 'ENTRADA'"
              [class.text-white]="filter() === 'ENTRADA'"
              class="px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-widest border border-surface-border hover:bg-surface-text/5 transition-all"
            >
              Entradas
            </button>
            <button 
              (click)="filter.set('SALIDA')"
              [class.bg-primary]="filter() === 'SALIDA'"
              [class.text-white]="filter() === 'SALIDA'"
              class="px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-widest border border-surface-border hover:bg-surface-text/5 transition-all"
            >
              Salidas
            </button>
          </div>

          <div class="relative">
            <mat-icon class="absolute left-3 top-1/2 -translate-y-1/2 text-surface-text-muted text-sm">search</mat-icon>
            <input 
              type="text" 
              placeholder="Buscar por folio..." 
              class="bg-surface-bg border border-surface-border rounded-lg pl-10 pr-4 py-2 text-sm text-surface-text focus:border-primary outline-none w-64"
            >
          </div>
        </div>

        <!-- Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-surface-text/5 text-surface-text-muted uppercase text-[10px] font-bold tracking-widest">
              <tr>
                <th class="px-6 py-4">Identidad Triple</th>
                <th class="px-6 py-4">Tipo</th>
                <th class="px-6 py-4">Almacén Origen/Destino</th>
                <th class="px-6 py-4">Fecha Operación</th>
                <th class="px-6 py-4">Estado Ledger</th>
                <th class="px-6 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-border">
              @for (doc of filteredDocuments(); track doc.id) {
                <tr class="hover:bg-surface-text/5 transition-colors group">
                  <td class="px-6 py-4">
                    <div class="flex flex-col">
                      <span class="text-surface-text font-bold tracking-tight">{{ doc.folio }}</span>
                      <div class="flex items-center gap-2 mt-1">
                        <span class="text-[10px] text-surface-text-muted font-mono">SEQ: {{ doc.sequence_number }}</span>
                        <span class="text-[10px] text-surface-text-muted font-mono opacity-60">UUID: {{ doc.id.substring(0,8) }}...</span>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                      <mat-icon class="text-xs h-4 w-4" [class.text-emerald-400]="doc.type === 'ENTRADA'" [class.text-amber-400]="doc.type === 'SALIDA'">
                        {{ doc.type === 'ENTRADA' ? 'south_west' : 'north_east' }}
                      </mat-icon>
                      <span class="text-surface-text-muted">{{ doc.type }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4 text-surface-text-muted">{{ doc.warehouse }}</td>
                  <td class="px-6 py-4 text-surface-text-muted">{{ doc.date }}</td>
                  <td class="px-6 py-4">
                    <span class="status-badge" [ngClass]="'status-' + doc.status.toLowerCase()">
                      {{ doc.status }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-right">
                    <button class="p-2 text-surface-text-muted hover:text-surface-text hover:bg-surface-text/5 rounded-lg transition-all">
                      <mat-icon>visibility</mat-icon>
                    </button>
                    @if (doc.status === 'DRAFT') {
                      <button class="p-2 text-primary hover:bg-primary/10 rounded-lg transition-all ml-2">
                        <mat-icon>edit</mat-icon>
                      </button>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        
        <div class="p-6 border-t border-surface-border flex items-center justify-between text-xs text-surface-text-muted">
          <span>Mostrando {{ filteredDocuments().length }} de {{ documents().length }} registros</span>
          <div class="flex gap-2">
            <button class="p-2 border border-surface-border rounded hover:bg-surface-text/5 disabled:opacity-30" disabled>Anterior</button>
            <button class="p-2 border border-surface-border rounded hover:bg-surface-text/5">Siguiente</button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class DocumentListComponent {
  filter = signal<'ALL' | 'ENTRADA' | 'SALIDA'>('ALL');
  
  documents = signal([
    { id: 'uuid-789-abc', folio: 'ENT-2026-0045', sequence_number: 1045, type: 'ENTRADA', warehouse: 'Materia Prima A', date: '06/03/2026 10:30', status: 'CONFIRMED' },
    { id: 'uuid-790-def', folio: 'SAL-2026-0012', sequence_number: 1046, type: 'SALIDA', warehouse: 'Producto Terminado', date: '06/03/2026 11:15', status: 'DRAFT' },
    { id: 'uuid-791-ghi', folio: 'TRA-2026-0008', sequence_number: 1047, type: 'TRASPASO', warehouse: 'Almacén Central', date: '05/03/2026 09:00', status: 'CANCELLED' },
    { id: 'uuid-792-jkl', folio: 'ENT-2026-0044', sequence_number: 1044, type: 'ENTRADA', warehouse: 'Materia Prima B', date: '05/03/2026 16:45', status: 'CONFIRMED' },
    { id: 'uuid-793-mno', folio: 'SAL-2026-0011', sequence_number: 1043, type: 'SALIDA', warehouse: 'Producto Terminado', date: '05/03/2026 14:20', status: 'CONFIRMED' },
  ]);

  filteredDocuments = computed(() => {
    const f = this.filter();
    if (f === 'ALL') return this.documents();
    return this.documents().filter(d => d.type === f);
  });
}
