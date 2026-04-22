import { Component, OnInit, inject, signal, effect, computed, untracked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink, Router } from '@angular/router';
import { TranslationService } from '../../core/services/translation.service';
import { InventoryService } from '../../core/services/inventory.service';
import { AuthService } from '../../core/services/auth.service';
import { FormsModule } from '@angular/forms';
import { CurrencyFormatPipe } from '../../shared/pipes/currency-format.pipe';

interface InventoryDocument {
  id: string;
  type: 'ENTRY' | 'EXIT' | 'TRANSFER' | 'ADJUSTMENT';
  status: 'DRAFT' | 'PROCESSED' | 'CANCELLED';
  origin: string;
  destination: string;
  items_count: number;
  total_value: number;
  created_at: string;
  created_by: string;
  reference?: string;
}

@Component({
  selector: 'app-inventory-documents',
  standalone: true,
  imports: [CommonModule, MatIconModule, RouterLink, FormsModule, CurrencyFormatPipe],
  template: `
    <div class="space-y-8 animate-fade-in pb-24">
      <!-- Header Section -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-primary/10 border border-primary/30 rounded-xl flex items-center justify-center text-primary shadow-sm transition-all hover:bg-primary/20">
            <mat-icon class="text-2xl">history</mat-icon>
          </div>
          <div>
            <div class="flex flex-wrap items-center gap-2 mb-0.5">
              <h1 class="text-3xl md:text-3xl font-black text-slate-900 dark:text-white tracking-tighter uppercase italic">
                {{ t('inventory.documents.title', 'Registro de Movimientos') }}
              </h1>
              <span class="text-primary hidden md:inline-block text-3xl font-black italic">/</span>
              <!-- Warehouse Selector styled like Title -->
              <div class="flex items-center relative group">
                <select 
                  [value]="selectedWarehouseId()"
                  (change)="onWarehouseChange($event)"
                  class="bg-transparent border-none text-2xl md:text-3xl font-black tracking-tighter uppercase italic outline-none focus:ring-0 cursor-pointer appearance-none pl-1 pr-8 truncate max-w-[300px] md:max-w-none transition-colors
                         text-slate-900 hover:text-primary
                         dark:text-primary dark:hover:text-white dark:drop-shadow-[0_0_8px_rgba(0,229,255,0.4)]"
                >
                  <option [value]="null" class="text-base font-bold text-gray-800 bg-white dark:text-gray-200 dark:bg-[#0A0F1A] not-italic tracking-normal">TODOS LOS ALMACENES</option>
                  @for (wh of warehouses(); track wh.id) {
                    <option [value]="wh.id" class="text-base font-bold text-gray-800 bg-white dark:text-gray-200 dark:bg-[#0A0F1A] not-italic tracking-normal">{{ wh.name }}</option>
                  }
                </select>
                <mat-icon class="text-slate-400 dark:text-primary absolute right-0 pointer-events-none group-hover:text-primary transition-colors">arrow_drop_down</mat-icon>
              </div>
            </div>
            <p class="text-slate-500 dark:text-slate-400 font-mono text-[9px] tracking-[0.2em] uppercase">
              {{ t('inventory.documents.subtitle', 'Trazabilidad completa de entradas, salidas y transferencias') }}
            </p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <a 
            routerLink="new"
            class="bg-primary text-white dark:text-slate-950 px-8 h-12 flex items-center gap-3 rounded-xl font-black text-[11px] uppercase tracking-[0.3em] transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-primary/20"
          >
            <mat-icon class="text-lg">add_circle</mat-icon>
            Nuevo Movimiento
          </a>
        </div>
      </div>

       <!-- Quick Stats Grid -->
       <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
         <div class="industrial-card p-6 group hover:border-emerald-500/30 transition-all">
           <div class="flex items-center justify-between mb-4">
             <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Entradas (24h)</span>
             <div class="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500">
               <mat-icon class="text-sm">arrow_downward</mat-icon>
             </div>
           </div>
           <div class="flex items-baseline gap-2">
             <span class="text-3xl font-black text-surface-text tabular-nums">{{ summary().entries_24h }}</span>
             <span class="text-[10px] font-bold text-emerald-500 uppercase">Docs</span>
           </div>
           <div class="mt-4 h-1 w-full bg-white/5 rounded-full overflow-hidden">
             <div class="h-full bg-emerald-500 transition-all duration-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                  [style.width.%]="summary().entries_24h > 0 ? 100 : 0"></div>
           </div>
         </div>
 
         <div class="industrial-card p-6 group hover:border-rose-500/30 transition-all">
           <div class="flex items-center justify-between mb-4">
             <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Salidas (24h)</span>
             <div class="w-8 h-8 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-500">
               <mat-icon class="text-sm">arrow_upward</mat-icon>
             </div>
           </div>
           <div class="flex items-baseline gap-2">
             <span class="text-3xl font-black text-surface-text tabular-nums">{{ summary().outputs_24h }}</span>
             <span class="text-[10px] font-bold text-rose-500 uppercase">Docs</span>
           </div>
           <div class="mt-4 h-1 w-full bg-white/5 rounded-full overflow-hidden">
             <div class="h-full bg-rose-500 transition-all duration-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]"
                  [style.width.%]="summary().outputs_24h > 0 ? 100 : 0"></div>
           </div>
         </div>
 
         <div class="industrial-card p-6 group hover:border-primary/30 transition-all">
           <div class="flex items-center justify-between mb-4">
             <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Transferencias</span>
             <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
               <mat-icon class="text-sm">swap_horiz</mat-icon>
             </div>
           </div>
           <div class="flex items-baseline gap-2">
             <span class="text-3xl font-black text-surface-text tabular-nums">{{ summary().transfers_24h }}</span>
             <span class="text-[10px] font-bold text-primary uppercase">Docs</span>
           </div>
           <div class="mt-4 h-1 w-full bg-white/5 rounded-full overflow-hidden">
             <div class="h-full bg-primary transition-all duration-500 shadow-[0_0_10px_rgba(0,229,255,0.5)]"
                  [style.width.%]="summary().transfers_24h > 0 ? 100 : 0"></div>
           </div>
         </div>
 
         <div class="industrial-card p-6 group hover:border-amber-500/30 transition-all">
           <div class="flex items-center justify-between mb-4">
             <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Pendientes</span>
             <div class="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-500">
               <mat-icon class="text-sm">pending_actions</mat-icon>
             </div>
           </div>
           <div class="flex items-baseline gap-2">
             <span class="text-3xl font-black text-surface-text tabular-nums">{{ summary().pending_docs }}</span>
             <span class="text-[10px] font-bold text-amber-500 uppercase">Docs</span>
           </div>
           <div class="mt-4 h-1 w-full bg-white/5 rounded-full overflow-hidden">
             <div class="h-full bg-amber-500 transition-all duration-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]"
                  [style.width.%]="summary().pending_docs > 0 ? 100 : 0"></div>
           </div>
         </div>
       </div>

      <!-- Documents Table Section -->
      <div class="industrial-card overflow-hidden">
        <div class="p-6 border-b border-surface-border bg-white/5 flex items-center justify-between">
          <h2 class="text-[10px] font-black text-surface-text uppercase tracking-[0.2em]">Listado de Documentos</h2>
          <div class="flex items-center gap-2">
            <span class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Mostrar:</span>
            <select 
              [value]="selectedLimit()"
              (change)="onLimitChange($event)"
              class="bg-surface-bg border border-surface-border rounded-lg px-3 py-1 text-[10px] font-bold uppercase tracking-widest outline-none focus:border-primary cursor-pointer hover:bg-white/5 transition-colors">
              <option [value]="50">Últimos 50</option>
              <option [value]="100">Últimos 100</option>
              <option [value]="500">Últimos 500</option>
              <option [value]="1000">Todos</option>
            </select>
          </div>
        </div>

        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-bg/50">
                <th class="px-3 md:px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Documento</th>
                <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest hidden md:table-cell">Tipo</th>
                <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest hidden lg:table-cell">Origen / Destino</th>
                <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest hidden sm:table-cell">Items</th>
                <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest hidden md:table-cell">Valor</th>
                <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Estado</th>
                <th class="px-3 md:px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-border">
              @for (doc of documents(); track doc.id) {
                <tr class="hover:bg-white/5 transition-all group cursor-pointer">
                  <td class="px-3 md:px-6 py-5">
                    <div class="flex flex-col">
                      <span class="text-xs font-mono font-black text-surface-text group-hover:text-primary transition-colors">{{ doc.folio }}</span>
                      @if (doc.customs_pedimento) {
                        <div class="flex items-center gap-1.5 mt-1">
                          <mat-icon class="text-[10px] text-amber-500">gavel</mat-icon>
                          <span class="text-[9px] text-amber-500 font-black uppercase tracking-widest">{{ doc.customs_pedimento }}</span>
                        </div>
                      }
                      <span class="text-[9px] text-surface-text-muted font-mono font-bold uppercase mt-0.5">{{ doc.created_at | date:'dd MMM yyyy HH:mm' }}</span>
                      <div class="lg:hidden mt-2 flex flex-col gap-1">
                         <span class="text-[8px] font-black text-primary uppercase tracking-tighter">{{ doc.concept_name || doc.type }}</span>
                         <span class="text-[8px] font-bold text-surface-text-muted uppercase truncate max-w-[100px]">{{ doc.origin }} -> {{ doc.destination }}</span>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-5 hidden md:table-cell">
                      <div class="flex items-center gap-3">
                        <div [class]="getTypeIconClass(doc.concept_name || doc.type)" class="w-8 h-8 rounded-lg border flex items-center justify-center">
                          <mat-icon class="text-sm">{{ getTypeIcon(doc.concept_name || doc.type) }}</mat-icon>
                        </div>
                        <div class="flex flex-col">
                          <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest">
                            {{ doc.concept_name || doc.type }}
                          </span>
                          @if (doc.concept_name && doc.concept_name !== doc.type) {
                            <span class="text-[8px] text-surface-text-muted/50 font-mono uppercase">{{ doc.type }}</span>
                          }
                        </div>
                      </div>
                  </td>
                  <td class="px-6 py-5 hidden lg:table-cell">
                    <div class="flex items-center gap-3">
                      <div class="flex flex-col">
                        <span class="text-[10px] font-black text-surface-text uppercase tracking-tight">{{ doc.origin }}</span>
                        <div class="flex items-center gap-2 mt-1">
                          <mat-icon class="text-[10px] text-primary">subdirectory_arrow_right</mat-icon>
                          <span class="text-[10px] font-bold text-surface-text-muted uppercase tracking-tight">{{ doc.destination }}</span>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-5 hidden sm:table-cell">
                    <div class="flex flex-col">
                      <span class="text-xs font-black text-surface-text tabular-nums">{{ doc.items_count }}</span>
                      <span class="text-[8px] font-bold text-surface-text-muted uppercase tracking-widest">Partidas</span>
                    </div>
                  </td>
                  <td class="px-6 py-5 hidden md:table-cell">
                    <div class="flex flex-col">
                      <span class="text-xs font-black text-primary tabular-nums">{{ doc.total_value | currencyFormat }}</span>
                      <span class="text-[8px] font-bold text-surface-text-muted uppercase tracking-widest italic">Valuación</span>
                    </div>
                  </td>
                  <td class="px-6 py-5">
                    <span [class]="getStatusClass(doc.status)" class="px-2 md:px-3 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest border">
                      {{ doc.status }}
                    </span>
                  </td>
                  <td class="px-3 md:px-6 py-5 text-right">
                    <div class="flex items-center justify-end gap-1 md:opacity-0 group-hover:opacity-100 transition-opacity">
                      <!-- ICT Specific Actions -->
                      @if (doc.type === 'ICT_IN' && doc.status === 'DRAFT') {
                        <button (click)="openConfirmModal(doc, $event)" class="px-2 py-1 bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded-lg text-[9px] font-black uppercase tracking-widest hover:bg-cyan-500/20 transition-all flex items-center gap-1">
                          <mat-icon class="text-xs">move_to_inbox</mat-icon>
                          Recibir
                        </button>
                      }
                      @if (doc.type === 'ICT_OUT' && doc.status === 'PROCESSED') {
                        <button (click)="openRevertModal(doc, $event)" class="px-2 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 rounded-lg text-[9px] font-black uppercase tracking-widest hover:bg-indigo-500/20 transition-all flex items-center gap-1">
                          <mat-icon class="text-xs">undo</mat-icon>
                          Reclamar
                        </button>
                      }

                      <button (click)="viewPdf(doc.id, $event)" class="p-2 text-surface-text-muted hover:text-primary hover:bg-primary/10 rounded-lg transition-all" title="Ver PDF">
                        <mat-icon class="text-lg">picture_as_pdf</mat-icon>
                      </button>
                      <button 
                        (click)="viewDetails(doc.id, $event)" 
                        [disabled]="isSelfTransfer(doc)"
                        [class.opacity-30]="isSelfTransfer(doc)"
                        class="p-2 text-surface-text-muted hover:text-primary hover:bg-primary/10 rounded-lg transition-all" 
                        [title]="isSelfTransfer(doc) ? 'Restricción Anti-Fraude' : 'Detalles'"
                      >
                        <mat-icon class="text-lg">{{ isSelfTransfer(doc) ? 'block' : 'visibility' }}</mat-icon>
                      </button>
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        
        <div class="p-4 bg-surface-bg/30 border-t border-surface-border flex items-center justify-between">
          <span class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Mostrando {{ documents().length }} registros</span>
          <div class="flex items-center gap-2">
            <button class="p-1 text-surface-text-muted hover:text-primary disabled:opacity-30" disabled>
              <mat-icon>chevron_left</mat-icon>
            </button>
            <div class="flex items-center gap-1">
              <span class="w-6 h-6 flex items-center justify-center bg-primary text-slate-950 text-[10px] font-black rounded">1</span>
              <span class="w-6 h-6 flex items-center justify-center hover:bg-white/5 text-surface-text-muted text-[10px] font-black rounded cursor-pointer">2</span>
              <span class="w-6 h-6 flex items-center justify-center hover:bg-white/5 text-surface-text-muted text-[10px] font-black rounded cursor-pointer">3</span>
            </div>
            <button class="p-1 text-surface-text-muted hover:text-primary">
              <mat-icon>chevron_right</mat-icon>
            </button>
          </div>
        </div>
      </div>

       <!-- Modals (ICT Flow) -->
       @if (isConfirmingReceipt()) {
         <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in" (click)="isConfirmingReceipt.set(false)">
           <div class="industrial-card w-full max-w-lg p-8 space-y-6" (click)="$event.stopPropagation()">
              <div class="flex items-center gap-4 border-b border-surface-border pb-6">
                <div class="w-12 h-12 bg-cyan-500/10 rounded-xl flex items-center justify-center text-cyan-500">
                  <mat-icon>move_to_inbox</mat-icon>
                </div>
                <div>
                  <h3 class="text-xl font-black text-surface-text uppercase tracking-widest italic">Confirmar Recepción</h3>
                  <p class="text-[10px] text-surface-text-muted uppercase font-mono tracking-widest">Folio: {{ selectedDoc()?.folio }}</p>
                </div>
              </div>

              <div class="bg-white/5 border border-white/10 rounded-xl p-6 space-y-4">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block mb-1">Cantidad Enviada</span>
                    <span class="text-xl font-black text-surface-text">{{ selectedDoc()?.items_count }} unidades</span>
                  </div>
                  <div>
                    <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block mb-1">Valor Pactado (WAC destino)</span>
                    <span class="text-xl font-black text-primary">{{ selectedDoc()?.total_value | currencyFormat }}</span>
                  </div>
                </div>

                <div class="pt-4 border-t border-white/5 space-y-4">
                   <div class="grid grid-cols-2 gap-4">
                      <div>
                        <label class="text-[9px] font-black text-emerald-400 uppercase tracking-widest block mb-2">Cant. Recibida (OK)</label>
                        <input 
                          type="number" 
                          [value]="receivedQty()" 
                          (input)="onReceivedQtyChange($any($event.target).value)"
                          class="w-full bg-surface-bg border border-emerald-500/30 rounded-xl px-4 py-3 text-lg font-black text-surface-text focus:border-emerald-500 outline-none transition-all placeholder:text-surface-text-muted/30"
                        >
                      </div>
                      <div>
                        <label class="text-[9px] font-black text-rose-400 uppercase tracking-widest block mb-2">Cant. Dañada (Red Tag)</label>
                        <input 
                          type="number" 
                          [value]="damagedQty()" 
                          (input)="damagedQty.set($any($event.target).value)"
                          class="w-full bg-surface-bg border border-rose-500/30 rounded-xl px-4 py-3 text-lg font-black text-surface-text focus:border-rose-500 outline-none transition-all placeholder:text-surface-text-muted/30"
                        >
                      </div>
                   </div>

                   @if (hasDiscrepancy()) {
                     <div class="bg-rose-500/10 border border-rose-500/20 rounded-lg p-3 animate-pulse">
                        <p class="text-[8px] text-rose-400 font-black uppercase tracking-widest">
                          ⚠️ ATENCIÓN: Se detectó una discrepancia de {{ discrepancyQty() }} unidades.
                          El sistema generará un ajuste automático por merma.
                        </p>
                     </div>
                   }
                </div>
              </div>

              <div class="flex items-center gap-3 pt-4">
                <button (click)="isConfirmingReceipt.set(false)" class="flex-1 py-4 border border-surface-border text-[10px] uppercase font-black tracking-widest rounded-xl hover:bg-white/5 transition-all">Cancelar</button>
                <button 
                  (click)="confirmReceipt()" 
                  [disabled]="isProcessingAction()"
                  class="flex-[2] py-4 bg-primary text-black text-[10px] uppercase font-black tracking-widest rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50"
                >
                  Confirmar y Actualizar Stock
                </button>
              </div>
           </div>
         </div>
       }

       @if (isReclaimingStock()) {
         <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in" (click)="isReclaimingStock.set(false)">
           <div class="industrial-card w-full max-w-lg p-8 space-y-6" (click)="$event.stopPropagation()">
              <div class="flex items-center gap-4 border-b border-surface-border pb-6">
                <div class="w-12 h-12 bg-indigo-500/10 rounded-xl flex items-center justify-center text-indigo-500">
                  <mat-icon>undo</mat-icon>
                </div>
                <div>
                  <h3 class="text-xl font-black text-surface-text uppercase tracking-widest italic">Reclamar Stock (Revertir)</h3>
                  <p class="text-[10px] text-surface-text-muted uppercase font-mono tracking-widest">Folio: {{ selectedDoc()?.folio }}</p>
                </div>
              </div>

              <div class="bg-rose-500/5 border border-rose-500/20 rounded-xl p-6">
                <p class="text-[11px] text-rose-200/70 uppercase font-bold leading-relaxed tracking-wide">
                  ⚠️ ATENCIÓN: Esta acción revertirá la transferencia. El stock saldrá del almacén de tránsito y regresará al inventario disponible de tu almacén de origen. El folio de recepción en la empresa destino será cancelado.
                </p>
              </div>

              <div class="space-y-4">
                 <label class="text-[9px] font-black text-indigo-400 uppercase tracking-widest block">Motivo de la Reversión</label>
                 <textarea 
                   [value]="revertReason()" 
                   (input)="revertReason.set($any($event.target).value)"
                   placeholder="Ej. Mercancía abandonada, Error en logística..."
                   class="w-full h-24 bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-xs font-bold text-surface-text focus:border-indigo-500 outline-none transition-all"
                 ></textarea>
              </div>

              <div class="flex items-center gap-3 pt-4">
                <button (click)="isReclaimingStock.set(false)" class="flex-1 py-4 border border-surface-border text-[10px] uppercase font-black tracking-widest rounded-xl hover:bg-white/5 transition-all">Cancelar</button>
                <button 
                  (click)="reclaimStock()"
                  [disabled]="isProcessingAction() || !revertReason()"
                  class="flex-[2] py-4 bg-indigo-500 text-white text-[10px] uppercase font-black tracking-widest rounded-xl hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all disabled:opacity-30"
                >
                  Ejecutar Reclamo Stock
                </button>
              </div>
           </div>
         </div>
       }
    </div>
  `,
  styles: [`
    :host { display: block; }
    .custom-scrollbar::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.05);
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: rgba(0, 229, 255, 0.2);
      border-radius: 10px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
      background: rgba(0, 229, 255, 0.4);
    }
  `]
})
export class InventoryDocumentsComponent implements OnInit {
  translation = inject(TranslationService);
  inventoryService = inject(InventoryService);
  auth = inject(AuthService);
  router = inject(Router);
  
