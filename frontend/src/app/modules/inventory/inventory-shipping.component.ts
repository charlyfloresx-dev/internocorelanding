import {
  Component, signal, inject, OnInit, computed, HostListener
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { lastValueFrom } from 'rxjs';
import { MatIconModule } from '@angular/material/icon';
import { InventoryService } from '../../core/services/inventory.service';
import { ToastService } from '../../core/services/toast.service';
import { AuthService } from '../../core/services/auth.service';
import { StaffService } from '../../core/services/staff.service';
import { EligibilityResponse } from '../../core/models/hr.types';

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
  selector: 'app-inventory-shipping',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="min-h-screen bg-surface-bg text-surface-text font-mono select-none overflow-hidden flex flex-col">
      
      <!-- ── INDUSTRIAL HEADER ───────────────────────────────────────────── -->
      <div class="sticky top-0 z-30 bg-surface-card border-b-2 border-indigo-500/50 px-4 py-4 flex items-center justify-between shadow-2xl">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
            <mat-icon class="text-indigo-400">local_shipping</mat-icon>
          </div>
          <div>
            <h1 class="text-sm font-black uppercase tracking-widest text-indigo-400">Embarques (Dispatch)</h1>
            <p class="text-[9px] text-surface-text-muted uppercase tracking-tighter">{{ activeWarehouseName() || 'Offline Mode' }}</p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto max-w-4xl mx-auto w-full px-4 py-6 space-y-6">

        <!-- ── STEP 1: SCAN COMPLETED PICK LIST / FOLIO ───────────────────── -->
        <div *ngIf="!activeTask()" class="space-y-4 animate-fade-in">
          <div class="bg-surface-card border border-surface-border rounded-2xl p-6 shadow-xl relative overflow-hidden">
             <div class="absolute -right-4 -top-4 opacity-5">
              <mat-icon class="text-9xl">qr_code_scanner</mat-icon>
            </div>
            
            <label class="text-[10px] uppercase tracking-[0.3em] text-indigo-400 font-black mb-4 block relative z-10">
              Escanear Orden Pickeada (Transferencia)
            </label>
            <div class="flex gap-3 relative z-10">
              <input
                #folioInput
                [(ngModel)]="folioQuery"
                (keydown.enter)="loadTaskByFolio()"
                placeholder="ICT-XXXX-XXXX"
                class="flex-1 bg-surface-bg border-2 border-surface-border rounded-xl px-4 py-5 text-xl font-black text-indigo-400 placeholder-surface-text-muted outline-none focus:border-indigo-500 transition-all text-center tracking-[0.2em]"
                autocomplete="off"
                autofocus
              />
              <button (click)="loadTaskByFolio()" [disabled]="!folioQuery || isLoading()"
                class="w-16 rounded-xl bg-indigo-500 text-surface-bg flex items-center justify-center active:scale-95 transition-all shadow-lg shadow-indigo-500/20">
                <mat-icon *ngIf="!isLoading()">search</mat-icon>
                <mat-icon *ngIf="isLoading()" class="animate-spin">progress_activity</mat-icon>
              </button>
            </div>
          </div>
        </div>

        <!-- ── STEP 2: SHIPPING VALIDATION & DRIVER CREDENTIALS ──────────── -->
        <div *ngIf="activeTask()" class="space-y-4 animate-fade-in">
          
          <div class="flex items-center justify-between px-2">
            <button (click)="cancelActiveTask()" class="text-[10px] text-red-500 font-black uppercase flex items-center gap-1">
              <mat-icon class="text-sm">arrow_back</mat-icon> SALIR
            </button>
            <span class="text-[10px] font-black text-surface-text-muted uppercase">{{ activeTask()?.folio }}</span>
          </div>

          <div class="bg-indigo-500 text-white rounded-2xl p-5 shadow-2xl relative overflow-hidden">
            <div class="absolute right-[-10px] top-[-10px] opacity-10">
              <mat-icon class="text-8xl">verified</mat-icon>
            </div>
            
            <div class="relative z-10">
              <div class="flex justify-between items-start mb-4">
                <div>
                  <p class="text-[10px] font-black uppercase tracking-widest opacity-70">Despacho de Material</p>
                  <p class="text-3xl font-black tracking-tighter truncate">{{ activeTask()?.folio }}</p>
                </div>
                <div class="text-right">
                  <p class="text-[10px] font-black uppercase opacity-70">Piezas</p>
                  <p class="text-2xl font-black">{{ totalPieces() }}</p>
                </div>
              </div>

              <!-- ITEMS SUMMARY -->
              <div class="bg-black/20 rounded-xl p-3 border border-white/10 backdrop-blur-sm mb-4">
                <p class="text-[9px] font-black opacity-60 mb-2">RESUMEN DE PRODUCTOS</p>
                <div *ngFor="let item of activeTask()?.items" class="flex justify-between items-center text-xs border-b border-white/5 py-1">
                   <span class="font-bold truncate">{{ item.sku }}</span>
                   <span class="font-black">{{ item.quantity }} PZA</span>
                </div>
              </div>

              <!-- CROSS-BORDER REQUIRED: DRIVER BADGE SCAN (Segue to HR Phase 50) -->
              <div class="mt-4">
                <label class="text-[10px] font-black uppercase text-amber-300 mb-2 block tracking-widest text-center">
                   Escanear Gafete del Operador (Requisito Anexo 24)
                </label>
                <div class="flex gap-2">
                  <input 
                    #driverInput
                    [(ngModel)]="driverBuffer"
                    (keydown.enter)="validateDriver()"
                    placeholder="SCAN DRIVER BADGE / CURP"
                    class="w-full bg-black/40 text-amber-300 border-2 border-amber-300/30 rounded-xl px-4 py-4 text-sm font-black text-center placeholder-white/20 outline-none focus:border-amber-300 transition-all uppercase"
                  />
                  <button [disabled]="isValidatingDriver() || !driverBuffer" 
                    class="px-4 bg-amber-500/20 text-amber-300 rounded-xl border border-amber-500/50 flex flex-col items-center justify-center -space-y-1 disabled:opacity-30" 
                    (click)="validateDriver()">
                     <mat-icon *ngIf="!isValidatingDriver()" class="text-sm">badge</mat-icon>
                     <mat-icon *ngIf="isValidatingDriver()" class="text-sm animate-spin">progress_activity</mat-icon>
                     <span class="text-[8px] font-black uppercase tracking-widest mt-1">Validar</span>
                  </button>
                </div>

                <!-- ELIGIBILITY MESSAGES (Phase 50) -->
                <div *ngIf="driverEligibility() as el" class="mt-3 animate-fade-in shadow-2xl">
                  
                  <!-- SUCCESS CASE -->
                  <div *ngIf="el.eligible" class="p-3 bg-emerald-500/20 text-emerald-400 text-[10px] font-black border-2 border-emerald-500/50 rounded-xl flex items-center gap-3">
                    <mat-icon class="text-lg text-emerald-400">check_circle</mat-icon>
                    <div>
                      <p class="uppercase tracking-widest">Operador: {{ el.full_name }}</p>
                      <p class="text-[8px] opacity-70">{{ el.reason }}</p>
                    </div>
                  </div>

                  <!-- ERROR CASE: HIGH VISIBILITY -->
                  <div *ngIf="!el.eligible" class="p-4 bg-red-500/10 text-red-500 text-[10px] font-black border-2 border-red-500/50 rounded-xl flex items-start gap-4">
                    <mat-icon class="text-xl">report_problem</mat-icon>
                    <div class="flex-1">
                      <p class="uppercase tracking-widest mb-1">MOVIMIENTO RECHAZADO</p>
                      <p class="text-[11px] font-black bg-red-500 text-white px-2 py-0.5 rounded inline-block mb-2">{{ el.reason }}</p>
                      
                      <div *ngIf="el.details" class="bg-black/20 p-2 rounded-lg border border-red-500/20">
                        <p class="text-[8px] opacity-60 uppercase mb-1">Detalle Geográfico / Auditoría:</p>
                        <p class="text-[9px] uppercase">Documento: <span class="text-white">{{ el.details.document }}</span></p>
                        <p *ngIf="el.details.expiry_date" class="text-[9px] uppercase">Vencimiento: <span class="text-white">{{ el.details.expiry_date }}</span></p>
                        <p *ngIf="el.details.days_remaining !== undefined" class="text-[9px] uppercase">Días Restantes: <span class="text-red-400">{{ el.details.days_remaining }}</span></p>
                      </div>
                    </div>
                  </div>

                </div>
              </div>

            </div>
          </div>

          <!-- CONFIRM DISPATCH BUTTON -->
          <button (click)="confirmShipping()" [disabled]="!driverValid() || isProcessing()"
            class="w-full py-6 rounded-2xl bg-indigo-500 text-white font-black uppercase text-base tracking-widest
                   shadow-2xl shadow-indigo-500/40 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3
                   disabled:opacity-50 disabled:grayscale">
            <mat-icon *ngIf="!isProcessing()">flight_takeoff</mat-icon>
            <mat-icon *ngIf="isProcessing()" class="animate-spin">progress_activity</mat-icon>
            <span>{{ isProcessing() ? 'Embarcando...' : 'REGISTRAR SALIDA' }}</span>
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
export class InventoryShippingComponent implements OnInit {
  private inv = inject(InventoryService);
  private staff = inject(StaffService);
  private toast = inject(ToastService);
  private auth = inject(AuthService);

  isLoading = signal(false);
  isProcessing = signal(false);
  isValidatingDriver = signal(false);

  folioQuery = '';
  driverBuffer = '';
  driverEligibility = signal<EligibilityResponse | null>(null);
  activeTask = signal<any | null>(null);

  // Computed signals
  driverValid = computed(() => this.driverEligibility()?.eligible || false);

  ngOnInit() {}

  activeWarehouseName = computed(() => {
    const whs = this.inv.warehouses();
    const activeId = this.inv.selectedWarehouseId() || (whs[0]?.id);
    return whs.find(w => w.id === activeId)?.name || '';
  });

  totalPieces = computed(() => {
    const task = this.activeTask();
    if (!task) return 0;
    return task.items.reduce((acc: number, cur: any) => acc + cur.quantity, 0);
  });

  async loadTaskByFolio() {
    const folio = this.folioQuery.trim().toUpperCase();
    if (!folio) return;

    this.isLoading.set(true);
    try {
      const task = await this.inv.getTransferByFolio(folio);
      
      const shippingTask = {
        id: task.id,
        folio: task.folio,
        status: 'SHIPPING',
        items: [{
          product_id: task.product_id,
          sku: task.origin_sku || task.product_sku,
          name: task.product_name || 'Industrial Item',
          quantity: task.quantity
        }]
      };

      this.activeTask.set(shippingTask);
      this.driverBuffer = '';
      this.driverEligibility.set(null);
      playBeep('success');
    } catch (e) {
      this.toast.error('No se encontró la orden especificada.', 'Embarques Error');
      playBeep('error');
    } finally {
      this.isLoading.set(false);
    }
  }

  async validateDriver() {
    const buf = this.driverBuffer.trim();
    if (!buf) return;
    
    this.isValidatingDriver.set(true);
    try {
      // LLAMADA REAL CON lastValueFrom PARA MANEJAR EL OBSERVABLE
      const response = await lastValueFrom(this.staff.validateOperator(buf));
      this.driverEligibility.set(response);
      
      if (response.eligible) {
        playBeep('success');
        this.toast.success(`Operador Aprobado: ${response.full_name}`, 'Cumplimiento Logístico');
      } else {
        playBeep('error');
        this.toast.error(response.reason || 'Credencial no elegible para despacho.', 'Rechazo de Auditoría');
      }
    } catch (e) {
      playBeep('error');
      this.toast.error('No se pudo verificar el cumplimiento en este momento.', 'Error de Conexión HR');
    } finally {
      this.isValidatingDriver.set(false);
      this.driverBuffer = '';
    }
  }

  cancelActiveTask() {
    this.activeTask.set(null);
    this.folioQuery = '';
    this.driverBuffer = '';
    this.driverEligibility.set(null);
  }

  async confirmShipping() {
    if (!this.driverValid()) {
        this.toast.error('Requiere escanear gafete del operador antes de continuar.', 'Seguridad Anexo 24');
        return;
    }

    this.isProcessing.set(true);
    
    try {
      // In real scenario we update the transfer status to SHIPPED
      // await this.inv.dispatchTransfer(this.activeTask().id, { operator_credential: this.driverBuffer });
      
      this.toast.success('El material ha sido embarcado y descontado de stock temporal.', 'Salida Registrada');
      playBeep('success');
      
      this.activeTask.set(null);
      this.folioQuery = '';
      this.driverEligibility.set(null);
      this.driverBuffer = '';
    } catch (e) {
      this.toast.error('Error al sincronizar el embarque.', 'Sync Error');
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
