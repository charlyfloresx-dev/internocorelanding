import { Component, inject, OnInit, signal, effect, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { DashboardService } from '@services/dashboard.service';
import { InventoryService } from '@services/inventory.service';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { StatusBadgeComponent } from '../../shared/components/status-badge.component';
import { ItemSearchComponent, InventoryItem } from '../../shared/components/item-search.component';
import { InventorySummary, MovementDocumentRow, DashboardDTO } from '@models/api.types';
import { finalize } from 'rxjs/operators';
import { MoneyPipe } from '../../shared/pipes/money.pipe';

import { InventoryReadinessGatekeeperComponent } from './readiness-gatekeeper.component';

@Component({
  selector: 'app-inventory-dashboard',
  standalone: true,
  imports: [CommonModule, MatIconModule, TranslatePipe, StatusBadgeComponent, ItemSearchComponent, InventoryReadinessGatekeeperComponent, MoneyPipe],
  template: `
    <!-- Onboarding Gatekeeper -->
    <app-inventory-readiness-gatekeeper 
      *ngIf="inventoryReadiness() && !inventoryReadiness()?.is_ready"
      [readiness]="inventoryReadiness()"
      (onRefresh)="checkReadiness()">
    </app-inventory-readiness-gatekeeper>

    <div class="p-6 space-y-8 animate-fade-in relative overflow-hidden min-h-screen">
      <!-- Scanline Effect (Industrial Feel) -->
      <div class="scan-line-overlay pointer-events-none"></div>

      <!-- Header Section -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
        <div>
          <h1 class="text-3xl font-black text-white tracking-tighter uppercase italic glow-text">
            {{ 'inventory.dashboard.title' | translate:'Control de Misión' }}
          </h1>
          <p class="text-surface-text-muted font-mono text-[10px] tracking-widest uppercase mt-1">
            {{ 'inventory.dashboard.subtitle' | translate:'Telemetría de Inventarios en Tiempo Real' }}
          </p>
        </div>
        
        <div class="flex flex-1 max-w-md items-center gap-4">
          <div class="flex-1">
             <app-item-search (itemSelected)="onGlobalSearch($event)"></app-item-search>
          </div>
          
          <!-- Warehouse Selector -->
          <div class="flex flex-col min-w-[180px]">
            <span class="text-[8px] font-black text-primary uppercase tracking-[0.2em] mb-1">Nodo de Control</span>
            <select [value]="selectedWarehouseId()" 
                    (change)="onWarehouseChange($event)"
                    class="bg-ic-slate border border-primary/30 rounded text-white text-[10px] font-black uppercase tracking-widest px-3 py-2 outline-none focus:border-primary shadow-[0_0_10px_rgba(30,174,219,0.1)] transition-all cursor-pointer">
               <option value="" disabled>SELECCIONE NODO...</option>
               @for (wh of physicalWarehouses(); track wh.id) {
                 <option [value]="wh.id">{{ wh.code }} - {{ wh.name }}</option>
               } @empty {
                 <option value="" disabled>CARGANDO NODOS...</option>
               }
            </select>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button (click)="refreshAll()" 
                  [disabled]="loading()"
                  class="btn-primary py-2 px-4 text-[10px] uppercase tracking-widest h-11">
            <mat-icon [class.animate-spin]="loading()" class="text-sm">refresh</mat-icon>
            {{ 'common.refresh' | translate:'Sincronizar' }}
          </button>
        </div>
      </div>

      <!-- Mission Control Primary Metrics -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
         <!-- VALUATION CARD (Mission Control) -->
         <div class="industrial-card p-6 border-l-4 border-primary bg-gradient-to-br from-primary/5 to-transparent">
            <div class="flex justify-between items-start mb-2">
               <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">VALUACIÓN TOTAL</span>
               <div class="flex items-center gap-1 text-emerald-400" *ngIf="(missionControl()?.valuation?.variation_percentage || 0) >= 0; else drop">
                  <mat-icon class="text-xs">trending_up</mat-icon>
                  <span class="text-[10px] font-bold">+{{ missionControl()?.valuation?.variation_percentage | number:'1.2-2' }}%</span>
               </div>
               <ng-template #drop>
                  <div class="flex items-center gap-1 text-red-500">
                    <mat-icon class="text-xs">trending_down</mat-icon>
                    <span class="text-[10px] font-bold">{{ missionControl()?.valuation?.variation_percentage | number:'1.2-2' }}%</span>
                  </div>
               </ng-template>
            </div>
            <div class="flex items-baseline gap-2">
               <span class="text-xs text-white/50 font-bold">$</span>
               <span class="text-4xl font-black text-white glow-text tracking-tighter">
                  {{ missionControl()?.valuation?.total_usd | number:'1.2-2' || '0.00' }}
               </span>
               <span class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest">USD</span>
            </div>
            <div class="mt-4 p-2 bg-black/20 rounded border border-white/5 flex items-center justify-between">
               <span class="text-[9px] font-bold text-surface-text-muted uppercase tracking-tighter italic">Cierre Ayer:</span>
               <span class="text-[10px] font-mono text-white/70">$ {{ missionControl()?.valuation?.stock_yesterday | number:'1.2-2' || '0.00' }}</span>
            </div>
         </div>

         <!-- CRITICAL ALERTS (Mission Control) -->
         <div class="industrial-card p-6 border-l-4 border-amber-500 overflow-hidden relative">
            <div class="relative z-10">
               <div class="flex justify-between items-start mb-2">
                  <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">ALERTAS CRÍTICAS</span>
                  <span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-500 text-[9px] font-black border border-amber-500/30">
                     {{ missionControl()?.critical_alerts?.length || 0 }} SKUs
                  </span>
               </div>
               
               <div class="space-y-2 mt-3 max-h-[80px] overflow-y-auto custom-scrollbar">
                  @for (alert of missionControl()?.critical_alerts; track alert.sku) {
                     <div class="flex items-center justify-between text-[10px] border-b border-white/5 pb-1">
                        <span class="font-mono text-white">{{ alert.sku }}</span>
                        <span class="font-black text-amber-400">{{ alert.current_quantity }} / {{ alert.min_quantity }}</span>
                     </div>
                  } @empty {
                     <div class="text-[9px] text-emerald-400 font-bold uppercase italic opacity-60 flex items-center gap-2 py-4">
                        <mat-icon class="text-xs">check_circle</mat-icon>
                        Niveles de stock garantizados
                     </div>
                  }
               </div>
            </div>
            <!-- Background Decoration -->
            <mat-icon class="absolute -right-4 -bottom-4 text-8xl text-amber-500/5 rotate-12">warning</mat-icon>
         </div>

         <!-- ACTIVITY HEATMAP -->
         <div class="industrial-card p-6 border-l-4 border-ic-cyan">
            <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em] mb-4 block">FLUJO POR HORA (24H)</span>
            <div class="flex items-end gap-1 h-20 px-2 box-border">
               @for (h of missionControl()?.hourly_series; track h.hour) {
                  @let entries_px = (h.entries / 50) * 100;
                  @let exits_px = (h.exits / 50) * 100;
                  <div class="flex-1 group relative h-full flex flex-col justify-end">
                     <div class="bg-red-500/30 w-full mb-0.5 transition-all duration-500 hover:bg-red-500" 
                          [style.height.%]="exits_px"></div>
                     <div class="bg-emerald-500/30 w-full transition-all duration-500 hover:bg-emerald-500" 
                          [style.height.%]="entries_px"></div>
                     
                     <!-- Tooltip -->
                     <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50">
                        <div class="bg-black/95 border border-white/10 p-2 rounded text-[8px] font-mono text-white whitespace-nowrap shadow-2xl">
                           <div class="text-[9px] mb-1 font-black text-white/50 border-b border-white/10">{{ h.hour }}h</div>
                           <div class="text-emerald-400">ENTRADAS: {{ h.entries }}</div>
                           <div class="text-red-400">SALIDAS: {{ h.exits }}</div>
                        </div>
                     </div>
                  </div>
               } @empty {
                 <div class="flex-1 flex items-center justify-center text-[8px] text-surface-text-muted uppercase italic opacity-40">
                   Sincronizando flujo...
                 </div>
               }
            </div>
            <div class="mt-2 flex justify-between text-[7px] font-bold text-surface-text-muted uppercase tracking-widest opacity-50">
               <span>24h ago</span>
               <span>Ahora</span>
            </div>
         </div>
      </div>

      <!-- Secondary Telemetry Widgets (Operational Row) -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">
        <!-- Entries 24h -->
        <div class="industrial-card p-6 group">
          <div class="flex items-start justify-between mb-4">
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">INBOUND</span>
              <h3 class="text-lg font-bold text-white uppercase">{{ 'inventory.dashboard.entries' | translate:'Entradas 24h' }}</h3>
            </div>
            <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 flex items-center justify-center shadow-[0_0_15px_rgba(16,185,129,0.2)]">
              <mat-icon>south_west</mat-icon>
            </div>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="text-4xl font-black text-white tracking-tighter">{{ summary()?.entries_24h || 0 }}</span>
            <span class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest">Movimientos</span>
          </div>
          <div class="mt-4 progress-bar-industrial bg-white/5 h-1 rounded-full overflow-hidden">
             <div class="bg-emerald-500 h-full shadow-[0_0_8px_rgba(16,185,129,0.6)] transition-all duration-1000" [style.width.%]="75"></div>
          </div>
        </div>

        <!-- Outputs 24h -->
        <div class="industrial-card p-6 group">
          <div class="flex items-start justify-between mb-4">
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">OUTBOUND</span>
              <h3 class="text-lg font-bold text-white uppercase">{{ 'inventory.dashboard.outputs' | translate:'Salidas 24h' }}</h3>
            </div>
            <div class="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/30 text-red-500 flex items-center justify-center shadow-[0_0_15px_rgba(239,68,68,0.2)]">
              <mat-icon>north_east</mat-icon>
            </div>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="text-4xl font-black text-white tracking-tighter">{{ summary()?.outputs_24h || 0 }}</span>
            <span class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest">Despachos</span>
          </div>
          <div class="mt-4 progress-bar-industrial bg-white/5 h-1 rounded-full overflow-hidden">
             <div class="bg-red-500 h-full shadow-[0_0_8px_rgba(239,68,68,0.6)] transition-all duration-1000" [style.width.%]="45"></div>
          </div>
        </div>

        <!-- Transfers 24h -->
        <div class="industrial-card p-6 group">
          <div class="flex items-start justify-between mb-4">
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">INTERNAL</span>
              <h3 class="text-lg font-bold text-white uppercase">{{ 'inventory.dashboard.transfers' | translate:'Traspasos 24h' }}</h3>
            </div>
            <div class="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-500 flex items-center justify-center shadow-[0_0_15px_rgba(14,165,233,0.2)]">
              <mat-icon>sync_alt</mat-icon>
            </div>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="text-4xl font-black text-white tracking-tighter">{{ summary()?.transfers_24h || 0 }}</span>
            <span class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest">Logística</span>
          </div>
          <div class="mt-4 progress-bar-industrial bg-white/5 h-1 rounded-full overflow-hidden">
             <div class="bg-sky-500 h-full shadow-[0_0_8px_rgba(14,165,233,0.6)] transition-all duration-1000" [style.width.%]="60"></div>
          </div>
        </div>

        <!-- Pending Documents -->
        <div class="industrial-card p-6 group">
          <div class="flex items-start justify-between mb-4">
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">QUEUE</span>
              <h3 class="text-lg font-bold text-white uppercase">{{ 'inventory.dashboard.pending' | translate:'Pendientes' }}</h3>
            </div>
            <div class="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-500 flex items-center justify-center shadow-[0_0_15px_rgba(245,158,11,0.2)]">
              <mat-icon>pending_actions</mat-icon>
            </div>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="text-4xl font-black text-white tracking-tighter">{{ summary()?.pending_docs || 0 }}</span>
            <span class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest">Borradores</span>
          </div>
          <div class="mt-4 progress-bar-industrial bg-white/5 h-1 rounded-full overflow-hidden">
             <div class="bg-amber-500 h-full shadow-[0_0_8px_rgba(245,158,11,0.6)] transition-all duration-1000" [style.width.%]="20"></div>
          </div>
        </div>
      </div>

      <!-- Main Section: Recent Ledger -->
      <div class="industrial-card overflow-hidden relative z-10 flex flex-col">
        <div class="p-6 border-b border-white/5 flex flex-col md:flex-row md:items-center justify-between bg-white/[0.02] gap-4">
           <div class="flex items-center gap-4">
             <h2 class="text-xs font-black text-white uppercase tracking-[0.2em] flex items-center">
               <mat-icon class="text-primary text-sm mr-2">receipt_long</mat-icon>
               Libro Mayor Reciente (Kardex)
             </h2>
             <span class="text-[9px] font-bold px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
               {{ totalRecords() }} TOTAL
             </span>
           </div>

           <div class="flex items-center gap-3">
             <div class="flex items-center gap-2">
               <span class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest italic">Mostrar:</span>
               <select [value]="pageSize()" 
                       (change)="onPageSizeChange($event)"
                       class="bg-ic-slate border border-white/10 rounded text-sky-400 text-[10px] font-black uppercase tracking-widest px-2 py-1 outline-none focus:border-primary/50 transition-all cursor-pointer">
                 <option [value]="10">ÚLTIMOS 10</option>
                 <option [value]="25">ÚLTIMOS 25</option>
                 <option [value]="50">ÚLTIMOS 50</option>
                 <option [value]="100">ÚLTIMOS 100</option>
               </select>
             </div>
             <button class="text-[10px] font-bold text-primary uppercase tracking-widest hover:glow-text transition-all">Ver Historial Completo</button>
           </div>
        </div>
        
        <div class="overflow-x-auto min-h-[400px]">
           <table class="w-full text-left border-collapse">
             <thead>
               <tr class="bg-white/[0.03]">
                 <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest w-[20%]">Identidad Folio</th>
                 <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest w-[15%]">Evento</th>
                 <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest w-[30%]">Nodos de Tránsito</th>
                 <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest text-right w-[10%]">Items</th>
                 <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest text-right w-[10%]">Monto</th>
                 <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest text-center w-[15%]">Estado Ledger</th>
               </tr>
             </thead>
             <tbody class="divide-y divide-white/5">
               @if (loading()) {
                 @for (i of [1,2,3,4,5]; track i) {
                   <tr class="animate-pulse bg-white/[0.01]">
                     <td class="px-6 py-6"><div class="h-4 bg-white/5 rounded w-24"></div></td>
                     <td class="px-6 py-6"><div class="h-4 bg-white/5 rounded w-16"></div></td>
                     <td class="px-6 py-6"><div class="h-4 bg-white/5 rounded w-48"></div></td>
                     <td class="px-6 py-6 text-right"><div class="h-4 bg-white/5 rounded w-8 ml-auto"></div></td>
                     <td class="px-6 py-6 flex justify-center"><div class="h-6 bg-white/5 rounded-full w-20"></div></td>
                   </tr>
                 }
               } @else if (movements().length === 0) {
                 <tr>
                   <td colspan="5" class="px-6 py-32 text-center text-surface-text-muted italic text-xs uppercase tracking-widest opacity-30">
                     <mat-icon class="text-4xl mb-4 block mx-auto">settings_backup_restore</mat-icon>
                     Sincronización completa. No hay movimientos registrados para esta página.
                   </td>
                 </tr>
               } @else {
                 @for (row of movements(); track row.id) {
                   <tr class="hover:bg-ic-cyan/5 transition-colors cursor-pointer group border-l-2 border-transparent hover:border-ic-cyan">
                     <td class="px-6 py-4">
                       <div class="flex flex-col">
                         <span class="text-[13px] font-black text-white group-hover:text-primary transition-colors tracking-tight font-mono">{{ row.folio }}</span>
                         <span class="text-[9px] font-mono text-surface-text-muted uppercase tracking-tighter">{{ row.date | date:'MMM dd, HH:mm:ss' }}</span>
                       </div>
                     </td>
                     <td class="px-6 py-4">
                        <div class="flex items-center gap-2">
                          <mat-icon [class]="row.type === 'ENTRY' ? 'text-emerald-500' : 'text-red-500'" class="text-xs">
                            {{ row.type === 'ENTRY' ? 'arrow_downward' : 'arrow_upward' }}
                          </mat-icon>
                          <span class="text-[10px] font-bold text-white uppercase tracking-widest">{{ row.type }}</span>
                        </div>
                     </td>
                     <td class="px-6 py-4">
                        <div class="flex flex-col gap-1">
                           <div class="flex items-center gap-2">
                              <span class="text-[10px] font-bold text-white uppercase">{{ row.origin || 'N/A' }}</span>
                           </div>
                           <div [class.opacity-40]="row.destination === 'N/A'" class="flex items-center gap-1.5 ml-2">
                              <mat-icon class="text-[10px] text-ic-cyan/50 font-black">subdirectory_arrow_right</mat-icon>
                              <span class="text-[9px] font-bold text-ic-cyan/70 uppercase italic tracking-wider">{{ row.destination || 'N/A' }}</span>
                           </div>
                        </div>
                     </td>
                     <td class="px-6 py-4 text-right">
                       <span class="text-[13px] font-black text-white font-mono">{{ row.items_count }}</span>
                     </td>
                     <td class="px-6 py-4 text-right">
                       <span class="text-[10px] font-black text-primary font-mono">{{ (row as any).total_valuation | money }}</span>
                     </td>
                     <td class="px-6 py-4">
                       <div class="flex justify-center items-center gap-3">
                         <app-status-badge [status]="row.status"></app-status-badge>
                         
                         <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button class="p-1.5 hover:bg-white/10 rounded-lg text-surface-text-muted hover:text-primary transition-colors" title="Detalle Forense">
                               <mat-icon class="text-sm">visibility</mat-icon>
                            </button>
                            @if (row.status === 'DRAFT') {
                              <button class="p-1.5 hover:bg-white/10 rounded-lg text-surface-text-muted hover:text-amber-400 transition-colors" title="Editar">
                                 <mat-icon class="text-sm">edit</mat-icon>
                              </button>
                            }
                         </div>
                       </div>
                     </td>
                   </tr>
                 }
               }
             </tbody>
           </table>
        </div>

        <!-- Pagination Bar -->
        <div class="p-6 bg-white/[0.03] border-t border-white/5 flex items-center justify-between relative">
           <div class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em] flex items-center gap-4">
              <span>Mostrando registros {{ startRecord() }} - {{ endRecord() }} de {{ totalRecords() }}</span>
              <div class="w-32 h-0.5 bg-white/5 rounded-full overflow-hidden">
                 <div class="bg-primary h-full transition-all duration-700" [style.width.%]="progressPercentage()"></div>
              </div>
           </div>

           <div class="flex items-center gap-2">
              <button (click)="changePage(currentPage() - 1)"
                      [disabled]="currentPage() === 1 || loading()"
                      class="p-2 border border-white/10 rounded-lg hover:bg-white/10 disabled:opacity-20 disabled:cursor-not-allowed transition-all text-white">
                <mat-icon>chevron_left</mat-icon>
              </button>
              
              <div class="flex items-center gap-1 px-4 text-[11px] font-black text-white">
                <span class="text-primary italic">PAGE</span>
                <span class="bg-ic-slate border border-primary/30 px-3 py-1 rounded-md min-w-[32px] text-center">{{ currentPage() }}</span>
                <span class="text-surface-text-muted opacity-40">/ {{ totalPages() }}</span>
              </div>

              <button (click)="changePage(currentPage() + 1)"
                      [disabled]="currentPage() >= totalPages() || loading()"
                      class="p-2 border border-white/10 rounded-lg hover:bg-white/10 disabled:opacity-20 disabled:cursor-not-allowed transition-all text-white">
                <mat-icon>chevron_right</mat-icon>
              </button>
           </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .scan-line-overlay {
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      pointer-events: none;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.05), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.05));
      background-size: 100% 2px, 3px 100%;
      z-index: 5;
      opacity: 0.1;
    }
    .custom-scrollbar::-webkit-scrollbar { width: 4px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
    .glow-text { text-shadow: 0 0 10px rgba(30,174,219,0.5); }
    .industrial-card {
      background: rgba(15, 23, 42, 0.6);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 4px;
    }
  `]
})
export class InventoryDashboardComponent implements OnInit {
  private dashboardService = inject(DashboardService);
  private inventoryService = inject(InventoryService);
  
