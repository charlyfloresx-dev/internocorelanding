import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, Subscription } from 'rxjs';
import { InventoryService } from '../../core/services/inventory.service';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { LocalDatePipe } from '../../shared/pipes/local-date.pipe';

@Component({
  selector: 'app-stock-level',
  standalone: true,
  imports: [CommonModule, TranslatePipe, FormsModule, LocalDatePipe],
  template: `
    <div class="p-6 h-full flex flex-col bg-slate-50 relative">
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <div>
          <h1 class="text-2xl font-bold text-slate-800 tracking-tight">
            {{ 'inventory.stock.title' | translate:'Stock por Almacén' }}
          </h1>
          <p class="text-slate-500 mt-1">
            {{ 'inventory.stock.compliance_view' | translate:'Vista de Cumplimiento Binacional (Anexo 24)' }}
          </p>
        </div>
        
        <div class="flex items-center gap-3 w-full md:w-auto">
          <div class="flex items-center gap-2 mr-2">
            <span class="text-xs font-bold text-slate-400 uppercase tracking-tighter">Exportar:</span>
            <button 
              class="flex items-center gap-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 px-3 py-2 rounded-lg text-xs font-bold transition-all border border-emerald-200 shadow-sm"
              (click)="downloadAuditSheet()"
              [disabled]="loading"
            >
              <i class="material-icons text-sm">download</i>
              {{ 'inventory.stock.export_audit' | translate:'Hoja de Conteo' }}
            </button>
          </div>

          <div class="relative flex-grow md:w-64">
            <i class="material-icons absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">search</i>
            <input 
              type="text" 
              [(ngModel)]="searchQuery"
              (ngModelChange)="onSearchInputChange()"
              placeholder="Buscar SKU o Pedimento..." 
              class="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all bg-white"
            >
          </div>
          <button class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm whitespace-nowrap" (click)="loadStock()">
            <i class="material-icons text-[18px] align-middle mr-1">refresh</i>
            Actualizar
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading" class="absolute inset-0 z-50 flex items-center justify-center bg-white/50 backdrop-blur-sm rounded-xl">
        <div class="flex flex-col items-center">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
          <span class="text-slate-600 font-medium font-mono text-xs">INDUSTRIAL_LATENCY_EMULATION_LOAD...</span>
        </div>
      </div>

      <div class="flex-grow bg-white rounded-xl shadow-sm border border-slate-200 overflow-auto">
        <table class="w-full text-left text-sm text-slate-600">
          <thead class="bg-slate-50 border-b border-slate-200 text-slate-700 sticky top-0 z-10">
            <tr>
              <th class="px-6 py-4 font-semibold uppercase tracking-wider text-[11px] text-slate-400">SKU</th>
              <th class="px-6 py-4 font-semibold uppercase tracking-wider text-[11px] text-slate-400">Producto</th>
              <th class="px-6 py-4 font-semibold uppercase tracking-wider text-[11px] text-slate-400">
                {{ 'inventory.stock.pedimento' | translate:'Pedimento' }}
              </th>
              <th class="px-6 py-4 font-semibold uppercase tracking-wider text-[11px] text-slate-400 text-right">
                {{ 'inventory.stock.available_qty' | translate:'Disponible' }}
              </th>
              <th class="px-6 py-4 font-semibold uppercase tracking-wider text-[11px] text-slate-400">Vencimiento</th>
              <th class="px-6 py-4 font-semibold uppercase tracking-wider text-[11px] text-slate-400 text-center">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr *ngFor="let item of stockData" class="hover:bg-indigo-50/30 transition-colors">
              <td class="px-6 py-4 font-mono text-xs font-semibold text-slate-800">{{ item.sku }}</td>
              <td class="px-6 py-4">
                <div class="flex flex-col">
                  <span class="font-medium text-slate-900">{{ item.product_name }}</span>
                  <span class="text-[11px] text-slate-400 uppercase font-mono">{{ item.item_id | slice:0:8 }}</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <i class="material-icons text-slate-300 text-xs">description</i>
                  <span class="font-mono text-xs">{{ item.pedimento_number }}</span>
                </div>
              </td>
              <td class="px-6 py-4 font-bold text-right tabular-nums text-slate-900" [ngClass]="{'text-red-600': (item.total_available_qty || 0) <= 0}">
                {{ item.total_available_qty | number:'1.0-2' }}
              </td>
              <td class="px-6 py-4">
                <div class="flex flex-col">
                  <span class="text-xs font-medium">{{ item.expiry_date ? (item.expiry_date | localDate:'dd/MM/yyyy') : 'N/A' }}</span>
                  <span *ngIf="item.days_to_expiry !== null" class="text-[10px]" [ngClass]="item.is_at_risk ? 'text-red-500 font-bold' : 'text-slate-400'">
                    {{ item.days_to_expiry }} días restantes
                  </span>
                </div>
              </td>
              <td class="px-6 py-4 text-center">
                <span 
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider shadow-sm"
                  [ngClass]="{
                    'bg-red-100 text-red-700 border border-red-200': item.is_at_risk,
                    'bg-emerald-100 text-emerald-700 border border-emerald-200': !item.is_at_risk && (item.total_available_qty || 0) > 0,
                    'bg-slate-100 text-slate-700 border border-slate-200': (item.total_available_qty || 0) <= 0
                  }"
                >
                  {{ item.is_at_risk ? 'Riesgo' : (item.total_available_qty > 0 ? 'Conforme' : 'Agotado') }}
                </span>
              </td>
            </tr>
            <tr *ngIf="!loading && stockData.length === 0">
              <td colspan="6" class="px-6 py-20 text-center">
                <div class="flex flex-col items-center gap-2">
                  <i class="material-icons text-slate-300 text-4xl">inventory_2</i>
                  <span class="text-slate-500 font-medium">No se encontraron registros de inventario.</span>
                  <p class="text-xs text-slate-400">Intenta con otro término de búsqueda o ajusta los filtros.</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Footer -->
      <div class="mt-4 flex flex-col sm:flex-row justify-between items-center bg-white p-3 rounded-lg border border-slate-200 shadow-sm gap-4">
        <div class="text-xs text-slate-500 font-medium">
          Mostrando <span class="text-slate-900 font-bold">{{ stockData.length }}</span> de <span class="text-slate-900 font-bold">{{ totalCount }}</span> registros industriales
        </div>
        
        <div class="flex items-center gap-2">
          <button 
            [disabled]="currentPage === 0 || loading"
            (click)="goToPage(currentPage - 1)"
            class="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-30 disabled:hover:bg-transparent transition-all"
          >
            <i class="material-icons text-sm">chevron_left</i>
          </button>
          
          <div class="flex items-center gap-1">
            <span class="text-xs text-slate-400">Página</span>
            <span class="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-md text-xs font-bold">{{ currentPage + 1 }}</span>
          </div>

          <button 
            [disabled]="isLastPage() || loading"
            (click)="goToPage(currentPage + 1)"
            class="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-30 disabled:hover:bg-transparent transition-all"
          >
            <i class="material-icons text-sm">chevron_right</i>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; height: 100%; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #cbd5e1; }
  `]
})
export class StockLevelComponent implements OnInit, OnDestroy {
  private inventoryService = inject(InventoryService);
  
