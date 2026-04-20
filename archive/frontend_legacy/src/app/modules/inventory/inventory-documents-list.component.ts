import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { InventoryService } from '@services/inventory.service';
import { TranslationService } from '@services/translation.service';
import { ConceptType, DocumentStatus } from '@models/api.types';

@Component({
  selector: 'app-inventory-documents-list',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule],
  template: `
    <div class="p-8 space-y-8 animate-fade-in-up">
      
      <!-- Header Section -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <div class="flex items-center gap-2 text-primary">
            <mat-icon class="text-xl">history_edu</mat-icon>
            <span class="text-[10px] font-black uppercase tracking-[0.3em]">Logística & Almacén</span>
          </div>
          <h1 class="text-3xl font-black text-white tracking-tighter uppercase italic">
            {{ ts.translate('inventory.movements_title', 'Movimientos de Inventario') }}
          </h1>
          <p class="text-surface-text-muted text-xs font-medium uppercase tracking-widest opacity-60">
            {{ ts.translate('inventory.movements_subtitle', 'Gestión de Entradas, Salidas y Transferencias') }}
          </p>
        </div>

        <div class="flex items-center gap-3">
          <button class="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-surface-text-muted hover:text-primary hover:border-primary/30 transition-all flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest">
            <mat-icon class="text-lg">filter_list</mat-icon>
            {{ ts.translate('common.filters', 'Filtros') }}
          </button>
          
          <a routerLink="/inventory/documents/new" 
             class="bg-primary hover:bg-primary/80 text-ic-dark font-black py-3 px-6 rounded-xl shadow-[0_0_20px_rgba(0,229,255,0.3)] transition-all flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] active:scale-95">
            <mat-icon class="text-lg">add_circle</mat-icon>
            {{ ts.translate('inventory.new_document', 'Nuevo Documento') }}
          </a>
        </div>
      </div>

      <!-- Quick Stats / Filters (Future Style) -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <button (click)="setFilter('all')" 
                [ngClass]="{'border-primary bg-primary/5': filter() === 'all'}"
                class="glass-card p-4 rounded-2xl border border-white/10 text-left transition-all hover:bg-white/5 group relative overflow-hidden">
          <div class="flex items-center justify-between mb-2">
            <mat-icon [class.text-primary]="filter() === 'all'" class="text-surface-text-muted group-hover:text-primary transition-colors">apps</mat-icon>
            <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest">Global</span>
          </div>
          <div class="text-2xl font-black text-white italic tracking-tighter">{{ service.documents().length }}</div>
          <div class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Todos los Registros</div>
          @if (filter() === 'all') {
            <div class="absolute bottom-0 left-0 w-full h-1 bg-primary animate-width-full"></div>
          }
        </button>

        <button (click)="setFilter('entry')" 
                [ngClass]="{'border-emerald-500 bg-emerald-500/5': filter() === 'entry'}"
                class="glass-card p-4 rounded-2xl border border-white/10 text-left transition-all hover:bg-white/5 group relative overflow-hidden">
          <div class="flex items-center justify-between mb-2">
            <mat-icon [class.text-emerald-500]="filter() === 'entry'" class="text-surface-text-muted group-hover:text-emerald-500 transition-colors">login</mat-icon>
            <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest">Entradas</span>
          </div>
          <div class="text-2xl font-black text-white italic tracking-tighter">
            {{ getCountByType(ConceptType.Entry) }}
          </div>
          <div class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Suministros & Devoluciones</div>
          @if (filter() === 'entry') {
            <div class="absolute bottom-0 left-0 w-full h-1 bg-emerald-500 animate-width-full"></div>
          }
        </button>

        <button (click)="setFilter('output')" 
                [ngClass]="{'border-red-500 bg-red-500/5': filter() === 'output'}"
                class="glass-card p-4 rounded-2xl border border-white/10 text-left transition-all hover:bg-white/5 group relative overflow-hidden">
          <div class="flex items-center justify-between mb-2">
            <mat-icon [class.text-red-500]="filter() === 'output'" class="text-surface-text-muted group-hover:text-red-500 transition-colors">logout</mat-icon>
            <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest">Salidas</span>
          </div>
          <div class="text-2xl font-black text-white italic tracking-tighter">
            {{ getCountByType(ConceptType.Output) }}
          </div>
          <div class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Ventas & Consumos</div>
          @if (filter() === 'output') {
            <div class="absolute bottom-0 left-0 w-full h-1 bg-red-500 animate-width-full"></div>
          }
        </button>

        <div class="glass-card p-4 rounded-2xl border border-white/10 bg-primary/5 flex flex-col justify-center">
          <div class="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-1">Valor Total</div>
          <div class="text-2xl font-black text-white italic tracking-tighter">{{ getTotalValue() | currency }}</div>
          <div class="w-full bg-white/10 h-1 rounded-full mt-2 overflow-hidden">
             <div class="bg-primary h-full w-2/3 shadow-[0_0_10px_rgba(0,229,255,0.8)]"></div>
          </div>
        </div>
      </div>

      <!-- Table Section (Triple Identity Concept) -->
      <div class="glass-card rounded-[2rem] border border-white/10 overflow-hidden shadow-2xl">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-white/5 border-b border-white/10">
                <th class="px-6 py-4 text-[10px] font-black text-surface-text-muted uppercase tracking-widest">Identidad Triple</th>
                <th class="px-6 py-4 text-[10px] font-black text-surface-text-muted uppercase tracking-widest text-center">Tipo</th>
                <th class="px-6 py-4 text-[10px] font-black text-surface-text-muted uppercase tracking-widest">Almacén</th>
                <th class="px-6 py-4 text-[10px] font-black text-surface-text-muted uppercase tracking-widest text-right">Monto</th>
                <th class="px-6 py-4 text-[10px] font-black text-surface-text-muted uppercase tracking-widest text-center">Estado Ledger</th>
                <th class="px-6 py-4 text-[10px] font-black text-surface-text-muted uppercase tracking-widest text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/5 font-sans">
              @for (doc of filteredDocuments(); track doc.id) {
                <tr class="hover:bg-white/10 transition-colors group">
                  <td class="px-6 py-5">
                    <div class="flex flex-col">
                      <span class="text-sm font-black text-white tracking-tight">{{ doc.folio || 'FOLIO-PENDING' }}</span>
                      <div class="flex items-center gap-2 mt-1">
                        <span class="text-[9px] text-surface-text-muted font-bold uppercase tracking-widest opacity-60">ID: {{ doc.id.substring(0,8) }}</span>
                        <div class="w-1 h-1 bg-white/20 rounded-full"></div>
                        <span class="text-[9px] text-primary font-black uppercase tracking-widest">{{ doc.conceptName }}</span>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-5">
                    <div class="flex items-center justify-center">
                      <div [class]="doc.conceptType === ConceptType.Entry ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'" 
                           class="w-8 h-8 rounded-lg flex items-center justify-center border border-white/5">
                        <mat-icon class="text-lg">{{ doc.conceptType === ConceptType.Entry ? 'south_west' : 'north_east' }}</mat-icon>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-5">
                    <div class="flex flex-col">
                      <span class="text-xs font-bold text-surface-text tracking-tight uppercase">{{ doc.warehouseId || 'Principal' }}</span>
                      <span class="text-[9px] text-surface-text-muted font-bold uppercase tracking-widest">{{ doc.deliveryDate | date:'shortTime' }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-5 text-right font-mono text-sm font-black" [class.text-emerald-400]="doc.conceptType === ConceptType.Entry" [class.text-red-400]="doc.conceptType === ConceptType.Output">
                    {{ doc.conceptType === ConceptType.Entry ? '+' : '-' }}{{ doc.total_amount | currency }}
                  </td>
                  <td class="px-6 py-5">
                    <div class="flex justify-center">
                      <span [class]="getStatusClass(doc.status)" 
                            class="px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest border border-white/10 shadow-lg">
                        {{ ts.translate('status.' + doc.status.toLowerCase(), doc.status) }}
                      </span>
                      @if (doc.folio.startsWith('ICT-IN') || (doc as any).is_mirror) {
                        <span class="px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 text-[8px] font-black uppercase tracking-widest border border-sky-500/30 ml-2 animate-pulse">
                          Espejo ICT
                        </span>
                      }
                    </div>
                  </td>
                  <td class="px-6 py-5 text-right">
                    <div class="flex items-center justify-end gap-2">
                       @if (doc.type === 'ICT_TRANSFER' || doc.type === 'Traspaso' || doc.conceptType === 'ICT_TRANSFER') {
                         <button [disabled]="isSelfTransfer(doc)"
                                 [title]="isSelfTransfer(doc) ? 'Restricción Anti-Fraude' : 'Recibir Traspaso'"
                                 [class.opacity-30]="isSelfTransfer(doc)"
                                 class="p-2 text-surface-text-muted hover:text-primary hover:bg-primary/10 rounded-lg transition-all group/btn disabled:cursor-not-allowed">
                           <mat-icon class="text-lg">call_received</mat-icon>
                         </button>
                       }
                       <button [routerLink]="['/inventory/documents', doc.id]" 
                               class="p-2 text-surface-text-muted hover:text-primary hover:bg-primary/10 rounded-lg transition-all group/btn">
                         <mat-icon class="text-lg">visibility</mat-icon>
                       </button>
                       <button class="p-2 text-surface-text-muted hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-all">
                         <mat-icon class="text-lg">delete_outline</mat-icon>
                       </button>
                    </div>
                  </td>
                </tr>
              }
              @if (filteredDocuments().length === 0) {
                <tr>
                  <td colspan="6" class="px-6 py-20 text-center">
                    <div class="flex flex-col items-center opacity-30">
                      <mat-icon class="text-6xl mb-4">inventory_2</mat-icon>
                      <h3 class="text-xl font-black uppercase tracking-tighter italic">{{ ts.translate('common.no_data', 'No hay registros') }}</h3>
                      <p class="text-xs font-bold uppercase tracking-widest mt-2 group-hover:text-primary transition-colors">Inicie un nuevo documento para ver datos industriales</p>
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        
        <!-- Pagination (Industrial Footer) -->
        <div class="px-6 py-4 bg-white/5 border-t border-white/10 flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-surface-text-muted">
          <div class="flex items-center gap-4">
             <span>{{ ts.translate('common.showing', 'Mostrando') }} {{ filteredDocuments().length }} {{ ts.translate('common.of', 'de') }} {{ service.documents().length }}</span>
             <div class="w-32 bg-white/10 h-1 rounded-full overflow-hidden">
                <div [style.width.%]="(filteredDocuments().length / (service.documents().length || 1)) * 100" class="bg-primary h-full transition-all duration-500"></div>
             </div>
          </div>
          <div class="flex items-center gap-2">
            <button class="p-2 border border-white/10 rounded-lg hover:bg-white/5 disabled:opacity-30 transition-all font-black">
               <mat-icon class="text-sm">chevron_left</mat-icon>
            </button>
            <button class="p-2 border border-white/10 rounded-lg bg-primary/10 text-primary font-black">1</button>
            <button class="p-2 border border-white/10 rounded-lg hover:bg-white/5 transition-all font-black font-sans">2</button>
            <button class="p-2 border border-white/10 rounded-lg hover:bg-white/5 transition-all font-black">
               <mat-icon class="text-sm">chevron_right</mat-icon>
            </button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class InventoryDocumentsListComponent implements OnInit {
  public service = inject(InventoryService);
  public ts = inject(TranslationService);

  public filter = signal<'all' | 'entry' | 'output'>('all');
  public ConceptType = ConceptType;

  ngOnInit() {
    this.service.loadDocuments();
  }

  filteredDocuments = computed(() => {
    const docs = this.service.documents();
    const f = this.filter();
    if (f === 'all') return docs;
    if (f === 'entry') return docs.filter(d => d.conceptType === ConceptType.Entry);
    return docs.filter(d => d.conceptType === ConceptType.Output);
  });

  setFilter(f: 'all' | 'entry' | 'output') {
    this.filter.set(f);
  }

  getCountByType(type: ConceptType): number {
    return this.service.documents().filter(d => d.conceptType === type).length;
  }

  getTotalValue(): number {
    return this.service.documents().reduce((acc, doc) => acc + (doc.total_amount || 0), 0);
  }

  getStatusClass(status: string): string {
    switch (status.toUpperCase()) {
      case 'CONFIRMED': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'DRAFT': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'CANCELLED': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-white/5 text-surface-text-muted border-white/10';
    }
  }

  get currentUserId(): string | null {
    try {
      const session = JSON.parse(localStorage.getItem('auth_session') || '{}');
      return session?.user?.id || session?.user_id || null;
    } catch { return null; }
  }

  isSelfTransfer(doc: any): boolean {
    const uid = this.currentUserId;
    return (doc.type === 'ICT_TRANSFER' || doc.type === 'Traspaso' || doc.conceptType === 'ICT_TRANSFER') && doc.created_by === uid;
  }
}
