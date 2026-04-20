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

// ─── Industrial Audio Feedback ──────────────────────────────────────────────
function playIndustrialBeep(frequency: number = 200, duration: number = 0.3) {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    const now = ctx.currentTime;
    
    osc.frequency.setValueAtTime(frequency, now);
    osc.type = 'square'; // Industrial feel
    
    gain.gain.setValueAtTime(0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
    
    osc.start(now); osc.stop(now + duration);
  } catch (e) {}
}

@Component({
  selector: 'app-inventory-put-away',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="min-h-screen bg-surface-bg text-surface-text font-mono select-none overflow-hidden flex flex-col">
      
      <!-- ── INDUSTRIAL HEADER ───────────────────────────────────────────── -->
      <div class="sticky top-0 z-30 bg-surface-card border-b-2 border-emerald-500/50 px-4 py-4 flex items-center justify-between shadow-2xl">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
            <mat-icon class="text-emerald-400">forklift</mat-icon>
          </div>
          <div>
            <h1 class="text-sm font-black uppercase tracking-widest text-emerald-400">Put-Away Handheld</h1>
            <p class="text-[9px] text-surface-text-muted uppercase tracking-tighter">{{ activeWarehouseName() || 'Offline Mode' }}</p>
          </div>
        </div>
        <div class="text-right">
          <span class="text-[10px] font-black text-emerald-400 uppercase tracking-widest">PASO {{ currentStep() }} OF 3</span>
          <div class="mt-1 flex gap-1 justify-end">
             <div *ngFor="let i of [1,2,3]" 
                  [class.bg-emerald-500]="currentStep() >= i" [class.bg-white/10]="currentStep() < i"
                  class="w-4 h-1 rounded-full transition-all"></div>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto px-4 py-6 space-y-6 max-w-4xl mx-auto w-full">

        <!-- ── STEP 1: SCAN ORIGIN (Pallet / Lot / Source Loc) ────────────── -->
        <div *ngIf="currentStep() === 1" class="space-y-4 animate-fade-in">
          
          <!-- Toggle Manual Mode Button -->
          <div class="flex justify-end">
             <button (click)="toggleManualMode()" 
                     class="text-[9px] font-black uppercase px-3 py-1.5 rounded-lg border transition-all"
                     [class.bg-emerald-500]="isManualMode()" [class.text-surface-bg]="isManualMode()" [class.border-emerald-500]="isManualMode()"
                     [class.text-surface-text-muted]="!isManualMode()" [class.border-surface-border]="!isManualMode()" [class.hover:text-surface-text]="!isManualMode()">
               {{ isManualMode() ? 'Cerrar Modo Manual' : 'Entrada Manual (Sin Folio)' }}
             </button>
          </div>

          <!-- STANDARD SCAN MODE -->
          <div *ngIf="!isManualMode()" class="bg-surface-card border border-emerald-500/20 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
             <div class="absolute -right-4 -top-4 opacity-5">
              <mat-icon class="text-9xl">barcode_scanner</mat-icon>
            </div>
            
            <label class="text-[10px] uppercase tracking-[0.3em] text-emerald-400 font-black mb-4 block">
              PARTE 1: Escanear Origen (Pallet/Lote)
            </label>
            
            <div class="space-y-4 relative z-10">
              <input
                #originInput
                [(ngModel)]="originScan"
                (keydown.enter)="processOrigin()"
                placeholder="PALLET-XXX / LOTE-XXX"
                class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-6 text-2xl font-black text-emerald-400 placeholder-surface-text-muted outline-none focus:border-emerald-500 transition-all text-center tracking-widest uppercase"
                autocomplete="off"
                autofocus
              />
              
              <div class="p-4 bg-emerald-500/5 rounded-xl border border-emerald-500/10">
                <p class="text-[9px] text-emerald-400/80 font-black uppercase leading-relaxed text-center">
                  Identifique el Pallet o Lote en el área de recibo (DOCK-01)
                </p>
              </div>
            </div>
          </div>

          <!-- MANUAL BLIND ENTRY MODE -->
          <div *ngIf="isManualMode()" class="bg-surface-card border-2 border-amber-500/40 rounded-2xl p-6 shadow-2xl space-y-4 animate-fade-in">
             <label class="text-[10px] uppercase tracking-[0.3em] text-amber-500 font-black block">
              Entrada Manual (Blind Entry)
            </label>

            <!-- Instant Search Field -->
            <div class="space-y-2">
              <span class="text-[8px] text-surface-text-muted uppercase font-black">SKU / No. Parte</span>
              <input
                #manualSkuInput
                [(ngModel)]="manualSku"
                placeholder="ESCRIBE SKU..."
                class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-4 text-xl font-black text-amber-400 outline-none focus:border-amber-500 transition-all uppercase"
              />
            </div>

            <!-- Instant Result feedback from Registry -->
            <div class="min-h-[60px] p-4 bg-surface-bg rounded-xl border border-surface-border flex items-center gap-3">
               <mat-icon [class.text-amber-500]="manualProductResult()" class="text-surface-text-muted">
                 {{ manualProductResult() ? 'inventory_2' : 'search_off' }}
               </mat-icon>
               <div class="flex-1 min-w-0">
                 <p class="text-[10px] font-black text-surface-text leading-tight">
                   {{ manualProductResult()?.name || 'Esperando SKU válido...' }}
                 </p>
                 <p *ngIf="manualProductResult()" class="text-[8px] text-amber-500 uppercase mt-1 font-bold">Registrado en Caché O(1)</p>
               </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
               <div class="space-y-2">
                  <span class="text-[8px] text-surface-text-muted uppercase font-black">Cantidad</span>
                  <input type="number" [(ngModel)]="manualQty" class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-4 text-xl font-black text-surface-text outline-none"/>
               </div>
               <div class="space-y-2">
                  <span class="text-[8px] text-surface-text-muted uppercase font-black">UOM</span>
                  <div class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-4 text-xl font-black text-surface-text-muted">PZA</div>
               </div>
            </div>

            <button 
              (click)="processManualEntry()"
              [disabled]="!manualProductResult()"
              class="w-full py-4 rounded-xl bg-amber-500 text-surface-bg font-black uppercase tracking-widest shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2">
              <mat-icon>arrow_forward</mat-icon>
              <span>Continuar a Ubicación</span>
            </button>
          </div>

        </div>

        <!-- ── STEP 2: SCAN DESTINATION (Rack) ────────────────────────────── -->
        <div *ngIf="currentStep() === 2" class="space-y-4 animate-fade-in">
          <div class="bg-surface-card border border-emerald-500/20 rounded-2xl p-6 shadow-2xl">
            <div class="flex items-center justify-between mb-4">
               <label class="text-[10px] uppercase tracking-[0.3em] text-emerald-400 font-black">
                PARTE 2: Destino (Rack)
              </label>
              <button (click)="currentStep.set(1)" class="text-[9px] text-surface-text-muted font-black uppercase hover:text-surface-text">Cambiar Origen</button>
            </div>

            <div class="bg-surface-bg rounded-xl p-4 mb-6 border border-surface-border flex items-center gap-4">
              <div class="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <mat-icon class="text-emerald-400">inventory_2</mat-icon>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-[9px] text-surface-text-muted font-black uppercase">Material Identificado</p>
                <p class="text-xl font-black text-surface-text truncate">{{ identifiedItem()?.sku }}</p>
                <p class="text-[10px] text-emerald-400 font-bold truncate">CANT: {{ identifiedItem()?.quantity }} PZA</p>
              </div>
            </div>

            <input
              #destInput
              [(ngModel)]="destScan"
              (keydown.enter)="processDestination()"
              placeholder="SCAN RACK LOCATION"
              class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-6 text-2xl font-black text-emerald-400 placeholder-surface-text-muted outline-none focus:border-emerald-500 transition-all text-center tracking-widest uppercase"
              autocomplete="off"
            />
            
            <p class="text-[9px] text-surface-text-muted mt-4 text-center">Escanee la etiqueta de ubicación en el Rack definitivo.</p>
          </div>
        </div>

        <!-- ── STEP 3: CONFIRM & EXECUTE ───────────────────────────────────── -->
        <div *ngIf="currentStep() === 3" class="space-y-4 animate-fade-in">
          <div class="bg-surface-card border-2 border-emerald-500/40 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
            
            <div class="text-center space-y-2 mb-8">
              <mat-icon class="text-6xl text-emerald-400 animate-pulse">check_circle</mat-icon>
              <h2 class="text-xl font-black uppercase tracking-tighter">Confirmar Re-ubicación</h2>
            </div>

            <div class="space-y-1 relative z-10">
              <div class="flex justify-between items-center py-4 border-b border-surface-border">
                <span class="text-[10px] font-black text-surface-text-muted uppercase">Material</span>
                <span class="text-sm font-black text-emerald-400">{{ identifiedItem()?.sku }}</span>
              </div>
              <div class="flex justify-between items-center py-4 border-b border-surface-border">
                <span class="text-[10px] font-black text-surface-text-muted uppercase">Origen</span>
                <span class="text-sm font-black text-surface-text">{{ identifiedItem()?.from_location }}</span>
              </div>
              <div class="flex justify-between items-center py-4 border-b border-surface-border">
                <span class="text-[10px] font-black text-surface-text-muted uppercase">Destino</span>
                <span class="text-sm font-black text-emerald-400">{{ destScan }}</span>
              </div>
              <div class="flex justify-between items-center py-4 border-b border-surface-border">
                <span class="text-[10px] font-black text-surface-text-muted uppercase">Densidad Rack</span>
                <div class="flex-1 mx-4 h-1.5 bg-surface-border rounded-full overflow-hidden">
                   <div class="h-full transition-all duration-700" 
                        [style.width.%]="locationDensity()?.utilization_percent || 0"
                        [class.bg-emerald-500]="(locationDensity()?.utilization_percent || 0) < 75"
                        [class.bg-amber-500]="(locationDensity()?.utilization_percent || 0) >= 75 && (locationDensity()?.utilization_percent || 0) < 95"
                        [class.bg-red-500]="(locationDensity()?.utilization_percent || 0) >= 95"></div>
                </div>
                <span class="text-[10px] font-black" 
                      [class.text-emerald-400]="(locationDensity()?.utilization_percent || 0) < 75"
                      [class.text-amber-400]="(locationDensity()?.utilization_percent || 0) >= 75">
                  {{ locationDensity()?.utilization_percent || 0 }}%
                </span>
              </div>
              <div class="flex justify-between items-center py-4">
                <span class="text-[10px] font-black text-surface-text-muted uppercase">Capacidad Restante</span>
                <span class="text-xs font-black text-surface-text">{{ locationDensity()?.available_space || 'LIMITLESS' }} PZA</span>
              </div>
            </div>

            <button 
              (click)="executePutAway()" 
              [disabled]="isProcessing()"
              class="w-full mt-8 py-6 rounded-2xl bg-emerald-500 text-surface-bg font-black uppercase text-lg tracking-widest
                     shadow-2xl shadow-emerald-500/30 active:scale-95 transition-all flex items-center justify-center gap-3">
              <mat-icon *ngIf="!isProcessing()">task_alt</mat-icon>
              <mat-icon *ngIf="isProcessing()" class="animate-spin text-surface-bg/50">sync</mat-icon>
              <span>{{ isProcessing() ? 'GUARDANDO...' : 'CONFIRMAR [F2]' }}</span>
            </button>

            <button (click)="currentStep.set(2)" [disabled]="isProcessing()"
              class="w-full mt-4 py-2 text-[10px] text-surface-text-muted font-black uppercase hover:text-surface-text transition-colors">
              Correjir Ubicación
            </button>
          </div>
        </div>

      </div>

      <!-- ── INDUSTRIAL FOOTER / STATUS ──────────────────────────────────── -->
      <div class="bg-[#111] border-t border-white/5 px-6 py-3 flex justify-between items-center">
        <div class="flex items-center gap-2">
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span class="text-[8px] font-black text-white/40 uppercase tracking-widest">Sistema Operativo</span>
        </div>
        <span class="text-[8px] font-black text-white/20">v3.8.0-INDUSTRIAL</span>
      </div>
    </div>
  `,
  styles: [`
    @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
    .animate-fade-in { animation: fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .animate-spin { animation: spin 1s linear infinite; }
  `]
})
export class InventoryPutAwayComponent implements OnInit {
  private inv = inject(InventoryService);
  private registry = inject(InventoryRegistryService);
  private toast = inject(ToastService);
  private auth = inject(AuthService);

  @ViewChild('originInput') originInput?: ElementRef;
  @ViewChild('destInput') destInput?: ElementRef;
  @ViewChild('manualSkuInput') manualSkuInput?: ElementRef;

  // ── State ──────────────────────────────────────────────────────────────────
  currentStep = signal(1);
  isManualMode = signal(false); // [Phase 48] Blind Entry Mode
  isLoading = signal(false);
  isProcessing = signal(false);

  originScan = '';
  destScan = '';
  
  // Manual Entry Form
  manualSku = '';
  manualQty = 1;
  manualUnit = 'PZA';
  
  identifiedItem = signal<any | null>(null);
  locationDensity = signal<any | null>(null);

  // Instant lookup for Manual Mode
  manualProductResult = computed(() => {
    return this.registry.getProductBySku(this.manualSku);
  });

  // ── Lifecycle ──────────────────────────────────────────────────────────────
  ngOnInit() {
    this.inv.loadCatalogs();
    this.registry.hydrate(); // Performance Layer: Hydrate O(1) Catalog
  }

  // ── Computed ─────────────────────────────────────────────────────────────
  activeWarehouseName = computed(() => {
    const whs = this.inv.warehouses();
    const activeId = this.inv.warehouses()[0]?.id;
    return whs.find(w => w.id === activeId)?.name || 'CENTRO LOGÍSTICO';
  });

  // ── Actions ────────────────────────────────────────────────────────────────

  async processOrigin() {
    const scan = this.originScan.trim().toUpperCase();
    if (!scan) return;

    this.isLoading.set(true);
    try {
      const warehouseId = this.inv.warehouses()[0]?.id;
      
      // Industrial Search: Find matching stock entries (Pedimentos/Lots) in this warehouse
      const res = await this.inv.getCustomsBalances(warehouseId, 5, 0, scan);
      
      if (!res.data || res.data.length === 0) {
        throw new Error('Stock no encontrado');
      }

      // We take the first match as the "identified" stock
      const stock = res.data[0];
      
      this.identifiedItem.set({
        product_id: stock.item_id,
        uom_id: '1a7444c9-40df-51d5-833b-501fc84b67bb', // Fallback PZA
        sku: stock.sku,
        quantity: stock.total_available_qty,
        from_location: 'DOCK-01', // Standard staging location
        pedimento: stock.pedimento_number,
        is_manual: false
      });

      playIndustrialBeep(880, 0.15);
      this.currentStep.set(2);
      setTimeout(() => this.destInput?.nativeElement.focus(), 100);
      
    } catch (e) {
      // Automatic Fallback suggestion for Manual Entry
      this.toast.info('Material no localizado en DOCK-01. ¿Es una entrada manual?', 'Modo Manual Disponible');
      playIndustrialBeep(200, 0.4);
    } finally {
      this.isLoading.set(false);
    }
  }

  toggleManualMode() {
    this.isManualMode.set(!this.isManualMode());
    if (this.isManualMode()) {
      setTimeout(() => this.manualSkuInput?.nativeElement.focus(), 100);
    } else {
      setTimeout(() => this.originInput?.nativeElement.focus(), 100);
    }
  }

  processManualEntry() {
    const product = this.manualProductResult();
    if (!product) {
      this.toast.error('SKU no existe en el catálogo maestro.', 'Error de Catálogo');
      playIndustrialBeep(100, 0.5);
      return;
    }

    if (this.manualQty <= 0) {
      this.toast.warning('La cantidad debe ser mayor a 0.', 'Validación');
      return;
    }

    this.identifiedItem.set({
      product_id: product.id,
      uom_id: '1a7444c9-40df-51d5-833b-501fc84b67bb', // PZA
      sku: product.sku,
      quantity: this.manualQty,
      from_location: 'FLOOR_ADJUST', // Manual entry origin
      pedimento: 'MANUAL_ENTRY',
      is_manual: true
    });

    this.isManualMode.set(false);
    this.currentStep.set(2);
    playIndustrialBeep(880, 0.15);
    setTimeout(() => this.destInput?.nativeElement.focus(), 100);
  }

  async processDestination() {
    const scan = this.destScan.trim().toUpperCase();
    if (!scan) return;

    // Basic location validation (Industrial Patterns: RACK-X-Y-Z)
    if (scan.length < 3) {
      this.toast.warning('Etiqueta de ubicación inválida.', 'Validación de Destino');
      playIndustrialBeep(200, 0.4);
      return;
    }

    this.isLoading.set(true);
    try {
      const warehouseId = this.inv.warehouses()[0]?.id;
      const res = await this.inv.getLocationDensity(warehouseId, scan);
      this.locationDensity.set(res.data);

      const item = this.identifiedItem();
      const nextOccupancy = res.data.current_occupancy + item.quantity;
      
      // If capacity is defined and exceeded, warn immediately
      if (res.data.max_capacity > 0 && nextOccupancy > res.data.max_capacity) {
        this.toast.error(`¡CAPACIDAD EXCEDIDA! La ubicación solo soporta ${res.data.max_capacity}.`, 'Density Guard 🚨');
        playIndustrialBeep(110, 0.8);
        return;
      }

      playIndustrialBeep(880, 0.15);
      this.currentStep.set(3);
    } catch (e) {
      this.toast.error('No se pudo validar la capacidad de la ubicación.', 'Sync Error');
    } finally {
      this.isLoading.set(false);
    }
  }

  async executePutAway() {
    if (this.isProcessing()) return;
    this.isProcessing.set(true);

    try {
      const warehouseId = this.inv.warehouses()[0]?.id;
      const item = this.identifiedItem();

      await this.inv.relocateStock({
        product_id: item.product_id,
        uom_id: item.uom_id,
        warehouse_id: warehouseId,
        quantity: item.quantity,
        from_location: item.from_location,
        to_location: this.destScan,
        notes: `Put-away manual via Handheld. Scan: ${this.originScan}`
      });

      this.toast.success('Material re-ubicado correctamente.', '✅ Put-Away Exitoso');
      playIndustrialBeep(1000, 0.3);
      
      // Reset flow
      this.resetFlow();
      
    } catch (e: any) {
      const msg = e?.error?.message || 'Error al sincronizar re-ubicación.';
      this.toast.error(msg, 'Sync Error');
      playIndustrialBeep(110, 0.6); // Very low beep = critical failure
    } finally {
      this.isProcessing.set(false);
    }
  }

  resetFlow() {
    this.currentStep.set(1);
    this.originScan = '';
    this.destScan = '';
    this.identifiedItem.set(null);
    setTimeout(() => this.originInput?.nativeElement.focus(), 100);
  }

  @HostListener('window:keydown', ['$event'])
  handleGlobalKeys(event: KeyboardEvent) {
    if (event.key === 'F2') {
      event.preventDefault();
      if (this.currentStep() === 3) {
        this.executePutAway();
      } else {
        // Focus appropriate input
        if (this.currentStep() === 1) this.originInput?.nativeElement.focus();
        if (this.currentStep() === 2) this.destInput?.nativeElement.focus();
      }
    }
  }
}