  stockData: any[] = [];
  loading = false;
  
  // Industrial Scalability State
  searchQuery = '';
  private searchSubject = new Subject<string>();
  private searchSubscription?: Subscription;

  totalCount = 0;
  pageSize = 50;
  currentPage = 0;

  ngOnInit() {
    this.loadStock();

    // Technical debounce for Industrial Handheld Scanners
    this.searchSubscription = this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged()
    ).subscribe(() => {
      this.onSearch();
    });
  }

  ngOnDestroy() {
    this.searchSubscription?.unsubscribe();
  }

  onSearchInputChange() {
    this.searchSubject.next(this.searchQuery);
  }

  async loadStock() {
    try {
      this.loading = true;
      const offset = this.currentPage * this.pageSize;
      const response = await this.inventoryService.getCustomsBalances(
        undefined, 
        this.pageSize, 
        offset, 
        this.searchQuery
      );
      
      console.log('[StockLevel] 📦 API Raw Payload:', response);

      // --- RESILIENT PARSING (Phase 48.2) ---
      // Distinguishes between direct data array and wrapped microservice response objects
      const rawData = response.data || response;
      
      if (Array.isArray(rawData)) {
        // Option A: Standard Flat ApiResponse<T[]>
        this.stockData = rawData;
        this.totalCount = response.total_count || rawData.length;
      } else if (rawData && typeof rawData === 'object' && Array.isArray((rawData as any).data)) {
        // Option B: Double-Wrapped Microservice Response { status, data: { data: [], total_count } }
        const wrapped = rawData as any;
        this.stockData = wrapped.data;
        this.totalCount = wrapped.total_count || wrapped.data.length;
      } else {
        // Option C: Empty or Malformed
        console.warn('[StockLevel] ⚠️ Unexpected response format:', rawData);
        this.stockData = [];
        this.totalCount = 0;
      }
    } catch (e) {
      console.error('[StockLevel] Error loading audit balances:', e);
      this.stockData = [];
      this.totalCount = 0;
    } finally {
      this.loading = false;
    }
  }

  onSearch() {
    this.currentPage = 0;
    this.loadStock();
  }

  goToPage(page: number) {
    this.currentPage = page;
    this.loadStock();
  }

  isLastPage(): boolean {
    return (this.currentPage + 1) * this.pageSize >= this.totalCount;
  }

  /**
   * [Phase 49] Downloads the detailed stock CSV for floor audit.
   */
  downloadAuditSheet() {
    const warehouses = this.inventoryService.warehouses();
    const warehouseId = warehouses[0]?.id; // Default to first warehouse
    
    if (!warehouseId) {
      console.warn('[StockLevel] No se encontró almacén activo para exportar.');
      return;
    }

    this.loading = true;
    this.inventoryService.exportAuditCsv(warehouseId).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Audit_Sheet_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        this.playSuccessBeep();
        this.loading = false;
      },
      error: (err) => {
        console.error('[StockLevel] Error al exportar hoja de auditoría:', err);
        this.loading = false;
      }
    });
  }

  private playSuccessBeep() {
    try {
      const context = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = context.createOscillator();
      const gain = context.createGain();
      
      osc.type = 'square';
      osc.frequency.setValueAtTime(880, context.currentTime); // High pitch success
      
      gain.gain.setValueAtTime(0.1, context.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.2);
      
      osc.connect(gain);
      gain.connect(context.destination);
      
      osc.start();
      osc.stop(context.currentTime + 0.2);
    } catch (e) {
      console.warn('[Audio] Beep failed:', e);
    }
  }
}
