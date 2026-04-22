import { Component, signal, OnInit, inject, effect, computed, untracked } from '@angular/core';
import { TranslationService } from '../../core/services/translation.service';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { StatusBadgeComponent } from '../../shared/components/status-badge.component';
import { ItemSearchComponent, InventoryItem } from '../../shared/components/item-search.component';
import { InventoryService } from '../../core/services/inventory.service';
import { AuthService } from '../../core/services/auth.service';
import { Router } from '@angular/router';
import { DashboardDTO, StockAlert, Money, Currency, ValidationStatus } from '../../core/models/domain.types';
import { CurrencyFormatPipe } from '../../shared/pipes/currency-format.pipe';
import { DensityAlertPanelComponent } from './components/density-alert-panel.component';
import { OverflowBadgeComponent } from '../../shared/components/overflow-badge.component';

interface StockWidget {
  warehouse: string;
  code: string;
  totalItems: number;
  value: string;
  valuation?: Money;
  trend: number;
  status: 'GREEN' | 'ORANGE' | 'RED';
}

interface CriticalItem {
  sku: string;
  name: string;
  current: number;
  min: number;
  warehouse: string;
}

@Component({
  selector: 'app-inventory-dashboard',
  standalone: true,
  imports: [CommonModule, MatIconModule, TranslatePipe, StatusBadgeComponent, ItemSearchComponent, CurrencyFormatPipe, DensityAlertPanelComponent, OverflowBadgeComponent],
  template: `
    <div class="space-y-8 animate-fade-in">
      <!-- Header Section -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 class="text-4xl font-black text-surface-text tracking-tighter uppercase italic glow-text">
            {{ 'inventory.dashboard.title' | translate:'Mission Control' }}
          </h1>
          <p class="text-surface-text-muted font-mono text-xs tracking-widest uppercase mt-2">
            {{ 'inventory.dashboard.subtitle' | translate:'Estado de salud de almacenes binacionales' }}
          </p>
        </div>
        
        <div class="flex flex-1 max-w-md">
          <app-item-search (itemSelected)="onGlobalSearch($event)"></app-item-search>
        </div>

        <div class="flex items-center gap-3">
          <button (click)="loadAllWarehouseData([])" class="btn-primary py-2 px-4 text-xs">
            <mat-icon class="text-sm">refresh</mat-icon>
            {{ 'common.refresh' | translate:'Actualizar Datos' }}
          </button>
        </div>
      </div>

      <!-- Stock Widgets -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        @for (widget of stockWidgets(); track widget.code; let i = $index) {
          <div 
            class="industrial-card p-6 group transition-all hover:border-primary/30 cursor-pointer"
            [ngClass]="{'border-primary shadow-[0_0_20px_rgba(var(--primary-rgb),0.2)]': selectedWarehouseId() === (warehouses()[i]?.id)}"
            (click)="selectWarehouse(i)"
          >
            <div class="flex items-start justify-between mb-4">
              <div class="flex flex-col">
                <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">{{ widget.code }}</span>
                <h3 class="text-lg font-bold text-surface-text truncate max-w-[150px]">{{ widget.warehouse }}</h3>
              </div>
              <div 
                class="w-10 h-10 rounded-xl flex items-center justify-center border transition-all duration-500"
                [ngClass]="{
                  'bg-emerald-500/10 border-emerald-500/30 text-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.2)]': widget.status === 'GREEN',
                  'bg-amber-500/10 border-amber-500/30 text-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.2)]': widget.status === 'ORANGE',
                  'bg-red-500/10 border-red-500/30 text-red-500 shadow-[0_0_15px_rgba(239,68,68,0.2)]': widget.status === 'RED'
                }"
              >
                <mat-icon>{{ widget.status === 'GREEN' ? 'check_circle' : widget.status === 'ORANGE' ? 'warning' : 'error' }}</mat-icon>
              </div>
            </div>

            <div class="flex items-baseline gap-2 mb-4">
              <span class="text-3xl font-black text-surface-text tracking-tighter">{{ widget.totalItems | number:'1.1-2' }}</span>
              <span class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest">Items</span>
            </div>

            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1 text-[10px] font-bold" [ngClass]="widget.trend >= 0 ? 'text-emerald-500' : 'text-red-500'">
                <mat-icon class="text-xs w-3 h-3">{{ widget.trend >= 0 ? 'trending_up' : 'trending_down' }}</mat-icon>
                <span>{{ widget.trend >= 0 ? '+' : '' }}{{ widget.trend | number:'1.1-2' }}% vs ayer</span>
              </div>
              <span class="text-[10px] font-mono text-surface-text-muted">{{ widget.valuation ? (widget.valuation.amount | currencyFormat) : (widget.value + ' USD') }}</span>
            </div>
          </div>
        }
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Left Column: Critical Alerts -->
        <div class="lg:col-span-1 space-y-6">
          <div class="industrial-card p-6 h-full">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xs font-black text-surface-text uppercase tracking-[0.2em] flex items-center gap-2">
                <mat-icon class="text-red-500 text-sm">notification_important</mat-icon>
                {{ 'inventory.dashboard.critical_alerts' | translate:'Alertas de Nivel Crítico' }}
              </h2>
              <span class="text-[10px] bg-red-500/20 text-red-500 px-2 py-0.5 rounded-full font-bold border border-red-500/30 animate-pulse">
                {{ criticalItems().length }} ITEMS
              </span>
            </div>

            <div class="space-y-4">
              @for (item of criticalItems(); track item.sku) {
                <div class="p-4 bg-surface-bg/50 border border-surface-border rounded-xl hover:border-red-500/30 transition-all group">
                  <div class="flex items-start justify-between mb-2">
                    <div class="flex flex-col">
                      <span class="text-[9px] font-mono text-red-500 font-bold tracking-widest">{{ item.sku }}</span>
                      <span class="text-xs font-bold text-surface-text group-hover:text-red-400 transition-colors">{{ item.name }}</span>
                    </div>
                    <span class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">{{ item.warehouse }}</span>
                  </div>
                  
                  <div class="flex items-center justify-between mt-3">
                    <div class="flex flex-col">
                      <span class="text-[8px] text-surface-text-muted uppercase font-bold">{{ 'inventory.dashboard.current' | translate:'Actual' }}</span>
                      <span class="text-sm font-black text-red-500">{{ item.current }}</span>
                    </div>
                    <div class="flex flex-col text-right">
                      <span class="text-[8px] text-surface-text-muted uppercase font-bold">{{ 'inventory.dashboard.minimum' | translate:'Mínimo' }}</span>
                      <span class="text-sm font-black text-surface-text">{{ item.min }}</span>
                    </div>
                  </div>
                </div>
              }
            </div>
          </div>

        <!-- Pending Transfers / IN_TRANSIT Badges -->
        <div class="space-y-4">
          <!-- QUICK ACCESS: Handheld Inbound (Industrial Focus) -->
          <div (click)="router.navigate(['/inventory/inbound'])" 
               class="industrial-card p-6 border-primary/30 bg-primary/5 hover:bg-primary/10 cursor-pointer transition-all group">
            <div class="flex items-center justify-between mb-2">
              <div class="flex flex-col">
                <h2 class="text-xs font-black text-primary uppercase tracking-[0.2em] flex items-center gap-2">
                  <mat-icon class="text-sm">qr_code_scanner</mat-icon>
                  Inbound Handheld
                </h2>
                <p class="text-[9px] text-surface-text-muted mt-1 font-mono uppercase">Optimizado para Montacargas</p>
              </div>
              <mat-icon class="text-primary group-hover:translate-x-1 transition-transform">arrow_forward</mat-icon>
            </div>
            <div class="flex items-center gap-3 mt-4">
               <span class="text-[10px] bg-primary/20 text-primary px-2 py-1 rounded border border-primary/30 font-black">F2 FOCUS</span>
               <span class="text-[10px] bg-surface-bg text-surface-text-muted px-2 py-1 rounded border border-surface-border font-black">OFFLINE READY</span>
            </div>
          </div>

          <!-- QUICK ACCESS: Handheld Picking (Outbound) -->
          <div (click)="router.navigate(['/inventory/picking'])" 
               class="industrial-card p-6 border-orange-500/30 bg-orange-500/5 hover:bg-orange-500/10 cursor-pointer transition-all group">
            <div class="flex items-center justify-between mb-2">
              <div class="flex flex-col">
                <h2 class="text-xs font-black text-orange-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <mat-icon class="text-sm">conveyor_belt</mat-icon>
                  Picking Handheld
                </h2>
                <p class="text-[9px] text-surface-text-muted mt-1 font-mono uppercase">Control de Montacargas (Salidas)</p>
              </div>
              <mat-icon class="text-orange-400 group-hover:translate-x-1 transition-transform">arrow_forward</mat-icon>
            </div>
            <div class="flex items-center gap-3 mt-4">
               <span class="text-[10px] bg-orange-500/20 text-orange-400 px-2 py-1 rounded border border-orange-500/30 font-black">FIFO MODE</span>
               <span class="text-[10px] bg-surface-bg text-surface-text-muted px-2 py-1 rounded border border-surface-border font-black">OFFLINE SYNC</span>
            </div>
          </div>

          <!-- QUICK ACCESS: Handheld Put-Away (PRIORITY HIGH) -->
          <div (click)="router.navigate(['/inventory/put-away'])" 
               class="industrial-card p-6 border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10 cursor-pointer transition-all group">
            <div class="flex items-center justify-between mb-2">
              <div class="flex flex-col">
                <h2 class="text-xs font-black text-emerald-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <mat-icon class="text-sm">forklift</mat-icon>
                  Put-Away Handheld
                </h2>
                <p class="text-[9px] text-surface-text-muted mt-1 font-mono uppercase">Re-ubicación (DOCK -> RACK)</p>
              </div>
              <mat-icon class="text-emerald-400 group-hover:translate-x-1 transition-transform">arrow_forward</mat-icon>
            </div>
            <div class="flex items-center gap-3 mt-4">
               <span class="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded border border-emerald-500/30 font-black">3 SCANS</span>
               <span class="text-[10px] bg-surface-bg text-surface-text-muted px-2 py-1 rounded border border-surface-border font-black">ANEXO 24</span>
            </div>
          </div>

          <!-- QUICK ACCESS: Cycle Count / Auditoría Spot (Phase 49) -->
          <div (click)="router.navigate(['/inventory/cycle-count'])" 
               class="industrial-card p-6 border-cyan-500/30 bg-cyan-500/5 hover:bg-cyan-500/10 cursor-pointer transition-all group">
            <div class="flex items-center justify-between mb-2">
              <div class="flex flex-col">
                <h2 class="text-xs font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <mat-icon class="text-sm">fact_check</mat-icon>
                  Auditoría Spot
                </h2>
                <p class="text-[9px] text-surface-text-muted mt-1 font-mono uppercase">Conteo Ciego por Ubicación</p>
              </div>
              <mat-icon class="text-cyan-400 group-hover:translate-x-1 transition-transform">arrow_forward</mat-icon>
            </div>
            <div class="flex items-center gap-3 mt-4">
               <span class="text-[10px] bg-cyan-500/20 text-cyan-400 px-2 py-1 rounded border border-cyan-500/30 font-black">BLIND COUNT</span>
               <span class="text-[10px] bg-surface-bg text-surface-text-muted px-2 py-1 rounded border border-surface-border font-black">SUPERVISOR</span>
            </div>
          </div>

          @if (pendingTransfers().length > 0) {
            <div class="industrial-card p-6 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.1)]">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-xs font-black text-amber-500 uppercase tracking-[0.2em] flex items-center gap-2">
                  <mat-icon class="text-sm">local_shipping</mat-icon>
                  En Tránsito (Espejo)
                </h2>
                <span class="text-[10px] bg-amber-500/20 text-amber-500 px-2 py-0.5 rounded-full font-bold border border-amber-500/30 animate-pulse">
                  {{ pendingTransfers().length }} PENDING
                </span>
              </div>
              <div class="space-y-3">
                @for (transfer of pendingTransfers(); track transfer.id) {
                  <div 
                    (click)="goToReceive(transfer.id)"
                    class="p-4 bg-surface-bg/50 border border-amber-500/20 rounded-xl hover:border-amber-400 hover:bg-amber-500/10 cursor-pointer transition-all group">
                    <div class="flex items-start justify-between mb-2">
                      <div class="flex flex-col">
                        <span class="text-[9px] font-mono text-amber-500 font-bold tracking-widest">{{ transfer.folio }}</span>
                        <span class="text-xs font-bold text-surface-text">{{ 'Desde: ' + (transfer.company_id | slice:0:8) + '...' }}</span>
                      </div>
                    </div>
                    <div class="flex items-center justify-between mt-2">
                      <div class="text-[10px] text-surface-text-muted font-bold flex items-center gap-1">
                        <mat-icon class="text-[10px] w-3 h-3 text-cyan-500">inventory_2</mat-icon>
                        {{ transfer.quantity }} QTY
                      </div>
                      <span class="text-[9px] bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded font-black uppercase">
                        Recibir DRAFT
                      </span>
                    </div>
                  </div>
                }
              </div>
            </div>
          }
        </div>

        <!-- Right Column: Operations Graph & Ledger -->
        <div class="lg:col-span-2 space-y-8">
          
          <!-- God Mode: Density Violation Alerts -->
          <app-density-alert-panel></app-density-alert-panel>

          <!-- Telemetry Graph Placeholder (Simplified) -->
          <div class="industrial-card p-6 min-h-[300px]">
             <div class="flex items-center justify-between mb-8">
              <h2 class="text-xs font-black text-surface-text uppercase tracking-[0.2em] flex items-center gap-2">
                <mat-icon class="text-primary text-sm">analytics</mat-icon>
                {{ 'inventory.dashboard.telemetry' | translate:'Telemetría de Movimientos 24H' }}
              </h2>
            </div>
            
            <div class="flex items-end justify-between h-48 gap-2 px-4">
              @for (point of graphData(); track point.hour) {
                <div class="flex-1 flex flex-col items-center gap-1 group">
                  <div class="w-full flex gap-0.5 justify-center items-end h-32 relative">
                    <div 
                      class="w-2 bg-primary/20 border-t border-primary/50 group-hover:bg-primary/40 transition-all" 
                      [style.height.%]="point.in > 0 ? (point.in / 50) * 100 : 5"
                      [title]="'In: ' + point.in"
                    ></div>
                    <div 
                      class="w-2 bg-orange-500/20 border-t border-orange-500/50 group-hover:bg-orange-500/40 transition-all" 
                      [style.height.%]="point.out > 0 ? (point.out / 50) * 100 : 5"
                      [title]="'Out: ' + point.out"
                    ></div>
                  </div>
                  <span class="text-[8px] text-surface-text-muted font-mono">{{ point.hour }}</span>
                </div>
              }
            </div>
          </div>

          <!-- Recent Movements Ledger -->
          <div class="industrial-card overflow-hidden">
            <div class="p-6 border-b border-surface-border flex items-center justify-between">
              <h2 class="text-xs font-black text-surface-text uppercase tracking-[0.2em]">
                {{ 'inventory.dashboard.ledger' | translate:'Libro Mayor Reciente' }}
              </h2>
              <div class="flex items-center gap-4">
                <input 
                  type="text" 
                  [placeholder]="'common.search' | translate:'Filtrar...'" 
                  (input)="onFilterChange($event)"
                  class="bg-surface-bg border border-surface-border text-[10px] px-3 py-1 rounded-lg focus:outline-none focus:border-primary/50 transition-all w-48 font-mono"
                >
              </div>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs border-collapse">
                <thead class="bg-surface-bg/50 text-surface-text-muted font-black border-b border-surface-border uppercase tracking-widest text-[9px]">
                  <tr>
                    <th (click)="sort('folio')" class="px-6 py-4 cursor-pointer hover:text-primary transition-colors">Folio</th>
                    <th (click)="sort('type')" class="px-6 py-4 cursor-pointer hover:text-primary transition-colors">Tipo</th>
                    <th class="px-6 py-4">Almacén</th>
                    <th (click)="sort('date')" class="px-6 py-4 cursor-pointer hover:text-primary transition-colors text-right">Fecha</th>
                    <th class="px-6 py-4 text-right">Valuación</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-surface-border">
                  @for (m of filteredLedger(); track m.folio) {
                    <tr class="hover:bg-white/[0.02] transition-colors group">
                      <td class="px-6 py-4 font-mono font-bold">
                        <span class="text-primary">{{ m.folio }}</span>
                        <div class="text-[8px] text-surface-text-muted">{{ m.subFolio }}</div>
                      </td>
                      <td class="px-6 py-4">
                        <app-status-badge [status]="m.status" [label]="m.concept_name || m.type"></app-status-badge>
                      </td>
                      <td class="px-6 py-4 text-surface-text-muted italic flex items-center gap-2">
                        {{ m.warehouse }}
                        @if (m.validation_status) {
                          <app-overflow-badge [status]="m.validation_status"></app-overflow-badge>
                        }
                      </td>
                      <td class="px-6 py-4 text-right font-mono text-[10px]">{{ m.date | date:'shortTime' }}</td>
                      <td class="px-6 py-4 text-right font-black">{{ m.valuation.amount | currencyFormat }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .glow-text {
      text-shadow: 0 0 20px rgba(var(--primary-rgb), 0.3);
    }
    .industrial-card {
      background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
      border: 1px solid rgba(255,255,255,0.05);
      border-radius: 20px;
    }
  `]
})
export class InventoryDashboardComponent implements OnInit {
  private inventoryService = inject(InventoryService);
  private auth = inject(AuthService);
  public router = inject(Router);
  protected translationService = inject(TranslationService);
  
