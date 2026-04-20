import {
  Component, signal, inject, OnInit, computed, HostListener, ViewChild, ElementRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { InventoryService } from '../../core/services/inventory.service';
import { InventoryRegistryService } from '../../core/services/inventory-registry.service';
import { ToastService } from '../../core/services/toast.service';
import { AuthService } from '../../core/services/auth.service';

// ─── Industrial Audio Feedback (Ported from Put-Away) ───────────────────────
function playIndustrialBeep(frequency: number = 200, duration: number = 0.3) {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    const now = ctx.currentTime;
    osc.frequency.setValueAtTime(frequency, now);
    osc.type = 'square';
    gain.gain.setValueAtTime(0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
    osc.start(now); osc.stop(now + duration);
  } catch (e) {}
}

// ─── Scanner Data Hygiene (Legacy Port: InternoExtensions.getNumber) ────────
function sanitizeScannerInput(raw: string): string {
  return raw.replace(/[^a-zA-Z0-9\-_]/g, '').trim().toUpperCase();
}

interface ScannedItem {
  sku: string;
  productName: string;
  productId: string;
  scannedQty: number;
}

interface DiscrepancyRow {
  sku: string;
  productName: string;
  productId: string;
  theoretical: number;
  counted: number;
  difference: number;
  percentVariance: number;
  status: 'MATCH' | 'SURPLUS' | 'SHORTAGE';
}

@Component({
  selector: 'app-cycle-count',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="min-h-screen bg-surface-bg text-surface-text font-mono select-none overflow-hidden flex flex-col">
      
      <!-- ── INDUSTRIAL HEADER ─────────────────────────────────────────── -->
      <div class="sticky top-0 z-30 bg-surface-card border-b-2 border-cyan-500/50 px-4 py-4 flex items-center justify-between shadow-2xl">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center border border-cyan-500/30">
            <mat-icon class="text-cyan-400">fact_check</mat-icon>
          </div>
          <div>
            <h1 class="text-sm font-black uppercase tracking-widest text-cyan-400">Auditoría Spot</h1>
            <p class="text-[9px] text-surface-text-muted uppercase tracking-tighter">{{ activeWarehouseName() || 'Cycle Count Mode' }}</p>
          </div>
        </div>
        <div class="text-right">
          <span class="text-[10px] font-black text-cyan-400 uppercase tracking-widest">PASO {{ currentStep() }} DE 3</span>
          <div class="mt-1 flex gap-1 justify-end">
             <div *ngFor="let i of [1,2,3]" 
                  [class.bg-cyan-500]="currentStep() >= i" [class.bg-surface-border]="currentStep() < i"
                  class="w-4 h-1 rounded-full transition-all"></div>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto px-4 py-6 space-y-6 max-w-4xl mx-auto w-full">

        <!-- ── STEP 1: SCAN LOCATION ───────────────────────────────────── -->
        <div *ngIf="currentStep() === 1" class="space-y-4 animate-fade-in">
          <div class="bg-surface-card border-2 border-cyan-500/20 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
             <div class="absolute -right-4 -top-4 opacity-5">
              <mat-icon class="text-9xl">location_searching</mat-icon>
            </div>
            
            <label class="text-[10px] uppercase tracking-[0.3em] text-cyan-400/70 font-black mb-4 block">
              PASO 1: Escanear Ubicación a Auditar
            </label>
            
            <div class="space-y-4 relative z-10">
              <input
                #locationInput
                [(ngModel)]="locationScan"
                (keydown.enter)="processLocation()"
                placeholder="RACK-X-XX"
                class="w-full bg-surface-bg border-2 border-surface-border rounded-xl px-4 py-6 text-2xl font-black text-cyan-400 placeholder-white/5 outline-none focus:border-cyan-500 transition-all text-center tracking-widest uppercase"
                autocomplete="off"
                autofocus
              />
              
              <div class="p-4 bg-cyan-500/5 rounded-xl border border-cyan-500/10">
                <p class="text-[9px] text-cyan-400/50 font-black uppercase leading-relaxed text-center">
                  Escanee la etiqueta del rack que desea auditar. El sistema bloqueará la vista a esa ubicación.
                </p>
              </div>

              <button 
                (click)="processLocation()"
                [disabled]="!locationScan || isLoading()"
                class="w-full py-4 rounded-xl bg-cyan-500 text-black font-black uppercase tracking-widest shadow-lg active:scale-95 transition-all disabled:opacity-30 flex items-center justify-center gap-2">
                <mat-icon>lock</mat-icon>
                <span>Bloquear Ubicación</span>
              </button>
            </div>
          </div>

          <!-- Quick Stats -->
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-surface-card rounded-xl p-4 border border-surface-border">
              <p class="text-[8px] text-surface-text-muted uppercase font-black">Conteos Hoy</p>
              <p class="text-2xl font-black text-cyan-400">{{ completedCounts() }}</p>
            </div>
            <div class="bg-surface-card rounded-xl p-4 border border-surface-border">
              <p class="text-[8px] text-surface-text-muted uppercase font-black">Discrepancias</p>
              <p class="text-2xl font-black" [class.text-red-400]="discrepancyCount() > 0" [class.text-emerald-400]="discrepancyCount() === 0">{{ discrepancyCount() }}</p>
            </div>
          </div>
        </div>

        <!-- ── STEP 2: BLIND COUNT ─────────────────────────────────────── -->
        <div *ngIf="currentStep() === 2" class="space-y-4 animate-fade-in">
          
          <!-- Locked Location Banner -->
          <div class="bg-surface-bg/60 rounded-xl p-4 border-2 border-cyan-500/30 flex items-center gap-4">
            <div class="w-12 h-12 rounded-lg bg-cyan-500/10 flex items-center justify-center shrink-0">
              <mat-icon class="text-cyan-400">pin_drop</mat-icon>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-[9px] text-surface-text-muted font-black uppercase">Ubicación Bloqueada</p>
              <p class="text-xl font-black text-cyan-400 truncate">{{ lockedLocation() }}</p>
            </div>
            <button (click)="resetFlow()" class="text-[9px] text-surface-text-muted font-black uppercase hover:text-red-400 transition-colors">
              <mat-icon class="text-sm">close</mat-icon>
            </button>
          </div>

          <!-- Scan Item Input -->
          <div class="bg-surface-card border-2 border-cyan-500/20 rounded-2xl p-6 shadow-2xl">
            <label class="text-[10px] uppercase tracking-[0.3em] text-cyan-400/70 font-black mb-4 block">
              PASO 2: Escanear Items (Conteo Ciego)
            </label>

            <div class="flex gap-3">
              <input
                #itemInput
                [(ngModel)]="itemScan"
                (keydown.enter)="processItemScan()"
                placeholder="ESCANEAR SKU..."
                class="flex-1 bg-surface-bg border-2 border-surface-border rounded-xl px-4 py-4 text-lg font-black text-cyan-400 placeholder-white/5 outline-none focus:border-cyan-500 transition-all uppercase"
                autocomplete="off"
              />
              <button 
                (click)="processItemScan()"
                class="px-4 bg-cyan-500/20 border border-cyan-500/30 rounded-xl text-cyan-400 font-black active:scale-95 transition-all">
                <mat-icon>add</mat-icon>
              </button>
            </div>

            <!-- Item with qty adjustment -->
            <div *ngIf="lastScannedItem()" class="mt-4 bg-surface-bg/40 rounded-xl p-4 border border-surface-border flex items-center gap-3">
              <mat-icon class="text-cyan-400">inventory_2</mat-icon>
              <div class="flex-1 min-w-0">
                <p class="text-[10px] text-surface-text font-bold truncate">{{ lastScannedItem()?.productName }}</p>
                <p class="text-[8px] text-cyan-400/60 font-black uppercase">{{ lastScannedItem()?.sku }}</p>
              </div>
              <div class="flex items-center gap-1 bg-surface-bg rounded-lg border border-surface-border p-1">
                <button (click)="adjustLastQty(-1)" class="w-8 h-8 rounded-md bg-surface-border flex items-center justify-center text-surface-text-muted hover:bg-surface-border active:scale-90">
                  <mat-icon class="text-sm">remove</mat-icon>
                </button>
                <span class="px-3 text-lg font-black text-cyan-400 min-w-[40px] text-center">{{ lastScannedItem()?.scannedQty }}</span>
                <button (click)="adjustLastQty(1)" class="w-8 h-8 rounded-md bg-surface-border flex items-center justify-center text-surface-text-muted hover:bg-surface-border active:scale-90">
                  <mat-icon class="text-sm">add</mat-icon>
                </button>
              </div>
            </div>
          </div>

          <!-- Blind Counter (No theoretical data shown!) -->
          <div class="bg-surface-card rounded-2xl p-6 border border-surface-border text-center">
            <p class="text-[9px] text-surface-text-muted font-black uppercase tracking-widest">Modo Ciego Activo</p>
            <div class="mt-3 flex items-end justify-center gap-2">
              <span class="text-6xl font-black text-cyan-400 tabular-nums leading-none">{{ totalScannedItems() }}</span>
              <span class="text-surface-text-muted text-lg font-black uppercase mb-1">items</span>
            </div>
            <p class="text-[8px] text-surface-text-muted mt-3 uppercase">{{ scannedItems().length }} SKUs únicos contados</p>
            
            <div class="mt-4 w-full h-1 bg-surface-border rounded-full overflow-hidden">
              <div class="h-full bg-cyan-500 transition-all duration-500 animate-pulse" 
                   [style.width.%]="Math.min(100, totalScannedItems() * 2)"></div>
            </div>
          </div>

          <!-- Scanned Items List -->
          <div *ngIf="scannedItems().length > 0" class="bg-surface-card rounded-2xl border border-surface-border overflow-hidden">
            <div class="p-3 border-b border-surface-border flex items-center justify-between">
              <span class="text-[9px] text-surface-text-muted font-black uppercase">Items Escaneados</span>
              <button (click)="clearScannedItems()" class="text-[9px] text-red-400/50 font-black uppercase hover:text-red-400">Limpiar</button>
            </div>
            <div class="max-h-48 overflow-y-auto">
              <div *ngFor="let item of scannedItems(); let i = index" 
                   class="px-4 py-3 border-b border-surface-border flex items-center justify-between hover:bg-surface-border transition-colors">
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-bold text-surface-text truncate">{{ item.sku }}</p>
                  <p class="text-[8px] text-surface-text-muted truncate">{{ item.productName }}</p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-sm font-black text-cyan-400 tabular-nums">×{{ item.scannedQty }}</span>
                  <button (click)="removeScannedItem(i)" class="w-6 h-6 rounded flex items-center justify-center text-surface-text-muted hover:text-red-400 transition-colors">
                    <mat-icon class="text-sm">close</mat-icon>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Finish Counting Button -->
          <button 
            (click)="finishCounting()"
            [disabled]="isLoading()"
            class="w-full py-5 rounded-2xl bg-gradient-to-r from-cyan-600 to-cyan-500 text-black font-black uppercase tracking-widest shadow-lg active:scale-95 transition-all text-lg flex items-center justify-center gap-3">
            <mat-icon>assignment_turned_in</mat-icon>
            <span>Finalizar Conteo</span>
          </button>
        </div>

        <!-- ── STEP 3: DISCREPANCY ANALYSIS ────────────────────────────── -->
        <div *ngIf="currentStep() === 3" class="space-y-4 animate-fade-in">
          
          <!-- Result Banner -->
          <div class="rounded-2xl p-6 border-2 text-center"
               [class.bg-emerald-500/5]="!hasSignificantDiscrepancy()" 
               [class.border-emerald-500/30]="!hasSignificantDiscrepancy()"
               [class.bg-red-500/5]="hasSignificantDiscrepancy()" 
               [class.border-red-500/30]="hasSignificantDiscrepancy()">
            <mat-icon class="text-6xl mb-2" 
                      [class.text-emerald-400]="!hasSignificantDiscrepancy()"
                      [class.text-red-400]="hasSignificantDiscrepancy()">
              {{ hasSignificantDiscrepancy() ? 'warning' : 'verified' }}
            </mat-icon>
            <h2 class="text-lg font-black uppercase tracking-tighter" 
                [class.text-emerald-400]="!hasSignificantDiscrepancy()"
                [class.text-red-400]="hasSignificantDiscrepancy()">
              {{ hasSignificantDiscrepancy() ? 'Discrepancia Detectada' : 'Inventario Verificado' }}
            </h2>
            <p class="text-[9px] text-surface-text-muted mt-2 uppercase">
              Ubicación {{ lockedLocation() }} · {{ todayLabel }}
            </p>
          </div>

          <!-- Discrepancy Table -->
          <div class="bg-surface-card rounded-2xl border border-surface-border overflow-hidden">
            <div class="p-3 border-b border-surface-border">
              <span class="text-[9px] text-surface-text-muted font-black uppercase">Análisis de Discrepancias</span>
            </div>
            
            <div class="overflow-x-auto">
              <table class="w-full text-left">
                <thead>
                  <tr class="border-b border-surface-border">
                    <th class="px-3 py-2 text-[8px] text-surface-text-muted font-black uppercase">SKU</th>
                    <th class="px-3 py-2 text-[8px] text-surface-text-muted font-black uppercase text-right">Teórico</th>
                    <th class="px-3 py-2 text-[8px] text-surface-text-muted font-black uppercase text-right">Contado</th>
                    <th class="px-3 py-2 text-[8px] text-surface-text-muted font-black uppercase text-right">Diff</th>
                    <th class="px-3 py-2 text-[8px] text-surface-text-muted font-black uppercase text-center">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  <tr *ngFor="let row of discrepancyReport()" class="border-b border-surface-border last:border-0">
                    <td class="px-3 py-3">
                      <p class="text-xs font-bold text-surface-text">{{ row.sku }}</p>
                      <p class="text-[8px] text-surface-text-muted truncate max-w-[120px]">{{ row.productName }}</p>
                    </td>
                    <td class="px-3 py-3 text-xs font-bold text-surface-text-muted text-right tabular-nums">{{ row.theoretical }}</td>
                    <td class="px-3 py-3 text-xs font-bold text-cyan-400 text-right tabular-nums">{{ row.counted }}</td>
                    <td class="px-3 py-3 text-xs font-black text-right tabular-nums"
                        [class.text-emerald-400]="row.difference === 0"
                        [class.text-red-400]="row.difference < 0"
                        [class.text-amber-400]="row.difference > 0">
                      {{ row.difference > 0 ? '+' : '' }}{{ row.difference }}
                    </td>
                    <td class="px-3 py-3 text-center">
                      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[8px] font-black uppercase"
                            [class.bg-emerald-500/20]="row.status === 'MATCH'" [class.text-emerald-400]="row.status === 'MATCH'"
                            [class.bg-red-500/20]="row.status === 'SHORTAGE'" [class.text-red-400]="row.status === 'SHORTAGE'"
                            [class.bg-amber-500/20]="row.status === 'SURPLUS'" [class.text-amber-400]="row.status === 'SURPLUS'">
                        {{ row.status === 'MATCH' ? 'OK' : row.status === 'SHORTAGE' ? 'Faltante' : 'Sobrante' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Supervisor Override Notice -->
          <div *ngIf="hasSignificantDiscrepancy() && !isSupervisor()" 
               class="bg-amber-500/10 border-2 border-amber-500/30 rounded-2xl p-4 flex items-start gap-3">
            <mat-icon class="text-amber-400 shrink-0 mt-0.5">admin_panel_settings</mat-icon>
            <div>
              <p class="text-xs font-bold text-amber-400">Autorización Requerida</p>
              <p class="text-[9px] text-surface-text-muted mt-1 leading-relaxed">
                Discrepancia superior al 5%. Se requiere confirmación de un supervisor para aplicar el ajuste de inventario.
              </p>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex flex-col gap-3">
            <button 
              (click)="confirmCycleCount()"
              [disabled]="isProcessing() || (hasSignificantDiscrepancy() && !isSupervisor())"
              class="w-full py-5 rounded-2xl font-black uppercase tracking-widest shadow-lg active:scale-95 transition-all flex items-center justify-center gap-3 disabled:opacity-30"
              [class.bg-emerald-500]="!hasSignificantDiscrepancy()"
              [class.text-black]="!hasSignificantDiscrepancy()"
              [class.bg-red-500]="hasSignificantDiscrepancy()"
              [class.text-surface-text]="hasSignificantDiscrepancy()">
              <mat-icon>{{ hasSignificantDiscrepancy() ? 'gavel' : 'check_circle' }}</mat-icon>
              <span>{{ hasSignificantDiscrepancy() ? 'Confirmar Ajuste (Supervisor)' : 'Verificar Ubicación' }}</span>
            </button>
            
            <button 
              (click)="resetFlow()"
              class="w-full py-3 rounded-xl bg-surface-border text-surface-text-muted font-bold uppercase text-xs tracking-widest hover:bg-surface-border transition-all">
              <mat-icon class="text-sm align-middle mr-1">refresh</mat-icon>
              Nuevo Conteo
            </button>
          </div>
        </div>
      </div>

      <!-- Loading Overlay -->
      <div *ngIf="isLoading()" class="fixed inset-0 z-50 bg-surface-bg/80 flex items-center justify-center">
        <div class="flex flex-col items-center gap-4">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
          <span class="text-[9px] text-cyan-400 font-black uppercase tracking-widest">Procesando...</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; height: 100%; }
    .animate-fade-in {
      animation: fadeIn 0.3s ease-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
  `]
})
export class CycleCountComponent implements OnInit {
  private inv = inject(InventoryService);
  private registry = inject(InventoryRegistryService);
  private toast = inject(ToastService);
  private auth = inject(AuthService);

  // Expose Math for template
  Math = Math;
  todayLabel = new Date().toLocaleDateString();

  @ViewChild('locationInput') locationInput!: ElementRef;
  @ViewChild('itemInput') itemInput!: ElementRef;

  // ─── Flow State ───────────────────────────────────────────────────────────
  currentStep = signal(1);
  isLoading = signal(false);
  isProcessing = signal(false);
  
  // Step 1: Location
  locationScan = '';
  lockedLocation = signal('');
  
  // Step 2: Blind Count
  itemScan = '';
  scannedItems = signal<ScannedItem[]>([]);
  lastScannedItem = signal<ScannedItem | null>(null);
  
  // Step 3: Discrepancy
  discrepancyReport = signal<DiscrepancyRow[]>([]);
  theoreticalStock = signal<any[]>([]);

  // Session Stats
  completedCounts = signal(0);
  discrepancyCount = signal(0);

  // Computed
  totalScannedItems = computed(() => 
    this.scannedItems().reduce((sum, item) => sum + item.scannedQty, 0)
  );

  hasSignificantDiscrepancy = computed(() => 
    this.discrepancyReport().some(r => Math.abs(r.percentVariance) > 5)
  );

  activeWarehouseName = computed(() => {
    const warehouses = this.inv.warehouses();
    return warehouses[0]?.name || null;
  });

  isSupervisor = computed(() => {
    const session = (this.auth as any).currentSession?.() || (this.auth as any).session?.();
    if (!session) return false;
    const roles = session.roles || [];
    return roles.some((r: any) => 
      r === 'admin' || r === 'supervisor' || 
      (typeof r === 'object' && (r.name === 'admin' || r.name === 'supervisor'))
    );
  });

  async ngOnInit() {
    // Ensure the registry cache is hydrated for O(1) lookups
    await this.registry.hydrate();
    
    // Load session stats from storage
    const today = new Date().toISOString().slice(0, 10);
    const stats = JSON.parse(localStorage.getItem(`cc_stats_${today}`) || '{"counts":0,"discrepancies":0}');
    this.completedCounts.set(stats.counts);
    this.discrepancyCount.set(stats.discrepancies);
  }

  // ─── STEP 1: Lock Location ────────────────────────────────────────────────
  async processLocation() {
    const raw = sanitizeScannerInput(this.locationScan);
    if (!raw || raw.length < 3) {
      this.toast.warning('Etiqueta de ubicación inválida. Mínimo 3 caracteres.', 'Validación');
      playIndustrialBeep(200, 0.4);
      return;
    }

    this.isLoading.set(true);
    try {
      const warehouseId = this.inv.warehouses()[0]?.id;
      if (!warehouseId) {
        this.toast.error('No se encontró almacén activo.', 'Error');
        return;
      }

      // Fetch theoretical stock for this location via customs balances (filtered by location code)
      const stockResponse = await this.inv.getCustomsBalances(warehouseId, 500, 0, raw);
      
      const rawData = stockResponse.data || stockResponse;
      let items: any[] = [];
      
      if (Array.isArray(rawData)) {
        items = rawData;
      } else if (rawData && typeof rawData === 'object' && Array.isArray((rawData as any).data)) {
        items = (rawData as any).data;
      }

      this.theoreticalStock.set(items);
      this.lockedLocation.set(raw);
      
      playIndustrialBeep(880, 0.15);
      this.toast.success(`Ubicación ${raw} bloqueada para auditoría.`, 'Conteo Ciego');
      this.currentStep.set(2);
      
      setTimeout(() => this.itemInput?.nativeElement?.focus(), 100);
    } catch (e) {
      this.toast.error('Error al cargar stock teórico de la ubicación.', 'Sync Error');
      playIndustrialBeep(200, 0.5);
    } finally {
      this.isLoading.set(false);
    }
  }

  // ─── STEP 2: Blind Item Scanning ──────────────────────────────────────────
  processItemScan() {
    const raw = sanitizeScannerInput(this.itemScan);
    if (!raw) return;

    // Validate against Registry Cache (O(1) lookup)
    const product = this.registry.getProductBySku(raw);
    
    if (!product) {
      this.toast.warning(`SKU "${raw}" no existe en el catálogo.`, 'SKU Desconocido');
      playIndustrialBeep(200, 0.3);
      this.itemScan = '';
      return;
    }

    // Check if already scanned — increment qty
    const current = this.scannedItems();
    const existingIndex = current.findIndex(i => i.sku === (product.sku || raw));
    
    if (existingIndex >= 0) {
      const updated = [...current];
      updated[existingIndex] = {
        ...updated[existingIndex],
        scannedQty: updated[existingIndex].scannedQty + 1
      };
      this.scannedItems.set(updated);
      this.lastScannedItem.set(updated[existingIndex]);
    } else {
      const newItem: ScannedItem = {
        sku: product.sku || raw,
        productName: product.name || raw,
        productId: product.id,
        scannedQty: 1
      };
      this.scannedItems.set([...current, newItem]);
      this.lastScannedItem.set(newItem);
    }

    playIndustrialBeep(660, 0.1); // Short confirmation beep
    this.itemScan = '';
    
    setTimeout(() => this.itemInput?.nativeElement?.focus(), 50);
  }

  adjustLastQty(delta: number) {
    const last = this.lastScannedItem();
    if (!last) return;
    
    const items = [...this.scannedItems()];
    const idx = items.findIndex(i => i.sku === last.sku);
    if (idx < 0) return;

    const newQty = Math.max(0, items[idx].scannedQty + delta);
    if (newQty === 0) {
      items.splice(idx, 1);
      this.lastScannedItem.set(items.length > 0 ? items[items.length - 1] : null);
    } else {
      items[idx] = { ...items[idx], scannedQty: newQty };
      this.lastScannedItem.set(items[idx]);
    }
    this.scannedItems.set(items);
  }

  removeScannedItem(index: number) {
    const items = [...this.scannedItems()];
    items.splice(index, 1);
    this.scannedItems.set(items);
    
    if (items.length === 0) {
      this.lastScannedItem.set(null);
    } else {
      this.lastScannedItem.set(items[items.length - 1]);
    }
  }

  clearScannedItems() {
    this.scannedItems.set([]);
    this.lastScannedItem.set(null);
  }

  // ─── STEP 3: Generate Discrepancy Analysis ───────────────────────────────
  finishCounting() {
    const theoretical = this.theoreticalStock();
    const counted = this.scannedItems();
    const report: DiscrepancyRow[] = [];

    // Build a map of counted items
    const countedMap = new Map<string, ScannedItem>();
    counted.forEach(c => countedMap.set(c.sku, c));

    // 1. Check theoretical items against count
    const processedSkus = new Set<string>();
    theoretical.forEach((t: any) => {
      const sku = t.sku || t.internal_sku || 'N/A';
      if (processedSkus.has(sku)) return; // Avoid duplicates
      processedSkus.add(sku);
      
      const theoreticalQty = t.total_available_qty || t.quantity || 0;
      const countedItem = countedMap.get(sku);
      const countedQty = countedItem?.scannedQty || 0;
      const diff = countedQty - theoreticalQty;
      
      report.push({
        sku,
        productName: countedItem?.productName || t.product_name || sku,
        productId: countedItem?.productId || t.item_id || '',
        theoretical: theoreticalQty,
        counted: countedQty,
        difference: diff,
        percentVariance: theoreticalQty > 0 ? (diff / theoreticalQty) * 100 : (countedQty > 0 ? 100 : 0),
        status: diff === 0 ? 'MATCH' : diff < 0 ? 'SHORTAGE' : 'SURPLUS'
      });
    });

    // 2. Check for items counted that aren't in theoretical (surprise surplus)
    counted.forEach(c => {
      if (!processedSkus.has(c.sku)) {
        report.push({
          sku: c.sku,
          productName: c.productName,
          productId: c.productId,
          theoretical: 0,
          counted: c.scannedQty,
          difference: c.scannedQty,
          percentVariance: 100,
          status: 'SURPLUS'
        });
      }
    });

    // Sort: Discrepancies first, then matches
    report.sort((a, b) => {
      if (a.status === 'MATCH' && b.status !== 'MATCH') return 1;
      if (a.status !== 'MATCH' && b.status === 'MATCH') return -1;
      return Math.abs(b.difference) - Math.abs(a.difference);
    });

    this.discrepancyReport.set(report);
    
    const hasIssues = report.some(r => r.status !== 'MATCH');
    if (hasIssues) {
      playIndustrialBeep(200, 0.6);
    } else {
      playIndustrialBeep(1000, 0.3);
    }
    
    this.currentStep.set(3);
  }

  // ─── STEP 3: Confirm & Log ────────────────────────────────────────────────
  async confirmCycleCount() {
    if (this.isProcessing()) return;
    this.isProcessing.set(true);

    try {
      // Log the cycle count result
      const report = this.discrepancyReport();
      const hasDiscrepancy = report.some(r => r.status !== 'MATCH');
      
      console.log('[CycleCount] 📋 Audit Result:', {
        location: this.lockedLocation(),
        timestamp: new Date().toISOString(),
        items: report,
        verified: !hasDiscrepancy
      });

      // Send to backend
      const warehouseId = this.inv.warehouses()[0]?.id;
      if (warehouseId) {
        const payloadItems = report.map(r => ({
          product_id: r.productId,
          sku: r.sku,
          difference: r.difference,
          status: r.status
        }));
        await this.inv.submitCycleCount(warehouseId, this.lockedLocation()!, payloadItems);
      }

      // Update session stats
      const today = new Date().toISOString().slice(0, 10);
      const newCounts = this.completedCounts() + 1;
      const newDisc = this.discrepancyCount() + (hasDiscrepancy ? 1 : 0);
      this.completedCounts.set(newCounts);
      this.discrepancyCount.set(newDisc);
      localStorage.setItem(`cc_stats_${today}`, JSON.stringify({ counts: newCounts, discrepancies: newDisc }));

      if (hasDiscrepancy) {
        this.toast.warning(
          `Discrepancia registrada para ${this.lockedLocation()}. Ajuste pendiente de revisión.`,
          'Auditoría con Varianza'
        );
      } else {
        this.toast.success(
          `Ubicación ${this.lockedLocation()} verificada exitosamente.`,
          '✅ Inventario Conforme'
        );
      }

      playIndustrialBeep(1000, 0.3);
      
      // Reset for next count
      setTimeout(() => this.resetFlow(), 1500);
      
    } catch (e: any) {
      this.toast.error('Error al registrar resultado de auditoría.', 'Sync Error');
      playIndustrialBeep(110, 0.6);
    } finally {
      this.isProcessing.set(false);
    }
  }

  // ─── Flow Control ─────────────────────────────────────────────────────────
  resetFlow() {
    this.currentStep.set(1);
    this.locationScan = '';
    this.itemScan = '';
    this.lockedLocation.set('');
    this.scannedItems.set([]);
    this.lastScannedItem.set(null);
    this.discrepancyReport.set([]);
    this.theoreticalStock.set([]);
    
    setTimeout(() => this.locationInput?.nativeElement?.focus(), 100);
  }

  // ─── Keyboard Shortcuts ───────────────────────────────────────────────────
  @HostListener('window:keydown', ['$event'])
  handleGlobalKeys(event: KeyboardEvent) {
    if (event.key === 'F2') {
      event.preventDefault();
      if (this.currentStep() === 2) {
        this.finishCounting();
      } else if (this.currentStep() === 3) {
        this.confirmCycleCount();
      } else {
        this.locationInput?.nativeElement?.focus();
      }
    }
    if (event.key === 'Escape') {
      if (this.currentStep() > 1) {
        this.resetFlow();
      }
    }
  }
}