  documents = signal<any[]>([]);
  warehouses = signal<any[]>([]);
   selectedWarehouseId = signal<string | null>(null);
   selectedLimit = signal<number>(50);
   isLoading = signal(false);
   summary = signal<any>({
     entries_24h: 0,
     outputs_24h: 0,
     transfers_24h: 0,
     pending_docs: 0
   });

    // ICT Actions State
    isConfirmingReceipt = signal(false);
    isReclaimingStock = signal(false);
    selectedDoc = signal<any>(null);
    revertReason = signal('');
    receivedQty = signal<number | null>(null);
    damagedQty = signal<number>(0);
    discrepancyQty = computed(() => {
      const doc = this.selectedDoc();
      if (!doc) return 0;
      const total = Number(this.receivedQty() || 0) + Number(this.damagedQty() || 0);
      return Math.abs(doc.items_count - total);
    });
    hasDiscrepancy = computed(() => this.discrepancyQty() > 0 || Number(this.damagedQty()) > 0);
    isProcessingAction = signal(false);

  private lastLoadedCompanyId: string | null = null;

  constructor() {
    // 🏢 Reactive: Reload data when corporate context (Tenant) changes
    effect(async () => {
      const companyId = this.auth.activeCompanyId();
      
      // Industrial Guard: Use untracked to avoid cyclical dependency on local signals (warehouse, documents)
      // and prevent re-run if company hasn't actually changed (e.g. on token rotation)
      if (companyId === this.lastLoadedCompanyId && companyId !== null) return;
      
      untracked(async () => {
        if (companyId) {
          console.log(`[InventoryDocs] 🏢 Company changed to ${companyId}. Reloading...`);
          this.lastLoadedCompanyId = companyId;
          
          // Reset local filters and reload
          this.selectedWarehouseId.set(null);
          await this.inventoryService.loadCatalogs(); // Ensure catalogs are ready
          await this.loadDocuments();
        } else {
          this.lastLoadedCompanyId = null;
          this.documents.set([]);
          this.summary.set({
            entries_24h: 0,
            outputs_24h: 0,
            transfers_24h: 0,
            pending_docs: 0
          });
        }
      });
    }, { allowSignalWrites: true });

    // Sync warehouses from service
    effect(() => {
      this.warehouses.set(this.inventoryService.warehouses());
    }, { allowSignalWrites: true });
  }

