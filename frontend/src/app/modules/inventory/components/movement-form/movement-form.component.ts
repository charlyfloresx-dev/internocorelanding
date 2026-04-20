// temp_future/src/app/modules/inventory/components/movement-form/movement-form.component.ts
import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-movement-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="glass-form p-8 rounded-2xl border border-white/5 shadow-2xl bg-slate-900/90 backdrop-blur-xl">
      <header class="mb-8 border-l-4 border-cyan-500 pl-4">
        <h3 class="text-xl font-black text-white tracking-widest uppercase italic">Nuevo Movimiento de Inventario</h3>
        <p class="text-xs text-cyan-400/80 font-mono">ID TRANSACCIÓN: {{ requestId() }}</p>
      </header>

      <form [formGroup]="movementForm" (ngSubmit)="onSubmit()" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-tighter">Tipo de Movimiento</label>
            <select formControlName="type" 
                    class="w-full bg-slate-800/50 border border-white/10 rounded-lg p-3 text-white focus:border-cyan-500 outline-none transition-all">
              <option value="IN">ENTRADA (+)</option>
              <option value="OUT">SALIDA (-)</option>
              <option value="ADJUST">AJUSTE</option>
            </select>
          </div>

          <div class="space-y-2">
            <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-tighter">Producto (SKU/ID)</label>
            <input type="text" formControlName="productId" 
                   class="w-full bg-slate-800/50 border border-white/10 rounded-lg p-3 text-white focus:border-cyan-500 outline-none placeholder:text-slate-500">
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-tighter">Cantidad</label>
            <input type="number" formControlName="quantity" 
                   class="w-full bg-slate-800/50 border border-white/10 rounded-lg p-3 text-white focus:border-cyan-500 outline-none">
          </div>

          <div class="space-y-2">
            <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-tighter">Almacén</label>
            <input type="text" formControlName="warehouseId" 
                   class="w-full bg-slate-800/50 border border-white/10 rounded-lg p-3 text-white focus:border-cyan-500 outline-none">
          </div>
        </div>

        <div class="pt-4 flex justify-end space-x-4">
          <button type="button" (click)="resetForm()" 
                  class="px-6 py-2 text-slate-400 hover:text-white transition-colors text-xs font-bold uppercase tracking-widest">
            Cancelar
          </button>
          <button type="submit" [disabled]="movementForm.invalid"
                  class="px-8 py-3 bg-gradient-to-r from-cyan-600 to-blue-700 hover:from-cyan-500 hover:to-blue-600 text-white rounded-xl font-black uppercase tracking-[0.2em] shadow-lg shadow-cyan-500/20 disabled:opacity-50 transition-all">
            Ejecutar Comando
          </button>
        </div>
      </form>
    </div>
  `
})
export class MovementFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  
  requestId = signal<string>('');
  
  movementForm = this.fb.group({
    type: ['IN', Validators.required],
    productId: ['', Validators.required],
    quantity: [0, [Validators.required, Validators.min(0.0001)]],
    warehouseId: ['', Validators.required],
    notes: ['']
  });

  ngOnInit() {
    this.resetForm();
  }

  resetForm() {
    this.movementForm.reset({ type: 'IN', quantity: 0 });
    // Zero Trust / Idempotency: Generate ID on init
    this.requestId.set(crypto.randomUUID());
  }

  onSubmit() {
    if (this.movementForm.valid) {
      console.log('Sending transaction:', {
        ...this.movementForm.value,
        client_request_id: this.requestId()
      });
      // Here would be the call to InventoryService
    }
  }
}