  // State Signals
  summary = signal<InventorySummary | null>(null);
  movements = signal<MovementDocumentRow[]>([]);
  missionControl = signal<DashboardDTO | null>(null);
  selectedWarehouseId = signal<string>('');
  loading = signal<boolean>(false);
  inventoryReadiness = this.inventoryService.inventoryReadiness;
  
  // Catalogs from service
  warehouses = this.inventoryService.warehouses;
  physicalWarehouses = this.inventoryService.physicalWarehouses;

  // Pagination Signals
  currentPage = signal<number>(1);
  pageSize = signal<number>(25);
  totalRecords = signal<number>(0);

  // Computed Values
  totalPages = computed(() => Math.ceil(this.totalRecords() / this.pageSize()) || 1);
  startRecord = computed(() => this.movements().length > 0 ? (this.currentPage() - 1) * this.pageSize() + 1 : 0);
  endRecord = computed(() => Math.min(this.currentPage() * this.pageSize(), this.totalRecords()));
  progressPercentage = computed(() => (this.endRecord() / (this.totalRecords() || 1)) * 100);

  constructor() {
    // Effect to reload all data when warehouse selection changes
    effect(() => {
      const whId = this.selectedWarehouseId();
      if (whId) {
        this.loadMissionControl();
        // Option to filter movements by warehouse could be added here if needed
      }
    }, { allowSignalWrites: true });

    // Effect to reload movements on pagination change
    effect(() => {
      this.loadMovements();
    }, { allowSignalWrites: true });
  }