  isReady = signal<boolean>(true);
  readinessSteps = signal<any[]>([]);

  selectedWarehouseId = signal<string | null>(null);
  private telemetryData = signal<DashboardDTO[]>([]);

  stockWidgets = computed<StockWidget[]>(() => {
    const data = this.telemetryData();
    const whs = this.inventoryService.warehouses();
    
    return data.map(dto => {
      const whId = dto.meta?.warehouse_id;
      const wh = whs.find(w => w.id === whId);
      const status = dto.critical_alerts.length === 0 ? 'GREEN' : 
                    dto.critical_alerts.length < 5 ? 'ORANGE' : 'RED';
      
      return {
        warehouse: wh?.name || 'Unknown',
        code: wh?.code || 'WH',
        totalItems: Number(dto.valuation?.current_total_stock || 0),
        value: Number(dto.valuation?.total_usd?.amount || 0).toLocaleString(),
        valuation: dto.valuation?.total_usd,
        trend: Number(dto.valuation?.variation_percentage || 0),
        status: status as any
      };
    });
  });

  criticalItems = computed<CriticalItem[]>(() => {
    const allTelemetry = this.telemetryData();
    const selectedId = this.selectedWarehouseId();
    
    let items: CriticalItem[] = [];
    const targets = selectedId ? allTelemetry.filter(t => t.meta?.warehouse_id === selectedId) : allTelemetry;
    
    targets.forEach(dto => {
      const whId = dto.meta?.warehouse_id;
      const wh = this.inventoryService.warehouses().find(w => w.id === whId);
      
      dto.critical_alerts.forEach(a => {
        items.push({
          sku: a.sku,
          name: a.name || 'Industrial Part',
          current: a.current_quantity,
          min: a.min_quantity,
          warehouse: wh?.code || 'WH'
        });
      });
    });
    
    return items;
  });

