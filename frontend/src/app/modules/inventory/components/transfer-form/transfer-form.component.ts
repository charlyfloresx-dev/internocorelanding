// temp_future/src/app/modules/inventory/components/transfer-form/transfer-form.component.ts
import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-transfer-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="glass-form p-8 rounded-2xl border border-white/5 shadow-2xl bg-slate-900/90 backdrop-blur-xl">
      <header class="mb-8 border-l-4 border-amber-500 pl-4">
        <h3 class="text-xl font-black text-white tracking-widest uppercase italic">Transferencia Inter-Almacén</h3>
        <p class="text-xs text-amber-400/80 font-mono italic">OPERACIÓN RESPALDADA POR LOGÍSTICA</p>
      </header>

      <form [formGroup]="transferForm" (ngSubmit)="onSubmit()" class="space-y-6">
        <!-- Origin Company Context (Read-only) -->
        <div class="p-3 bg-amber-500/10 rounded-lg border border-amber-500/20 mb-6">
          <p class="text-[10px] text-amber-500 font-bold uppercase tracking-widest">Empresa Origen (Sesión Activa)</p>
          <p class="text-lg font-mono text-white">{{ activeCompany() }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label class="text-[10px] font-bold text-amber-400 uppercase tracking-tighter">Almacén Origen</label>
            <select formControlName="fromWarehouseId" 
                    class="w-full bg-slate-800/50 border border-white/10 rounded-lg p-3 text-white focus:border-amber-500 outline-none transition-all">
              <option value="">Seleccionar Almacén...</option>
              <!-- Dinámicamente filtrado por empresa activa -->
            </select>
          </div>

          <div class="space-y-2">
            <label class="text-[10px] font-bold text-amber-400 uppercase tracking-tighter">Almacén Destino</label>
            <select formControlName="toWarehouseId" 
                    class="w-full bg-slate-800/50 border border-white/10 rounded-lg p-3 text-white focus:border-amber-500 outline-none transition-all">
              <option value="">Seleccionar Almacén...</option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label class="text-[10px] font-bold text-amber-400 uppercase tracking-tighter">Producto</label>
            <input type="text" formControlName="productId" 
                   class="w-full bg-slate-800/50 border border-white/10 rounded-lg p-3 text-white focus:border-amber-500 outline-none">
          </div>

          <div class="space-y-2">
            <label class="text-[10px] font-bold text-amber-400 uppercase tracking-tighter">Cantidad</label>
            <input type="number" formControlName="quantity" 
                   class="w-full bg-slate-800/50 border border-white/10 rounded-lg p-3 text-white focus:border-amber-500 outline-none">
          </div>
        </div>

        <div class="pt-4 flex justify-end space-x-4">
          <button type="submit" [disabled]="transferForm.invalid"
                  class="px-8 py-3 bg-gradient-to-r from-amber-600 to-orange-700 hover:from-amber-500 hover:to-orange-600 text-white rounded-xl font-black uppercase tracking-[0.2em] shadow-lg shadow-amber-500/20 disabled:opacity-50 transition-all">
            Despachar Transferencia
          </button>
        </div>
      </form>
    </div>
  `
})
export class TransferFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private auth = inject(AuthService);
  
  activeCompany = signal<string>('');
  
  transferForm = this.fb.group({
    fromWarehouseId: ['', Validators.required],
    toWarehouseId: ['', Validators.required],
    productId: ['', Validators.required],
    quantity: [0, [Validators.required, Validators.min(1)]]
  });

  ngOnInit() {
    this.activeCompany.set(this.auth.session()?.company_id || 'UNKNOWN');
  }

  onSubmit() {
    if (this.transferForm.valid) {
      console.log('Sending transfer request...');
    }
  }
}
