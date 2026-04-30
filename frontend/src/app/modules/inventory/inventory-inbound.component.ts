import {
  Component, signal, inject, OnInit, computed, HostListener
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { InventoryService } from '../../core/services/inventory.service';
import { MasterDataService } from '../../core/services/master-data.service';
import { ToastService } from '../../core/services/toast.service';
import { AuthService } from '../../core/services/auth.service';

// ─── Audio Context (Industrial Scanner Feedback) ──────────────────────────────
function playBeep(type: 'success' | 'warning' | 'error') {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    const now = ctx.currentTime;
    if (type === 'success') {
      osc.frequency.setValueAtTime(880, now);
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.15);
      osc.start(now); osc.stop(now + 0.15);
    } else if (type === 'error') {
      osc.frequency.setValueAtTime(220, now);
      osc.frequency.exponentialRampToValueAtTime(110, now + 0.4);
      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.4);
      osc.start(now); osc.stop(now + 0.4);
    }
  } catch (e) { /* audio not available */ }
}

@Component({
  selector: 'app-inventory-inbound',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="min-h-screen bg-surface-bg text-surface-text font-sans">

      <!-- ── RESTRICTION BANNERS (Phase 19) ────────────────────────────────── -->
      <div *ngIf="isUnpaid()" class="bg-red-600 text-white px-4 py-2 text-[10px] font-black uppercase tracking-widest text-center animate-pulse sticky top-0 z-[60]">
        Cuenta Bloqueada por Falta de Pago - Acceso Restringido a Consultas
      </div>
      <div *ngIf="isReadOnly() && !isUnpaid()" class="bg-amber-600 text-white px-4 py-2 text-[10px] font-black uppercase tracking-widest text-center sticky top-0 z-[60]">
        Modo Lectura Activo (Suscripción en Periodo de Gracia)
      </div>

      <!-- ── HEADER ─────────────────────────────────────────────────────────── -->
      <div class="sticky top-0 z-30 bg-surface-card border-b border-surface-border px-4 py-3 flex items-center justify-between shadow-lg">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-amber-500/20 flex items-center justify-center">
            <mat-icon class="text-amber-400 text-xl">move_to_inbox</mat-icon>
          </div>
          <div>
            <h1 class="text-sm font-black uppercase tracking-widest text-surface-text">Recepción de Mercancía</h1>
            <p class="text-[10px] text-surface-text-muted">{{ activeCompany() }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-[10px] font-mono bg-amber-500/10 text-amber-400 px-2 py-1 rounded-lg border border-amber-500/20">
            {{ pendingCount() }} PENDIENTES
          </span>
          <button (click)="loadPending()" [disabled]="isLoading()"
            class="w-9 h-9 rounded-xl bg-surface-bg border border-surface-border flex items-center justify-center hover:border-primary/50 transition-colors">
            <mat-icon class="text-sm" [class.animate-spin]="isLoading()">refresh</mat-icon>
          </button>
          <button (click)="openBlindReceipt()" [disabled]="isReadOnly()"
            class="px-3 py-1 bg-primary/20 border border-primary/30 rounded-lg text-[10px] text-primary font-black uppercase tracking-widest hover:bg-primary/30 transition-all disabled:opacity-30">
            Recibo Ciego
          </button>
        </div>
      </div>

      <div class="max-w-2xl mx-auto px-4 py-6 space-y-5">

        <!-- ── SCANNER INPUT ────────────────────────────────────────────────── -->
        <div class="bg-surface-card border border-surface-border rounded-2xl p-4 shadow-sm">
          <label class="text-[10px] uppercase tracking-[0.2em] text-surface-text-muted font-black mb-2 block">
            Escanear / Buscar Folio
          </label>
          <div class="flex gap-2">
            <input
              #folioInput
              [(ngModel)]="folioQuery"
              (keydown.enter)="searchByFolio()"
              placeholder="Ej: ICT-20260414-0001"
              class="flex-1 bg-surface-bg border border-surface-border rounded-xl px-4 py-4 text-base font-mono text-surface-text placeholder-surface-text-muted outline-none focus:border-primary transition-colors text-center tracking-widest"
              autocomplete="off"
              spellcheck="false"
            />
            <button (click)="searchByFolio()" [disabled]="!folioQuery || isSearching()"
              class="px-5 py-4 rounded-xl bg-primary text-surface-bg font-black uppercase text-[10px] tracking-widest
                     disabled:opacity-40 hover:scale-[1.02] active:scale-95 transition-all shadow-lg shadow-primary/30">
              <mat-icon *ngIf="!isSearching()">qr_code_scanner</mat-icon>
              <mat-icon *ngIf="isSearching()" class="animate-spin">progress_activity</mat-icon>
            </button>
          </div>
          <p *ngIf="searchError()" class="text-red-400 text-[10px] mt-2 text-center font-bold">{{ searchError() }}</p>
        </div>

        <!-- ── TRANSFER DETAIL (found by folio or selected from list) ─────── -->
        <div *ngIf="selectedTransfer()" class="bg-surface-card border-2 border-primary/30 rounded-2xl overflow-hidden shadow-xl animate-fade-in">

          <!-- Status Banner -->
          <div class="px-5 py-3 flex items-center justify-between"
               [class.bg-amber-500]="selectedTransfer()?.status === 'SHIPPED'"
               [class.bg-emerald-500]="selectedTransfer()?.status === 'DELIVERED'"
               [class.bg-surface-border]="selectedTransfer()?.status === 'CANCELLED'">
            <span class="text-xs font-black uppercase tracking-widest text-white">
              {{ selectedTransfer()?.status }}
            </span>
            <span class="text-white text-xl font-mono font-black">{{ selectedTransfer()?.folio }}</span>
            <button (click)="clearSelection()" class="text-white/80 hover:text-white">
              <mat-icon>close</mat-icon>
            </button>
          </div>

          <!-- Info Grid -->
          <div class="p-5 space-y-4">
            <div class="grid grid-cols-2 gap-3">
              <div class="bg-surface-bg rounded-xl p-3">
                <p class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1">Empresa Origen</p>
                <p class="text-xs font-bold text-surface-text truncate">{{ selectedTransfer()?.origin_company_name || 'Empresa A' }}</p>
              </div>
              <div class="bg-surface-bg rounded-xl p-3">
                <p class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1">Almacén Origen</p>
                <p class="text-xs font-bold text-surface-text truncate">{{ selectedTransfer()?.origin_warehouse_name || '—' }}</p>
              </div>
              <div class="bg-surface-bg rounded-xl p-3">
                <p class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1">Producto</p>
                <p class="text-xs font-bold text-primary truncate">{{ selectedTransfer()?.origin_sku || selectedTransfer()?.product_sku || '—' }}</p>
              </div>
              <div class="bg-surface-bg rounded-xl p-3">
                <p class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1">Cantidad Despachada</p>
                <p class="text-2xl font-black text-amber-400 font-mono">{{ selectedTransfer()?.quantity | number:'1.0-2' }}</p>
              </div>
            </div>

            <!-- Notes from sender -->
            <div *ngIf="selectedTransfer()?.notes" class="bg-surface-bg rounded-xl p-3 border-l-2 border-primary/40">
              <p class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1">Notas del Remitente</p>
              <p class="text-xs text-surface-text">{{ selectedTransfer()?.notes }}</p>
            </div>

            <!-- ── RECEIVE FORM (only when SHIPPED) ── -->
            <div *ngIf="selectedTransfer()?.status === 'SHIPPED'" class="space-y-3 pt-2 border-t border-surface-border">
              <p class="text-[10px] uppercase tracking-widest text-surface-text-muted font-black">Confirmar Recepción</p>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1 block">Cantidad Recibida</label>
                  <input [(ngModel)]="receivedQty"
                    type="number" min="0" step="0.01"
                    [placeholder]="selectedTransfer()?.quantity"
                    class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-lg font-mono font-black text-center text-emerald-400 outline-none focus:border-emerald-400 transition-colors" />
                </div>
                <div>
                  <label class="text-[9px] uppercase tracking-widest text-red-400 font-black mb-1 block">Cantidad Dañada</label>
                  <input [(ngModel)]="damagedQty"
                    type="number" min="0" step="0.01" placeholder="0"
                    class="w-full bg-surface-bg border border-red-500/20 rounded-xl px-4 py-3 text-lg font-mono font-black text-center text-red-400 outline-none focus:border-red-400 transition-colors" />
                </div>
              </div>

              <!-- Dock / Staging Selection (Maturity Phase 47) -->
              <div class="space-y-2">
                <label class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1 block">Ubicación de Recepción (Staging)</label>
                <div class="grid grid-cols-2 gap-2">
                  <button *ngFor="let dock of docks()" 
                    (click)="selectedDockId.set(dock.id)"
                    [class.border-primary]="selectedDockId() === dock.id"
                    [class.bg-primary/10]="selectedDockId() === dock.id"
                    class="p-3 border border-surface-border rounded-xl text-left transition-all hover:border-primary/50">
                    <p class="text-[10px] font-black text-surface-text">{{ dock.code }}</p>
                    <p class="text-[8px] text-surface-text-muted uppercase">{{ dock.name }}</p>
                  </button>
                </div>
              </div>

              <!-- Financial Impact (Maturity Phase) -->
              <div *ngIf="selectedTransfer()?.transfer_price" class="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3 flex items-center justify-between">
                <div>
                   <p class="text-[8px] uppercase font-black text-amber-500">Precio de Transferencia (Contract)</p>
                   <p class="text-xs font-mono font-bold text-surface-text">{{ selectedTransfer()?.transfer_price | currency:'USD' }} / {{ selectedTransfer()?.uom_code || 'PZA' }}</p>
                </div>
                <div class="text-right">
                   <p class="text-[8px] uppercase font-black text-surface-text-muted">Impacto Financiero</p>
                   <p class="text-xs font-mono font-bold text-amber-400">{{ (receivedQty || selectedTransfer()?.quantity) * selectedTransfer()?.transfer_price | currency:'USD' }}</p>
                </div>
              </div>

              <div>
                <label class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1 block">Notas de Recepción (opcional)</label>
                <textarea [(ngModel)]="receiveNotes" rows="2" placeholder="Condición del embalaje, observaciones..."
                  class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-xs text-surface-text resize-none outline-none focus:border-primary transition-colors"></textarea>
              </div>

              <!-- CONFIRM BUTTON - Big, fat, industrial -->
              <button (click)="confirmReceipt()" [disabled]="isConfirming() || isReadOnly()"
                class="w-full py-5 rounded-2xl bg-emerald-500 text-white font-black uppercase text-sm tracking-widest
                       shadow-xl shadow-emerald-500/30 hover:scale-[1.01] active:scale-[0.99] transition-all
                       disabled:opacity-50 disabled:grayscale flex items-center justify-center gap-3">
                <mat-icon *ngIf="!isConfirming()" class="text-2xl">verified</mat-icon>
                <mat-icon *ngIf="isConfirming()" class="text-2xl animate-spin">progress_activity</mat-icon>
                <span>{{ isConfirming() ? 'Procesando...' : 'CONFIRMAR RECEPCIÓN' }}</span>
              </button>

              <p class="text-[9px] text-center text-surface-text-muted">
                Si <strong>Cantidad Recibida</strong> está vacía, se asumirá la cantidad total despachada.
              </p>
            </div>

            <!-- Already delivered message -->
            <div *ngIf="selectedTransfer()?.status === 'DELIVERED'"
              class="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center">
              <mat-icon class="text-emerald-400 text-3xl block mb-2">check_circle</mat-icon>
              <p class="text-sm font-black text-emerald-400">Transferencia ya recibida.</p>
              <p class="text-[10px] text-surface-text-muted mt-1">Recibida: {{ selectedTransfer()?.received_at | date:'short' }}</p>
            </div>
          </div>
        </div>

        <!-- ── PENDING LIST ─────────────────────────────────────────────────── -->
        <div class="space-y-3">
          <div class="flex items-center gap-2">
            <mat-icon class="text-amber-400 scale-75">local_shipping</mat-icon>
            <h2 class="text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Transferencias en Tránsito</h2>
          </div>

          <!-- Loading skeleton -->
          <ng-container *ngIf="isLoading()">
            <div *ngFor="let i of [1,2,3]" class="h-20 bg-surface-card rounded-2xl animate-pulse"></div>
          </ng-container>

          <!-- Empty state -->
          <div *ngIf="!isLoading() && pendingTransfers().length === 0 && !selectedTransfer()"
            class="bg-surface-card border border-surface-border rounded-2xl p-10 text-center">
            <mat-icon class="text-4xl text-surface-text-muted block mb-3">inbox</mat-icon>
            <p class="text-sm font-bold text-surface-text-muted">Sin transferencias pendientes</p>
            <p class="text-[10px] text-surface-text-muted mt-1">Todo el inventario está recibido o no hay envíos activos.</p>
          </div>

          <!-- Transfer cards -->
          <div *ngFor="let t of pendingTransfers()"
            (click)="selectTransfer(t)"
            class="bg-surface-card border border-surface-border rounded-2xl p-4 cursor-pointer
                   hover:border-amber-500/50 hover:shadow-lg transition-all duration-200 active:scale-[0.99]"
            [class.border-primary]="selectedTransfer()?.id === t.id">
            <div class="flex items-start justify-between mb-2">
              <span class="font-mono text-sm font-black text-primary tracking-tight">{{ t.folio }}</span>
              <span class="text-[9px] font-black uppercase px-2 py-0.5 rounded-lg bg-amber-500/20 text-amber-400">EN TRÁNSITO</span>
            </div>
            <div class="grid grid-cols-3 gap-2">
              <div>
                <p class="text-[9px] text-surface-text-muted uppercase tracking-wider">SKU</p>
                <p class="text-xs font-bold text-surface-text truncate">{{ t.origin_sku || t.product_sku || '—' }}</p>
              </div>
              <div>
                <p class="text-[9px] text-surface-text-muted uppercase tracking-wider">Cantidad</p>
                <p class="text-xl font-black text-amber-400 font-mono leading-none">{{ t.quantity | number:'1.0-2' }}</p>
              </div>
              <div>
                <p class="text-[9px] text-surface-text-muted uppercase tracking-wider">Enviado</p>
                <p class="text-xs font-bold text-surface-text">{{ t.shipped_at | date:'d MMM' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- ── BLIND RECEIPT MODAL ─────────────────────────────────────────── -->
        <div *ngIf="showBlindReceipt()" class="fixed inset-0 z-50 flex items-center justify-center px-4 bg-surface-bg/90 backdrop-blur-sm animate-fade-in">
          <div class="w-full max-w-md bg-surface-card border-2 border-primary/50 rounded-3xl overflow-hidden shadow-2xl">
            <div class="bg-primary px-6 py-4 flex items-center justify-between">
              <h2 class="text-sm font-black text-surface-bg uppercase tracking-widest">Recibo Ciego (Directo)</h2>
              <button (click)="showBlindReceipt.set(false)" class="text-surface-bg/80 hover:text-surface-bg">
                <mat-icon>close</mat-icon>
              </button>
            </div>
            
            <div class="p-6 space-y-4">
              <div class="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                 <p class="text-[10px] text-amber-500 font-bold uppercase tracking-tight">Atención: Modo Industrial</p>
                 <p class="text-[9px] text-surface-text-muted mt-1">Este modo crea un recibo sin documento previo. Se requiere regularización posterior.</p>
              </div>

              <div>
                <label class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1 block">SKU / Producto</label>
                <input [(ngModel)]="blindSku" placeholder="Escanee SKU..."
                  class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-4 text-base font-mono font-black text-primary outline-none focus:border-primary transition-colors" />
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1 block">Cantidad</label>
                  <input [(ngModel)]="blindQty" type="number"
                    class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-4 text-lg font-mono font-black text-center text-emerald-400 outline-none focus:border-emerald-400 transition-colors" />
                </div>
                <div>
                  <label class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1 block">Unidad (UOM)</label>
                  <select [(ngModel)]="blindUomId" 
                    class="w-full bg-surface-bg border-2 border-surface-border rounded-xl px-6 py-5 text-[11px] font-black uppercase tracking-[0.2em] text-surface-text outline-none focus:border-primary appearance-none shadow-lg">
                    <option *ngFor="let uom of uoms()" [value]="uom.id">{{ uom.code }} - {{ uom.name }}</option>
                  </select>
                </div>
              </div>

              <div>
                <label class="text-[9px] uppercase tracking-widest text-surface-text-muted font-black mb-1 block">Almacén Destino</label>
                <select [(ngModel)]="blindWarehouseId" 
                  class="w-full bg-surface-bg border-2 border-surface-border rounded-xl px-6 py-5 text-[11px] font-black uppercase tracking-[0.2em] text-surface-text outline-none focus:border-primary appearance-none shadow-lg">
                  <option *ngFor="let wh of warehouses()" [value]="wh.id">{{ wh.code }} - {{ wh.name }}</option>
                </select>
              </div>

              <button (click)="confirmBlindReceipt()" [disabled]="isConfirming() || !blindSku || !blindQty"
                class="w-full py-5 rounded-2xl bg-primary text-surface-bg font-black uppercase text-sm tracking-widest
                       shadow-xl shadow-primary/30 hover:scale-[1.01] active:scale-[0.99] transition-all
                       disabled:opacity-50 disabled:grayscale flex items-center justify-center gap-3 mt-4">
                <mat-icon *ngIf="!isConfirming()">add_task</mat-icon>
                <mat-icon *ngIf="isConfirming()" class="animate-spin">progress_activity</mat-icon>
                <span>CONSOLIDAR RECIBO</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; } }
    .animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .animate-spin { animation: spin 1s linear infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .4; } }
    .animate-pulse { animation: pulse 1.5s ease-in-out infinite; }
  `]
})
export class InventoryInboundComponent implements OnInit {
  private inv = inject(InventoryService);
  private masterData = inject(MasterDataService);
  private toast = inject(ToastService);
  private auth = inject(AuthService);

  // ── State ──────────────────────────────────────────────────────────────────
  isReadOnly = this.auth.isReadOnly;
  isUnpaid = this.auth.isUnpaid;

  isLoading = signal(false);
  isSearching = signal(false);
  isConfirming = signal(false);

  pendingTransfers = signal<any[]>([]);
  selectedTransfer = signal<any | null>(null);
  searchError = signal('');

  folioQuery = '';
  receivedQty: number | null = null;
  damagedQty: number = 0;
  receiveNotes = '';

  // Blind Receipt State
  showBlindReceipt = signal(false);
  blindSku = '';
  blindQty: number | null = null;
  blindUomId = '';
  blindWarehouseId = '';

  // Staging points (Hardware/Industrial Reality) - Use warehouses as default locations
  selectedDockId = signal<string>('');
  docks = computed(() => this.inv.warehouses().map(w => ({ id: w.id, code: w.code, name: w.name })));


  // ── Computed ───────────────────────────────────────────────────────────────
  pendingCount = computed(() => this.pendingTransfers().length);
  activeCompany = computed(() => {
    const companies = this.auth.availableCompanies();
    const activeId = this.auth.activeCompanyId();
    const co = companies?.find((c: any) => c.company_id === activeId);
    return co?.company_name || 'Empresa Activa';
  });

  uoms = computed(() => this.inv.uoms() || []);
  warehouses = computed(() => this.inv.warehouses() || []);

  // ─── Concept Guards (Signal-Safe) ─────────────────────────────────────────────
  /**
   * INT-TRA concept_id — used for ICT receive flow.
   * Returns null during LOADING to block the submit button.
   */
  readonly transferConceptId = computed(() =>
    this.masterData.resolveConceptByCode('INT-TRA')?.id ?? null
  );

  /**
   * PUR-REC concept_id — used for blind receipts (external supplier delivery).
   * Returns null during LOADING to block the submit button.
   */
  readonly purchaseConceptId = computed(() =>
    this.masterData.resolveConceptByCode('PUR-REC')?.id ?? null
  );

  /** Three-state catalog guard. Bind to button labels for "Configurando Empresa..." state. */
  readonly catalogState = this.masterData.conceptCatalogState;

  // ── Keyboard shortcut: F2 = focus scanner input ───────────────────────────
  @HostListener('keydown.F2')
  onF2() {
    (document.querySelector('input[placeholder*="ICT"]') as HTMLInputElement)?.focus();
  }

  // ── Lifecycle ──────────────────────────────────────────────────────────────
  async ngOnInit() {
    await this.loadPending();
  }

  async loadPending() {
    this.isLoading.set(true);
    try {
      const data = await this.inv.getPendingInboundTransfers();
      this.pendingTransfers.set(data || []);
    } catch (e) {
      this.toast.error('No se pudieron cargar las transferencias pendientes.', 'Inbound');
    } finally {
      this.isLoading.set(false);
    }
  }

  async searchByFolio() {
    const folio = this.folioQuery.trim().toUpperCase();
    if (!folio) return;
    this.isSearching.set(true);
    this.searchError.set('');
    try {
      const result = await this.inv.getTransferByFolio(folio);
      this.selectedTransfer.set(result);
      this.resetReceiveForm();
      playBeep('success');
    } catch (e: any) {
      const msg = e?.error?.message || 'Folio no encontrado.';
      this.searchError.set(msg);
      this.selectedTransfer.set(null);
      playBeep('error');
    } finally {
      this.isSearching.set(false);
    }
  }

  selectTransfer(t: any) {
    this.selectedTransfer.set(t);
    this.resetReceiveForm();
    this.searchError.set('');
    this.folioQuery = t.folio;
  }

  clearSelection() {
    this.selectedTransfer.set(null);
    this.folioQuery = '';
    this.searchError.set('');
    this.resetReceiveForm();
  }

  resetReceiveForm() {
    this.receivedQty = null;
    this.damagedQty = 0;
    this.receiveNotes = '';
  }

  async confirmReceipt() {
    const transfer = this.selectedTransfer();
    if (!transfer || transfer.status !== 'SHIPPED') return;

    // Concept Guard: block if ICT concept not yet loaded
    const conceptId = this.transferConceptId();
    if (!conceptId) {
      this.toast.warning(
        'El catálogo de conceptos aún se está cargando. Por favor intenta en un momento.',
        'Configurando Empresa...'
      );
      return;
    }

    this.isConfirming.set(true);
    try {
      const updated = await this.inv.receiveTransfer(
        transfer.id,
        this.receivedQty ?? undefined,
        this.damagedQty,
        this.receiveNotes || (this.selectedDockId() ? `Recibido en ${this.selectedDockId()}` : undefined),
        conceptId   // ← Inject INT-TRA concept for Kardex traceability
      );

      // Update local state
      this.selectedTransfer.set({ ...transfer, ...updated, status: 'DELIVERED' });
      this.pendingTransfers.update(list => list.filter(t => t.id !== transfer.id));
      this.toast.success(`Folio ${transfer.folio} recibido. Stock actualizado.`, '✅ Recepción Confirmada');
      playBeep('success');
      this.resetReceiveForm();
    } catch (e: any) {
      const msg = e?.error?.message || 'Error al confirmar la recepción.';
      this.toast.error(msg, 'Error de Recepción');
      playBeep('error');
    } finally {
      this.isConfirming.set(false);
    }
  }

  // ── Blind Receipt Methods ──────────────────────────────────────────────────
  openBlindReceipt() {
    this.showBlindReceipt.set(true);
    // Auto-select first warehouse and UOM
    const whs = this.warehouses();
    const uoms = this.uoms();
    if (whs.length > 0) this.blindWarehouseId = whs[0].id;
    if (uoms.length > 0) this.blindUomId = uoms[0].id;
  }

  async confirmBlindReceipt() {
    if (!this.blindSku || !this.blindQty || !this.blindWarehouseId) return;

    // Concept Guard: block if PUR-REC concept not yet loaded
    const conceptId = this.purchaseConceptId();
    if (!conceptId) {
      this.toast.warning(
        'El catálogo de conceptos aún se está cargando. Por favor intenta en un momento.',
        'Configurando Empresa...'
      );
      return;
    }

    this.isConfirming.set(true);
    try {
      const payload = {
        sku: this.blindSku,
        quantity: this.blindQty,
        uom_id: this.blindUomId,
        destination_warehouse_id: this.blindWarehouseId,
        concept_id: conceptId,  // ← PUR-REC injected for Kardex traceability
        notes: `Recibo Directo (Handheld Blind) - Dock: ${this.selectedDockId()}`
      };

      const result = await this.inv.receiveDirect(payload);
      this.toast.success(`Recibo ${result.folio} consolidado correctamente.`, '✅ Direct Receipt');
      this.showBlindReceipt.set(false);
      playBeep('success');

      // Cleanup
      this.blindSku = '';
      this.blindQty = null;
      await this.loadPending();
    } catch (e: any) {
      const msg = e?.error?.message || 'Error en recibo directo.';
      this.toast.error(msg, 'Error Blind');
      playBeep('error');
    } finally {
      this.isConfirming.set(false);
    }
  }
}