  graphData = computed(() => {
    const allTelemetry = this.telemetryData();
    const selectedId = this.selectedWarehouseId();
    
    const targets = selectedId ? allTelemetry.filter(t => t.meta?.warehouse_id === selectedId) : allTelemetry;
    
    if (targets.length === 0) return [];
    
    const firstSeries = targets[0].movement_series || [];
    const aggregated = firstSeries.map(s => ({
      hour: new Date(s.hour).getHours().toString().padStart(2, '0') + ':00',
      in: 0,
      out: 0
    }));

    targets.forEach(dto => {
      dto.movement_series?.forEach((s, i) => {
        if (aggregated[i]) {
          aggregated[i].in += Number(s.entries);
          aggregated[i].out += Number(s.exits);
        }
      });
    });

    return aggregated;
  });

  recentLedger = signal<any[]>([]);
  pendingTransfers = signal<any[]>([]);
  filterQuery = signal('');
  sortKey = signal<string>('date');
  sortDir = signal<'asc' | 'desc'>('desc');

  filteredLedger = computed(() => {
    let items = [...this.recentLedger()];
    const query = this.filterQuery().toLowerCase().trim();

    if (query) {
      items = items.filter(item =>
        item.folio.toLowerCase().includes(query) ||
        item.type.toLowerCase().includes(query) ||
        (item.concept_name || '').toLowerCase().includes(query) || // Search by business label
        item.warehouse.toLowerCase().includes(query) ||
        item.status.toLowerCase().includes(query)
      );
    }

    const key = this.sortKey();
    const dir = this.sortDir();

    return items.sort((a: any, b: any) => {
      const valA = a[key] || '';
      const valB = b[key] || '';
      if (valA < valB) return dir === 'asc' ? -1 : 1;
      if (valA > valB) return dir === 'asc' ? 1 : -1;
      return 0;
    });
  });

