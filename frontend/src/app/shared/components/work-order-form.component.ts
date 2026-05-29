import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { NotificationService } from '../../core/services/notification.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';

@Component({
  selector: 'app-work-order-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">

      <!-- Header -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-violet-500/10 rounded-2xl flex items-center justify-center text-violet-400 border border-violet-500/20">
            <mat-icon class="text-2xl">assignment</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              Nueva Orden de Trabajo
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              MES · ORDEN DE FABRICACIÓN
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
        <form [formGroup]="form" class="space-y-5">

          <!-- Número de orden + Ítem -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">
                No. Orden * <span class="text-primary font-mono">(ERP)</span>
              </label>
              <input type="text" formControlName="order_number"
                placeholder="WO-2026-001"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono font-bold text-primary outline-none focus:border-primary transition-all" />
            </div>
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">SKU / Código ítem *</label>
              <input type="text" formControlName="item_code"
                placeholder="ECM-600"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono font-bold outline-none focus:border-primary transition-all uppercase" />
            </div>
          </div>

          <!-- Cantidad + Fecha compromiso -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Cantidad a fabricar *</label>
              <input type="number" formControlName="order_qty"
                placeholder="500" min="1"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono outline-none focus:border-primary transition-all" />
            </div>
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Fecha compromiso *</label>
              <input type="date" formControlName="due_date"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono outline-none focus:border-primary transition-all" />
            </div>
          </div>

          <!-- Alias / Tipo -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Alias / Referencia</label>
              <input type="text" formControlName="alias"
                placeholder="Lote Junio 2026"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs outline-none focus:border-primary transition-all" />
            </div>
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Tipo</label>
              <select formControlName="wo_type"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs cursor-pointer outline-none focus:border-primary transition-all">
                <option value="">— Sin clasificar —</option>
                <option value="STANDARD">Standard</option>
                <option value="REWORK">Retrabajo</option>
                <option value="PROTOTYPE">Prototipo</option>
              </select>
            </div>
          </div>

          <!-- Info: BOM explode -->
          <div class="p-4 bg-violet-500/5 rounded-xl border border-violet-500/10 flex items-start gap-3">
            <mat-icon class="text-sm text-violet-400 mt-0.5">info</mat-icon>
            <p class="text-[10px] text-surface-text-muted leading-relaxed">
              Al crear la OT se explotan automáticamente los componentes del BOM (si existe en Inventario)
              y se generan líneas <span class="text-violet-400 font-mono font-bold">MATERIAL_INPUT</span> + <span class="text-violet-400 font-mono font-bold">PLANNED_OUTPUT</span>.
            </p>
          </div>

        </form>
      </div>

      <!-- Footer -->
      <div class="pt-8 mt-auto border-t border-surface-border">
        <div class="flex flex-col gap-3">
          <button (click)="save()" [disabled]="form.invalid || saving()"
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic disabled:opacity-50 disabled:pointer-events-none">
            <mat-icon>{{ saving() ? 'sync' : 'verified' }}</mat-icon>
            {{ saving() ? 'Creando orden...' : 'Crear Orden de Trabajo' }}
          </button>
          <button type="button" (click)="drawer.close()"
            class="w-full py-4 border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-surface-border transition-all">
            Cancelar
          </button>
        </div>
      </div>

    </div>
  `,
  styles: [`:host { display: block; }`]
})
export class WorkOrderFormComponent {
  private http   = inject(HttpClient);
  private notif  = inject(NotificationService);
  drawer         = inject(SideDrawerService);
  private fb     = inject(FormBuilder);

  saving = signal(false);
  private base = `${environment.productionUrl}/mes/orders`;

  form: FormGroup = this.fb.group({
    order_number: ['', [Validators.required, Validators.maxLength(50)]],
    item_code:    ['', [Validators.required, Validators.maxLength(50)]],
    order_qty:    [null, [Validators.required, Validators.min(1)]],
    due_date:     ['', Validators.required],
    alias:        [''],
    wo_type:      [''],
  });

  async save() {
    if (this.form.invalid) return;
    this.saving.set(true);
    const v = this.form.value;
    const payload = {
      order_number: v.order_number,
      item_code:    v.item_code.toUpperCase(),
      order_qty:    Number(v.order_qty),
      due_date:     new Date(v.due_date).toISOString(),
      alias:        v.alias || undefined,
      wo_type:      v.wo_type || undefined,
    };
    try {
      await lastValueFrom(this.http.post(this.base + '/', payload));
      this.notif.success('Orden creada', `${v.order_number} — ${v.item_code}`);
      this.drawer.notifyRefresh();
      this.drawer.close();
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'No se pudo crear la orden');
    } finally {
      this.saving.set(false);
    }
  }
}