  async ngOnInit() {
    // Demo logic still belongs here as it's a one-time thing per init
    untracked(async () => {
      await this.inventoryService.verifyDemoDataFreshness(this.auth.activeCompanyId() || '');
    });
  }

  async loadDocuments() {
    if (this.isLoading()) return;
    this.isLoading.set(true);
    try {
      const warehouseId = this.selectedWarehouseId() || undefined;
      const limit = this.selectedLimit();
      // Parallel fetch for improved UX
      const [data, summaryData] = await Promise.all([
        this.inventoryService.getMovements(limit, warehouseId),
        this.inventoryService.getSummary(warehouseId)
      ]);

      this.summary.set(summaryData);
      
      let itemsToMap = Array.isArray(data) ? data : ((data as any)?.data || []);
      if (!Array.isArray(itemsToMap)) {
         console.warn('[Documents] Data is not an array:', data);
         itemsToMap = [];
      }
      
      this.documents.set(itemsToMap.map((d: any) => ({
        id: d.id,
        folio: d.folio || d.id || 'N/A',
        type: d.type || 'UNKNOWN',
        /** Display name resolved from concept catalog (preferred for UI) */
        concept_name: d.concept_name || null,
        concept_id: d.concept_id || null,
        status: d.status || 'PROCESSED',
        origin: d.origin || 'N/A',
        destination: d.destination || 'N/A',
        items_count: d.items_count || 0,
        total_value: d.total_value || d.total_weight || 0,
        created_at: d.date || new Date().toISOString(),
        created_by: d.created_by || 'SISTEMA',
        external_reference: d.external_reference,
        customs_pedimento: d.customs_pedimento
      })));
    } catch (e) {
      console.error('[Documents] Failed to load documents:', e);
    } finally {
      this.isLoading.set(false);
    }
  }