  isLoading = signal(false);
  private currentLoadedCompanyId: string | null = null;
  warehouses = computed(() => this.inventoryService.warehouses());

  constructor() {
    effect(async () => {
      const whs = this.inventoryService.warehouses();
      const isAuth = this.auth.isAuthenticated();
      const companyId = this.auth.activeCompanyId();

      if (isAuth && companyId && whs.length > 0) {
        if (this.currentLoadedCompanyId === companyId) return;
        this.currentLoadedCompanyId = companyId;

        console.log(`[Dashboard] Syncing Mission Control for ${companyId}...`);
        
        untracked(async () => {
          await this.inventoryService.verifyDemoDataFreshness(companyId);
          await this.checkReadiness();
          await this.loadAllWarehouseData([]);
          await this.loadRecentMovements();
        });
      } else if (!isAuth) {
        this.currentLoadedCompanyId = null;
      }
    });

    // Auto-selection of the first warehouse once data is loaded
    effect(() => {
      const data = this.telemetryData();
      if (data.length > 0 && !this.selectedWarehouseId()) {
        const firstWhId = data[0].meta?.warehouse_id;
        if (firstWhId) {
          console.log(`[Dashboard] Initializing warehouse context: ${firstWhId}`);
          this.selectedWarehouseId.set(firstWhId);
        }
      }
    });
  }

