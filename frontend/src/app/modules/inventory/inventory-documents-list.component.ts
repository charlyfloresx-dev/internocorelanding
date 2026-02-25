
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { InventoryService } from '@services/inventory.service';
import { ConceptType, DocumentStatus } from '@models/api.types';

@Component({
  selector: 'app-inventory-documents-list',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
           <h1 class="text-2xl font-bold text-white tracking-tight">Movimientos de Inventario</h1>
           <p class="text-slate-400 text-sm">Historial de entradas, salidas y ajustes</p>
        </div>
        <a routerLink="/inventory/documents/new" class="bg-sky-600 hover:bg-sky-500 text-white font-bold py-2 px-4 rounded-lg shadow-lg shadow-sky-900/20 transition-all flex items-center gap-2">
           <i class="fa-solid fa-file-invoice"></i> Nuevo Documento
        </a>
      </div>

      <!-- Filters -->
      <div class="flex gap-2 border-b border-slate-700 pb-1">
        <button 
          (click)="setFilter('all')" 
          class="px-4 py-2 text-sm font-bold border-b-2 transition-colors"
          [ngClass]="{
            'text-sky-400 border-sky-400': filter() === 'all',
            'text-slate-400 hover:text-white border-transparent': filter() !== 'all'
          }">
          Todos
        </button>
        <button 
          (click)="setFilter('entry')" 
          class="px-4 py-2 text-sm font-bold border-b-2 transition-colors"
          [ngClass]="{
            'text-sky-400 border-sky-400': filter() === 'entry',
            'text-slate-400 hover:text-white border-transparent': filter() !== 'entry'
          }">
          Entradas
        </button>
        <button 
          (click)="setFilter('output')" 
          class="px-4 py-2 text-sm font-bold border-b-2 transition-colors"
          [ngClass]="{
            'text-sky-400 border-sky-400': filter() === 'output',
            'text-slate-400 hover:text-white border-transparent': filter() !== 'output'
          }">
          Salidas
        </button>
      </div>

      <!-- Documents Table -->
      <div class="bg-slate-800 rounded-xl border border-slate-700 shadow-xl overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-slate-300">
            <thead class="bg-slate-900/50 text-slate-400 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-700">
              <tr>
                <th class="px-6 py-4">Folio (Comercial)</th>
                <th class="px-6 py-4">Secuencia (Auditoría)</th>
                <th class="px-6 py-4">Concepto / Fecha</th>
                <th class="px-6 py-4">Almacén</th>
                <th class="px-6 py-4">Socio Comercial</th>
                <th class="px-6 py-4 text-right">Total</th>
                <th class="px-6 py-4 text-center">Estatus</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700">
              @if (service.loading()) {
                <tr><td colspan="6" class="px-6 py-8 text-center text-slate-500"><i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Cargando documentos...</td></tr>
              } @else if (filteredDocuments().length === 0) {
                 <tr><td colspan="6" class="px-6 py-8 text-center text-slate-500">No hay movimientos que coincidan con el filtro actual.</td></tr>
              }

              @for (doc of filteredDocuments(); track doc.id) {
                <tr [routerLink]="['/inventory/documents', doc.id]" class="hover:bg-slate-700/50 transition-colors group cursor-pointer">
                  <td class="px-6 py-4">
                    <span class="font-bold text-white text-base">{{ doc.folio }}</span>
                  </td>
                  <td class="px-6 py-4 text-slate-400 font-mono text-xs">
                    #{{ doc.sequence_number | number:'3.0' }}
                  </td>
                  <td class="px-6 py-4">
                     <div class="flex items-center gap-2">
                       <div [class]="getConceptIconClass(doc.conceptType)" class="w-6 h-6 rounded flex items-center justify-center text-xs">
                          <i [class]="getConceptIcon(doc.conceptType)"></i>
                       </div>
                       <div class="flex flex-col">
                         <span class="text-white font-medium">{{ doc.conceptName }}</span>
                         <span class="text-[10px] text-slate-500">{{ doc.deliveryDate | date:'short' }}</span>
                       </div>
                     </div>
                     @if (doc.reference) {
                       <div class="text-[10px] text-slate-500 mt-1">Ref: {{ doc.reference }}</div>
                     }
                  </td>
                  <td class="px-6 py-4 text-slate-300">
                    {{ doc.warehouseName }}
                  </td>
                  <td class="px-6 py-4 text-slate-400 italic">
                    {{ doc.partnershipName || '-' }}
                  </td>
                  <td class="px-6 py-4 font-mono text-white text-right">
                    {{ doc.total_amount | currency }}
                  </td>
                  <td class="px-6 py-4 text-center">
                    <span [class]="getStatusClass(doc.status)">{{ doc.status }}</span>
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
export class InventoryDocumentsListComponent implements OnInit {
  public service = inject(InventoryService);
  ConceptType = ConceptType;

  filter = signal<'all' | 'entry' | 'output'>('all');

  filteredDocuments = computed(() => {
    const documents = this.service.documents();
    const currentFilter = this.filter();

    if (currentFilter === 'all') {
      return documents;
    }

    // Use ConceptType.Entry for 'entry' and ConceptType.Output for 'output'
    const conceptTypeFilter = currentFilter === 'entry' ? ConceptType.Entry : ConceptType.Output;
    return documents.filter(d => d.conceptType === conceptTypeFilter);
  });

  ngOnInit() {
    this.service.loadDocuments();
  }

  setFilter(filter: 'all' | 'entry' | 'output'): void {
    this.filter.set(filter);
  }

  getConceptIcon(type: ConceptType | undefined): string {
    return type === ConceptType.Entry ? 'fa-solid fa-arrow-right' : 'fa-solid fa-arrow-left';
  }

  getConceptIconClass(type: ConceptType | undefined): string {
    return type === ConceptType.Entry
      ? 'bg-green-500/10 text-green-500 border border-green-500/20'
      : 'bg-red-500/10 text-red-500 border border-red-500/20';
  }

  getStatusClass(status: DocumentStatus): string {
    switch (status) {
      case DocumentStatus.Confirmed: return 'text-[10px] font-bold uppercase bg-green-500/10 text-green-500 px-2 py-1 rounded border border-green-500/20';
      case DocumentStatus.Draft: return 'text-[10px] font-bold uppercase bg-slate-500/10 text-slate-400 px-2 py-1 rounded border border-slate-500/20';
      case DocumentStatus.Canceled: return 'text-[10px] font-bold uppercase bg-red-500/10 text-red-500 px-2 py-1 rounded border border-red-500/20';
      default: return '';
    }
  }
}