  onWarehouseChange(event: Event) {
    const select = event.target as HTMLSelectElement;
    const value = select.value === 'null' ? null : select.value;
    this.selectedWarehouseId.set(value);
    this.loadDocuments();
  }

  onLimitChange(event: Event) {
    const select = event.target as HTMLSelectElement;
    const value = parseInt(select.value, 10);
    this.selectedLimit.set(value || 50);
    this.loadDocuments();
  }

  viewPdf(docId: string, event: Event) {
    event.stopPropagation();
    this.router.navigate(['/inventory/documents', docId]);
  }

  viewDetails(docId: string, event: Event) {
    event.stopPropagation();
    this.router.navigate(['/inventory/documents', docId]);
  }

  t(key: string, fallback: string): string {
    return this.translation.translate(key, fallback);
  }

  getTypeIcon(typeOrConcept: string): string {
    const t = (typeOrConcept || '').toUpperCase();
    // Match concept names first (Spanish display labels)
    if (t.includes('COMPRA') || t.includes('PUR-REC') || t.includes('RECEPCI')) return 'shopping_cart';
    if (t.includes('DEVOLUC') || t.includes('PUR-RET')) return 'assignment_return';
    if (t.includes('AJUSTE POS') || t.includes('ADJ-POS')) return 'add_circle';
    if (t.includes('AJUSTE NEG') || t.includes('ADJ-NEG') || t.includes('MERMA') || t.includes('SCRAP')) return 'remove_circle';
    if (t.includes('TRASPASO') || t.includes('INT-TRA') || t.includes('TRANSFER')) return 'swap_horiz';
    if (t.includes('ICT_OUT')) return 'outbox';
    if (t.includes('ICT_IN')) return 'move_to_inbox';
    // Fallback to technical type
    if (t.includes('ENTRY') || t.includes('ENTRADA') || t === 'IN') return 'arrow_downward';
    if (t.includes('EXIT') || t.includes('SALIDA') || t === 'OUT') return 'arrow_upward';
    if (t.includes('ADJUSTMENT')) return 'tune';
    return 'help_outline';
  }