  async ngOnInit() {
    if (this.inventoryService.warehouses().length === 0) {
       await this.inventoryService.loadCatalogs();
    }
    await this.checkReadiness();
  }

  async checkReadiness() {
    try {
      const data = await this.inventoryService.getReadiness();
      this.isReady.set(data?.is_ready ?? true);
      this.readinessSteps.set(data?.steps || []);
    } catch (e) {
      console.error('[Dashboard] Readiness error:', e);
      this.isReady.set(false);
      this.readinessSteps.set([{ name: 'Connection Error', completed: false }]);
    }
  }

  async loadAllWarehouseData(warehouses: any[]) {
    this.isLoading.set(true);
    try {
      const data = await this.inventoryService.getConsolidatedMissionControl();
      this.telemetryData.set(data);
      
      // Load pending inbound transfers
      const pendingInfo = await this.inventoryService.getPendingInboundTransfers();
      this.pendingTransfers.set(pendingInfo || []);
    } catch (error) {
      console.error('❌ Consolidated telemetry fail:', error);
    } finally {
      this.isLoading.set(false);
    }
  }

  selectWarehouse(index: number) {
    const data = this.telemetryData();
    const targetId = data[index]?.meta?.warehouse_id;
    if (this.selectedWarehouseId() === targetId) {
      this.selectedWarehouseId.set(null);
    } else {
      this.selectedWarehouseId.set(targetId);
    }
  }

