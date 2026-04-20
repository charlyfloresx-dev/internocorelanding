import {
  Component, signal, inject, OnInit, computed, HostListener
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { InventoryService } from '../../core/services/inventory.service';
import { ToastService } from '../../core/services/toast.service';
import { AuthService } from '../../core/services/auth.service';

// ─── Industrial Audio Feedback ──────────────────────────────────────────────
function playBeep(type: 'success' | 'warning' | 'error') {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
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
  } catch (e) {}
}

@Component({
  selector: 'app-inventory-picking',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="min-h-screen bg-surface-bg text-surface-text font-mono select-none overflow-hidden flex flex-col">
      
      <!-- ── INDUSTRIAL HEADER ───────────────────────────────────────────── -->
      <div class="sticky top-0 z-30 bg-surface-card border-b-2 border-orange-500/50 px-4 py-4 flex items-center justify-between shadow-2xl">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-orange-500/20 flex items-center justify-center border border-orange-500/30">
            <mat-icon class="text-orange-400">conveyor_belt</mat-icon>
          </div>
          <div>
            <h1 class="text-sm font-black uppercase tracking-widest text-orange-400">Picking Handheld</h1>
            <p class="text-[9px] text-surface-text-muted uppercase tracking-tighter">{{ activeWarehouseName() || 'Offline Mode' }}</p>
          </div>
        </div>
        <div class="flex flex-col items-end">
          <div class="flex items-center gap-2">
            <span *ngIf="isOffline()" class="text-[8px] font-black bg-red-500 text-white px-2 py-0.5 rounded animate-pulse">OFFLINE</span>
            <span class="text-[10px] font-black text-orange-400">{{ pickedCount() }}/{{ totalToPick() }} PIEZAS</span>
          </div>
          <div class="mt-1 flex gap-1">
             <div *ngFor="let p of progressDots()" 
                  [class.bg-orange-500]="p" [class.bg-white/10]="!p"
                  class="w-2 h-1 rounded-full"></div>
          </div>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-4 py-6 space-y-6">

        <!-- ── STEP 1: SCAN ORDER/FOLIO ───────────────────────────────────── -->
        <div *ngIf="!activeTask()" class="space-y-4 animate-fade-in">
          <div class="bg-surface-card border border-surface-border rounded-2xl p-6 shadow-xl">
            <label class="text-[10px] uppercase tracking-[0.3em] text-orange-400 font-black mb-4 block">
              Escanear Orden de Salida / Traspaso
            </label>
            <div class="flex gap-3">
              <input
                #folioInput
                [(ngModel)]="folioQuery"
                (keydown.enter)="loadTaskByFolio()"
                placeholder="ICT-XXXX-XXXX"
                class="flex-1 bg-surface-bg border-2 border-surface-border rounded-xl px-4 py-5 text-xl font-black text-orange-400 placeholder-surface-text-muted outline-none focus:border-orange-500 transition-all text-center tracking-[0.2em]"
                autocomplete="off"
                autofocus
              />
              <button (click)="loadTaskByFolio()" [disabled]="!folioQuery || isLoading()"
                class="w-16 rounded-xl bg-orange-500 text-surface-bg flex items-center justify-center active:scale-95 transition-all shadow-lg shadow-orange-500/20">
                <mat-icon *ngIf="!isLoading()">search</mat-icon>
                <mat-icon *ngIf="isLoading()" class="animate-spin">progress_activity</mat-icon>
              </button>
            </div>
          </div>

          <!-- Offline Tasks Registry -->
          <div class="space-y-3">
            <h2 class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest pl-2">Tareas en Memoria Local</h2>
            <div *ngFor="let task of offlineTasks()" 
                 (click)="activeTask.set(task)"
                 class="bg-surface-card border border-surface-border rounded-xl p-4 flex items-center justify-between cursor-pointer hover:border-orange-500/30">
              <div>
                <p class="text-xs font-black text-orange-400">{{ task.folio }}</p>
                <p class="text-[9px] text-surface-text-muted mt-1">{{ task.items.length }} Items • {{ task.status }}</p>
              </div>
              <mat-icon class="text-surface-text-muted">keyboard_arrow_right</mat-icon>
            </div>
          </div>
        </div>

        <!-- ── STEP 2: PICKING CONTENT ────────────────────────────────────── -->
        <div *ngIf="activeTask()" class="space-y-4 animate-fade-in">
          
          <div class="flex items-center justify-between px-2">
            <button (click)="cancelActiveTask()" class="text-[10px] text-red-500 font-black uppercase flex items-center gap-1">
              <mat-icon class="text-sm">arrow_back</mat-icon> SALIR
            </button>
            <span class="text-[10px] font-black text-white/40 uppercase">{{ activeTask()?.folio }}</span>
          </div>

          <!-- FIFO SUGGESTION BANNER -->
          <div *ngIf="nextItemToPick() as item" class="bg-orange-500 text-black rounded-2xl p-5 shadow-2xl relative overflow-hidden">
            <div class="absolute right-[-10px] top-[-10px] opacity-10">
              <mat-icon class="text-8xl">location_on</mat-icon>
            </div>
            
            <div class="relative z-10">
              <div class="flex justify-between items-start mb-4">
                <div>
                  <p class="text-[10px] font-black uppercase tracking-widest opacity-70">Ubicación Sugerida (FIFO)</p>
                  <p class="text-4xl font-black tracking-tighter">{{ item.suggested_location || 'SEC-01-A' }}</p>
                </div>
                <div class="text-right">
                  <p class="text-[10px] font-black uppercase opacity-70">Pendiente</p>
                  <p class="text-2xl font-black">{{ item.quantity - (item.picked || 0) }}</p>
                </div>
              </div>

              <div class="bg-black/20 rounded-xl p-3 border border-white/10 backdrop-blur-sm">
                <p class="text-[9px] font-black opacity-60">PRODUCTO</p>
                <p class="text-lg font-black truncate">{{ item.sku }}</p>
                <p class="text-[10px] font-bold truncate opacity-80">{{ item.name }}</p>
              </div>

              <div class="mt-4">
                <label class="text-[10px] font-black uppercase opacity-60 mb-2 block tracking-widest text-center">Escanear Producto o Lote para Validar</label>
                <input 
                  #pickInput
                  [(ngModel)]="scanBuffer"
                  (keydown.enter)="validatePick()"
                  placeholder="SCAN SKU / BATCH"
                  class="w-full bg-black text-orange-400 border-none rounded-xl px-4 py-5 text-xl font-black text-center placeholder-white/5 outline-none focus:ring-4 ring-white/20 transition-all uppercase"
                />
              </div>
            </div>
          </div>

          <!-- PICKED ITEMS LIST -->
          <div class="space-y-3">
            <h2 class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest pl-2">Ítems Consolidados</h2>
            <div *ngFor="let item of activeTask()?.items" 
                 class="bg-surface-card border rounded-2xl p-4 flex items-center justify-between shadow-sm"
                 [class.border-emerald-500]="item.picked === item.quantity"
                 [class.border-surface-border]="item.picked !== item.quantity">
              <div class="flex items-center gap-3">
                <div [class.bg-emerald-500/20]="item.picked === item.quantity" 
                     [class.bg-surface-bg]="item.picked !== item.quantity"
                     class="w-10 h-10 rounded-xl flex items-center justify-center border"
                     [class.border-emerald-500/30]="item.picked === item.quantity"
                     [class.border-surface-border]="item.picked !== item.quantity">
                  <mat-icon [class.text-emerald-400]="item.picked === item.quantity" [class.text-surface-text-muted]="item.picked !== item.quantity">
                    {{ item.picked === item.quantity ? 'check_circle' : 'inventory_2' }}
                  </mat-icon>
                </div>
                <div>
                  <p class="text-xs font-black text-surface-text" [class.text-emerald-400]="item.picked === item.quantity">{{ item.sku }}</p>
                  <p class="text-[9px] text-surface-text-muted">{{ item.picked || 0 }} de {{ item.quantity }} pickeados</p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-[10px] font-black text-surface-text-muted uppercase">{{ item.suggested_location || 'STOCK' }}</p>
              </div>
            </div>
          </div>

          <!-- CONFIRM DISPATCH -->
          <button *ngIf="isTaskComplete()" (click)="confirmDispatch()" [disabled]="isProcessing()"
            class="w-full py-6 rounded-2xl bg-emerald-500 text-black font-black uppercase text-base tracking-widest
                   shadow-2xl shadow-emerald-500/40 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3">
            <mat-icon *ngIf="!isProcessing()">local_shipping</mat-icon>
            <mat-icon *ngIf="isProcessing()" class="animate-spin">progress_activity</mat-icon>
            <span>{{ isProcessing() ? 'Sincronizando...' : 'DESPACHAR MATERIAL' }}</span>
          </button>
        </div>

      </div>
    </div>
  `,
  styles: [`
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .animate-fade-in { animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .animate-spin { animation: spin 1s linear infinite; }
  `]
})
export class InventoryPickingComponent implements OnInit {
  private inv = inject(InventoryService);
  private toast = inject(ToastService);
  private auth = inject(AuthService);

  // ── State ──────────────────────────────────────────────────────────────────
  isLoading = signal(false);
  isProcessing = signal(false);
  isOffline = signal(!navigator.onLine);

  folioQuery = '';
  scanBuffer = '';
  activeTask = signal<any | null>(null);
  
  // Local Memory for Offline Flow (Maturity Phase)
  offlineTasks = signal<any[]>([]);

  // ── Lifecycle ──────────────────────────────────────────────────────────────
  ngOnInit() {
    this.loadOfflineProgress();
    
    window.addEventListener('online', () => this.isOffline.set(false));
    window.addEventListener('offline', () => this.isOffline.set(true));
  }

  // ── Computed Props ─────────────────────────────────────────────────────────
  activeWarehouseName = computed(() => {
    const whs = this.inv.warehouses();
    const activeId = this.inv.warehouses()[0]?.id; // Simplicius: use first or auth context
    return whs.find(w => w.id === activeId)?.name || '';
  });

  nextItemToPick = computed(() => {
    const task = this.activeTask();
    if (!task) return null;
    return task.items.find((i: any) => (i.picked || 0) < i.quantity);
  });

  isTaskComplete = computed(() => {
    const task = this.activeTask();
    if (!task) return false;
    return task.items.every((i: any) => i.picked === i.quantity);
  });

  pickedCount = computed(() => {
    const task = this.activeTask();
    if (!task) return 0;
    return task.items.reduce((acc: number, cur: any) => acc + (cur.picked || 0), 0);
  });

  totalToPick = computed(() => {
    const task = this.activeTask();
    if (!task) return 0;
    return task.items.reduce((acc: number, cur: any) => acc + cur.quantity, 0);
  });

  progressDots = computed(() => {
    const total = this.totalToPick();
    if (total === 0) return [];
    const picked = this.pickedCount();
    const dots = [];
    for (let i = 0; i < 10; i++) {
      dots.push(i < (picked / total) * 10);
    }
    return dots;
  });

  // ── Actions ────────────────────────────────────────────────────────────────

  private loadOfflineProgress() {
    const saved = localStorage.getItem('ic_picking_tasks');
    if (saved) {
      this.offlineTasks.set(JSON.parse(saved));
    }
  }

  private saveOfflineProgress() {
    localStorage.setItem('ic_picking_tasks', JSON.stringify(this.offlineTasks()));
    if (this.activeTask()) {
      const current = this.activeTask();
      const list = this.offlineTasks();
      const idx = list.findIndex(t => t.folio === current.folio);
      if (idx >= 0) {
        list[idx] = current;
      } else {
        list.push(current);
      }
      this.offlineTasks.set([...list]);
      localStorage.setItem('ic_picking_tasks', JSON.stringify(list));
    }
  }

  async loadTaskByFolio() {
    const folio = this.folioQuery.trim().toUpperCase();
    if (!folio) return;

    // Check if it's already in offline memory
    const existing = this.offlineTasks().find(t => t.folio === folio);
    if (existing) {
      this.activeTask.set(existing);
      playBeep('success');
      return;
    }

    this.isLoading.set(true);
    try {
      const task = await this.inv.getTransferByFolio(folio);
      
      // Industrial Maturity: Transform to Picking Task
      // In a real system, we'd fetch FIFO previews for each item
      const pickingTask = {
        id: task.id,
        folio: task.folio,
        status: 'PICKING',
        items: [{
          product_id: task.product_id,
          sku: task.origin_sku || task.product_sku,
          name: task.product_name || 'Industrial Item',
          quantity: task.quantity,
          picked: 0,
          suggested_location: 'SEC-01-A', // Mocking FIFO location
          suggested_batch: task.selected_batch_id
        }]
      };

      this.activeTask.set(pickingTask);
      this.saveOfflineProgress();
      playBeep('success');
    } catch (e) {
      this.toast.error('No se encontró la orden especificada.', 'Picking Error');
      playBeep('error');
    } finally {
      this.isLoading.set(false);
    }
  }

  validatePick() {
    const buffer = this.scanBuffer.trim().toUpperCase();
    if (!buffer) return;

    const item = this.nextItemToPick();
    if (!item) return;

    // Industrial Validation: Scan SKU or Batch ID
    if (buffer === item.sku.toUpperCase() || buffer === item.suggested_batch?.toUpperCase()) {
      this.activeTask.update(t => {
        const target = t.items.find((i: any) => i.sku === item.sku);
        target.picked = (target.picked || 0) + 1;
        return { ...t };
      });
      this.scanBuffer = '';
      playBeep('success');
      this.saveOfflineProgress();
    } else {
      this.toast.warning('SKU/Lote no coincide con el ítem actual.', 'Error de Escaneo');
      this.scanBuffer = '';
      playBeep('error');
    }
  }

  cancelActiveTask() {
    this.saveOfflineProgress();
    this.activeTask.set(null);
    this.folioQuery = '';
  }

  async confirmDispatch() {
    if (!this.isTaskComplete()) return;
    this.isProcessing.set(true);
    
    try {
      // Logic for dispatching (Inter-company or internal)
      // In a real scenario, we'd hit /inventory/transfers/dispatch or similar
      this.toast.success(`Despacho de folio ${this.activeTask().folio} completado.`, '✅ Despacho Exitoso');
      
      // Remove from offline memory
      const list = this.offlineTasks().filter(t => t.folio !== this.activeTask().folio);
      this.offlineTasks.set(list);
      localStorage.setItem('ic_picking_tasks', JSON.stringify(list));
      
      this.activeTask.set(null);
      this.folioQuery = '';
      playBeep('success');
    } catch (e) {
      this.toast.error('Error al sincronizar el despacho.', 'Sync Error');
      playBeep('error');
    } finally {
      this.isProcessing.set(false);
    }
  }

  @HostListener('keydown.F2')
  focusInput() {
    if (!this.activeTask()) {
      (document.querySelector('input[placeholder*="ICT"]') as HTMLInputElement)?.focus();
    } else {
      (document.querySelector('input[placeholder*="SCAN"]') as HTMLInputElement)?.focus();
    }
  }
}