  getTypeIconClass(typeOrConcept: string): string {
    const t = (typeOrConcept || '').toUpperCase();
    // Concept-aware color mapping
    if (t.includes('COMPRA') || t.includes('PUR-REC') || t.includes('RECEPCI') || t.includes('ENTRY') || t.includes('ENTRADA') || t === 'IN')
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    if (t.includes('DEVOLUC') || t.includes('PUR-RET') || t.includes('EXIT') || t.includes('SALIDA') || t === 'OUT')
      return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
    if (t.includes('TRASPASO') || t.includes('INT-TRA') || t.includes('TRANSFER'))
      return 'bg-neon-blue/10 text-neon-blue border-neon-blue/30';
    if (t.includes('ICT_OUT')) return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
    if (t.includes('ICT_IN')) return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
    if (t.includes('AJUSTE POS') || t.includes('ADJ-POS')) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    if (t.includes('AJUSTE NEG') || t.includes('ADJ-NEG') || t.includes('MERMA') || t.includes('SCRAP'))
      return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    if (t.includes('ADJUSTMENT')) return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'PROCESSED': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'DRAFT': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'CANCELLED': return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  }

  isSelfTransfer(document: any): boolean {
    let currentUserId = this.auth.currentUser()?.id;
    if (!currentUserId) {
      try {
        const session = JSON.parse(localStorage.getItem('_ic_auth_ctx') || '{}');
        currentUserId = session?.user?.id || session?.user_id;
      } catch { }
    }
    return (document.type === 'Traspaso' || document.type === 'TRANSFER' || document.type === 'ICT_TRANSFER') && document.created_by === currentUserId;
  }