  async loadRecentMovements() {
    try {
      this.isLoading.set(true);
      const movements = await this.inventoryService.getMovements(20);
      this.recentLedger.set(movements.map((m: any) => ({
        folio: m.folio,
        subFolio: m.id.split('-')[0].toUpperCase(),
        date: m.date,
        /** Technical type (ENTRY, EXIT, TRANSFER) — used as fallback */
        type: this.translationService.translate('inventory.type.' + m.type.toLowerCase(), m.type),
        /** Business concept name — preferred for display ("Recepción de Compra") */
        concept_name: m.concept_name || null,
        concept_id: m.concept_id || null,
        warehouse: m.type === 'TRANSFER' ? `${m.origin} -> ${m.destination}` : (m.type === 'ENTRY' ? m.destination : m.origin),
        status: m.status || 'PROCESSED',
        validation_status: m.validation_status,
        valuation: m.total_valuation || { amount: 0, currency: 'USD' }
      })));
    } catch (e) {
      console.error('[Dashboard] Ledger load fail:', e);
    } finally {
      this.isLoading.set(false);
    }
  }

  sort(key: string) {
    if (this.sortKey() === key) {
      this.sortDir.set(this.sortDir() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortKey.set(key);
      this.sortDir.set('desc');
    }
  }

  onFilterChange(event: Event) {
    const input = event.target as HTMLInputElement;
    this.filterQuery.set(input.value);
  }

  onGlobalSearch(item: InventoryItem) {
    alert(`Searching details for: ${item.name} (${item.sku})`);
  }

  goToCatalogs() {
    this.router.navigate(['/catalog']);
  }

  goToReceive(transferId: string) {
    this.router.navigate(['/inventory/receive'], { queryParams: { transfer_id: transferId } });
  }
}