  async ngOnInit() {
    await this.initDashboard();
  }

  async initDashboard() {
    this.loading.set(true);
    try {
      // 1. Check Readiness first (The Gatekeeper)
      await this.inventoryService.checkReadiness();
      
      // 2. Load Catalogs
      await this.inventoryService.loadCatalogs();
      
      // Auto-select first warehouse if available and none selected
      if (this.physicalWarehouses().length > 0 && !this.selectedWarehouseId()) {
        this.selectedWarehouseId.set(this.physicalWarehouses()[0].id);
      }
      
      // Initial load only if ready
      if (this.inventoryReadiness()?.is_ready) {
        this.refreshAll();
      }
    } catch (error) {
      console.error('Failed to initialize dashboard:', error);
    } finally {
      this.loading.set(false);
    }
  }

  async checkReadiness() {
    this.loading.set(true);
    await this.inventoryService.checkReadiness();
    if (this.inventoryReadiness()?.is_ready) {
      this.refreshAll();
    }
    this.loading.set(false);
  }

  refreshAll() {
    this.loadSummary();
    this.loadMovements();
    this.loadMissionControl();
  }

  loadSummary() {
    this.dashboardService.getSummary().subscribe({
      next: (res) => this.summary.set(res.data),
      error: (err) => console.error('Error fetching summary:', err)
    });
  }