  // === ICT Actions ===

  openConfirmModal(doc: any, event: Event) {
    event.stopPropagation();
    this.selectedDoc.set(doc);
    this.receivedQty.set(doc.items_count);
    this.damagedQty.set(0);
    this.isConfirmingReceipt.set(true);
  }

  onReceivedQtyChange(value: string) {
    const qty = Number(value);
    this.receivedQty.set(qty);
    // Auto-calculate damaged if user just wants to split
    const doc = this.selectedDoc();
    if (doc && qty < doc.items_count) {
       // Optional: auto-fill damaged? Better leave it manual for accuracy.
    }
  }

  openRevertModal(doc: any, event: Event) {
    event.stopPropagation();
    this.selectedDoc.set(doc);
    this.revertReason.set('');
    this.isReclaimingStock.set(true);
  }

  async confirmReceipt() {
    const doc = this.selectedDoc();
    if (!doc || this.isProcessingAction()) return;

    this.isProcessingAction.set(true);
    try {
      // In ICT context, we use the external_reference as the transferId
      await this.inventoryService.receiveTransfer(
        doc.external_reference || doc.id, 
        this.receivedQty() || undefined,
        this.damagedQty() || 0
      );
      this.isConfirmingReceipt.set(false);
      await this.loadDocuments();
    } catch (e) {
      console.error('[ICT] Error confirming receipt:', e);
    } finally {
      this.isProcessingAction.set(false);
    }
  }

  async reclaimStock() {
    const doc = this.selectedDoc();
    if (!doc || this.isProcessingAction()) return;

    this.isProcessingAction.set(true);
    try {
      await this.inventoryService.revertTransfer(doc.external_reference || doc.id, this.revertReason());
      this.isReclaimingStock.set(false);
      await this.loadDocuments();
    } catch (e) {
      console.error('[ICT] Error reclaiming stock:', e);
    } finally {
      this.isProcessingAction.set(false);
    }
  }
}