  loadMissionControl() {
    const whId = this.selectedWarehouseId();
    if (!whId) return;

    this.dashboardService.getMissionControl(whId).subscribe({
      next: (res) => this.missionControl.set(res.data),
      error: (err) => console.error('Error fetching mission control:', err)
    });
  }

  loadMovements() {
    this.loading.set(true);
    const offset = (this.currentPage() - 1) * this.pageSize();
    
    this.dashboardService.getMovements(this.pageSize(), offset).pipe(
      finalize(() => this.loading.set(false))
    ).subscribe({
      next: (res) => {
        this.movements.set(res.data || []);
        if (res.meta && res.meta.total_records !== undefined) {
          this.totalRecords.set(res.meta.total_records);
        } else {
          this.totalRecords.set(res.data?.length || 0);
        }
      },
      error: (err) => {
        console.error('Error fetching movements:', err);
        this.movements.set([]);
      }
    });
  }

  onWarehouseChange(event: any) {
    this.selectedWarehouseId.set(event.target.value);
    this.currentPage.set(1); // Reset pagination on filter change
  }

  changePage(newPage: number) {
    if (newPage < 1 || newPage > this.totalPages()) return;
    this.currentPage.set(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  onPageSizeChange(event: any) {
    const newSize = parseInt(event.target.value, 10);
    this.pageSize.set(newSize);
    this.currentPage.set(1);
  }

  onGlobalSearch(item: InventoryItem) {
    console.log('Search details for SKU:', item.sku);
    // Future: dynamic navigation or audit drill-down
  }
}
