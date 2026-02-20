
import { Component, inject, OnInit, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators, FormArray } from '@angular/forms';
import { InventoryService } from '@services/inventory.service';
import { ConceptType, CreateDocumentCommand } from '@models/api.types';

@Component({
  selector: 'app-inventory-document-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  template: `
    <div class="min-h-screen bg-slate-950 pb-20">
      
      <!-- Top Bar -->
      <div class="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6 sticky top-0 z-40">
        <div class="flex items-center gap-4">
          <button (click)="cancel()" class="w-8 h-8 rounded-full hover:bg-slate-800 text-slate-400 flex items-center justify-center transition-colors">
            <i class="fa-solid fa-arrow-left"></i>
          </button>
          <h1 class="text-xl font-bold text-white">Nuevo Documento</h1>
        </div>
        <div class="flex items-center gap-3">
          <div class="text-right mr-4 hidden sm:block">
             <div class="text-[10px] text-slate-500 uppercase font-bold">Total Documento</div>
             <div class="text-xl font-mono font-bold text-white">{{ total() | currency }}</div>
          </div>
          <button (click)="submit()" [disabled]="form.invalid || movements.length === 0" 
                  class="bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-2 px-6 rounded-lg shadow-lg shadow-green-900/20 transition-all flex items-center gap-2">
             <i class="fa-solid fa-check"></i> Confirmar
          </button>
        </div>
      </div>

      <div class="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- LEFT COL: HEADER FORM -->
        <div class="lg:col-span-4 space-y-6">
          
          <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
            <h3 class="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4 border-b border-slate-800 pb-2">Encabezado</h3>
            
            <form [formGroup]="form" class="space-y-4">
              
              <!-- CONCEPT (DRIVER) -->
              <div>
                 <label class="block text-slate-300 text-sm font-bold mb-2">Concepto *</label>
                 <select formControlName="conceptId" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-white focus:border-sky-500 outline-none transition-colors">
                    <option value="" disabled>Seleccione...</option>
                    @for (c of service.concepts(); track c.id) {
                      <option [value]="c.id">{{ c.name }}</option>
                    }
                 </select>
                 
                 <!-- Concept Visual Feedback -->
                 @if (selectedConcept(); as concept) {
                   <div [class]="concept.type === 1 
                        ? 'mt-2 p-2 bg-green-500/10 border border-green-500/20 rounded text-xs text-green-400 flex items-center gap-2'
                        : 'mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400 flex items-center gap-2'">
                      <i [class]="concept.type === 1 ? 'fa-solid fa-arrow-right' : 'fa-solid fa-arrow-left'"></i>
                      <span class="font-bold">{{ concept.type === 1 ? 'ENTRADA DE MERCANCÍA' : 'SALIDA DE MERCANCÍA' }}</span>
                   </div>
                 }
              </div>

              <!-- WAREHOUSE -->
              <div>
                 <label class="block text-slate-300 text-sm font-bold mb-2">Almacén *</label>
                 <select formControlName="warehouseId" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-white focus:border-sky-500 outline-none transition-colors">
                    @for (w of service.warehouses(); track w.id) {
                      <option [value]="w.id">{{ w.name }}</option>
                    }
                 </select>
              </div>

              <!-- PARTNER (Conditional) -->
              <div>
                 <label class="block text-slate-300 text-sm font-bold mb-2">Socio Comercial</label>
                 <select formControlName="partnershipId" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-white focus:border-sky-500 outline-none transition-colors">
                    <option value="">(Opcional / Interno)</option>
                    @for (p of service.partnerships(); track p.id) {
                      <option [value]="p.id">{{ p.name }} ({{ p.type === 1 ? 'Cliente' : 'Proveedor' }})</option>
                    }
                 </select>
              </div>

              <!-- DATE & REF -->
              <div class="grid grid-cols-2 gap-4">
                 <div>
                    <label class="block text-slate-300 text-xs font-bold mb-2">Fecha</label>
                    <input type="date" formControlName="deliveryDate" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-white focus:border-sky-500 outline-none">
                 </div>
                 <div>
                    <label class="block text-slate-300 text-xs font-bold mb-2">Referencia</label>
                    <input type="text" formControlName="reference" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-white focus:border-sky-500 outline-none" placeholder="Factura, Pedido...">
                 </div>
              </div>
              
              <div>
                 <label class="block text-slate-300 text-xs font-bold mb-2">Descripción</label>
                 <textarea formControlName="description" rows="3" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-white focus:border-sky-500 outline-none"></textarea>
              </div>

            </form>
          </div>
          
          <!-- Summary Card -->
          <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
             <div class="flex justify-between items-center mb-2">
               <span class="text-slate-400 text-sm">Subtotal</span>
               <span class="text-white font-mono">{{ subtotal() | currency }}</span>
             </div>
             <div class="flex justify-between items-center mb-2">
               <span class="text-slate-400 text-sm">Impuestos (16%)</span>
               <span class="text-white font-mono">{{ tax() | currency }}</span>
             </div>
             <div class="border-t border-slate-800 mt-4 pt-4 flex justify-between items-center">
               <span class="text-white font-bold text-lg">Total</span>
               <span class="text-sky-400 font-bold font-mono text-xl">{{ total() | currency }}</span>
             </div>
          </div>

        </div>

        <!-- RIGHT COL: MOVEMENTS GRID -->
        <div class="lg:col-span-8 flex flex-col h-full min-h-[500px] bg-slate-900 border border-slate-800 rounded-xl shadow-lg overflow-hidden">
           
           <!-- Toolbar -->
           <div class="p-4 border-b border-slate-800 bg-slate-900 flex justify-between items-center">
             <h3 class="text-slate-400 text-xs font-bold uppercase tracking-widest">Partidas del Documento</h3>
             
             <!-- Quick Add Form (Inline) -->
             <div class="hidden md:flex gap-2">
                <!-- Using a simplified approach: Button triggers a modal or enables a row -->
             </div>
           </div>

           <!-- Table -->
           <div class="flex-1 overflow-x-auto">
             <table class="w-full text-left text-sm text-slate-300">
               <thead class="bg-slate-950 text-slate-500 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-800">
                 <tr>
                   <th class="px-4 py-3 w-10">#</th>
                   <th class="px-4 py-3">Producto</th>
                   <th class="px-4 py-3 w-24 text-right">Cant.</th>
                   <th class="px-4 py-3 w-24">Unidad</th>
                   <th class="px-4 py-3 w-32 text-right">Precio</th>
                   <th class="px-4 py-3 w-32 text-right">Importe</th>
                   <th class="px-4 py-3 w-10"></th>
                 </tr>
               </thead>
               <tbody class="divide-y divide-slate-800 bg-slate-900/50">
                 
                 @for (row of movements; track $index) {
                   <tr class="group hover:bg-slate-800/50 transition-colors">
                     <td class="px-4 py-3 text-slate-500 font-mono">{{ $index + 1 }}</td>
                     <td class="px-4 py-3">
                        <select [ngModel]="row.productId" (ngModelChange)="updateProduct($index, $event)" class="w-full bg-transparent border border-transparent hover:border-slate-700 rounded text-white focus:bg-slate-950 focus:border-sky-500 outline-none">
                           <option value="" disabled>Seleccionar Producto...</option>
                           @for (item of service.items(); track item.productId) {
                             <option [value]="item.productId">{{ item.sku }} - {{ item.name }}</option>
                           }
                        </select>
                     </td>
                     <td class="px-4 py-3">
                        <input type="number" [(ngModel)]="row.quantity" (ngModelChange)="updateTotal($index)" class="w-full bg-transparent border border-transparent hover:border-slate-700 rounded text-right text-white font-mono focus:bg-slate-950 focus:border-sky-500 outline-none" min="0">
                     </td>
                     <td class="px-4 py-3 text-slate-500 text-xs">PZA</td>
                     <td class="px-4 py-3">
                        <input type="number" [(ngModel)]="row.unitPrice" (ngModelChange)="updateTotal($index)" class="w-full bg-transparent border border-transparent hover:border-slate-700 rounded text-right text-white font-mono focus:bg-slate-950 focus:border-sky-500 outline-none" min="0">
                     </td>
                     <td class="px-4 py-3 text-right font-mono text-white">
                        {{ (row.quantity * row.unitPrice) | currency }}
                     </td>
                     <td class="px-4 py-3 text-center">
                        <button (click)="removeRow($index)" class="text-slate-600 hover:text-red-500 transition-colors">
                          <i class="fa-solid fa-times"></i>
                        </button>
                     </td>
                   </tr>
                 }
                 
                 <!-- Add Row Button -->
                 <tr>
                   <td colspan="7" class="p-2">
                     <button (click)="addRow()" class="w-full py-2 border-2 border-dashed border-slate-800 rounded-lg text-slate-500 hover:text-sky-500 hover:border-sky-500 hover:bg-sky-500/5 transition-all flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-wide">
                       <i class="fa-solid fa-plus"></i> Agregar Partida
                     </button>
                   </td>
                 </tr>

               </tbody>
             </table>
           </div>

           <!-- Helper Footer -->
           <div class="p-4 bg-slate-950 border-t border-slate-800 text-xs text-slate-500 flex justify-between items-center">
             <div>
               <i class="fa-solid fa-circle-info mr-2"></i>
               Los precios se sugieren del catálogo maestro.
             </div>
             <div>
               {{ movements.length }} Partidas
             </div>
           </div>
        </div>

      </div>
    </div>
  `
})
export class InventoryDocumentEditorComponent implements OnInit {
  public service = inject(InventoryService);
  // Explicitly type FormBuilder to fix property 'group' does not exist on type 'unknown' error.
  fb: FormBuilder = inject(FormBuilder);
  router = inject(Router);

  // Form State
  form = this.fb.group({
    conceptId: ['', Validators.required],
    warehouseId: ['', Validators.required],
    partnershipId: [''],
    deliveryDate: [new Date().toISOString().slice(0, 10), Validators.required],
    reference: [''],
    description: ['']
  });

  // Lines State
  movements: { productId: string; quantity: number; unitPrice: number; }[] = [];

  // Computed State
  selectedConcept = computed(() => {
    const id = Number(this.form.controls.conceptId.value);
    return this.service.concepts().find(c => c.id === id) || null;
  });

  subtotal = computed(() => this.movements.reduce((sum, m) => sum + (m.quantity * m.unitPrice), 0));
  tax = computed(() => this.subtotal() * 0.16);
  total = computed(() => this.subtotal() + this.tax());

  ngOnInit() {
    this.service.loadCatalogs();
    this.service.loadItems();
    
    effect(() => {
        if (!this.form.controls.warehouseId.value && this.service.warehouses().length > 0) {
            this.form.controls.warehouseId.setValue(this.service.warehouses()[0].id as string);
        }
    });

    this.addRow();
  }

  addRow() {
    this.movements.push({ productId: '', quantity: 1, unitPrice: 0 });
  }

  removeRow(index: number) {
    this.movements.splice(index, 1);
  }

  updateProduct(index: number, productId: string) {
    const item = this.service.items().find(i => i.productId === productId);
    if (item) {
      this.movements[index].productId = productId;
      this.movements[index].unitPrice = item.price.amount;
    }
  }
  
  updateTotal(index: number) {
     this.movements = [...this.movements]; 
  }

  cancel() {
    this.router.navigate(['/inventory/documents']);
  }

  async submit() {
    if (this.form.invalid) return;
    
    const validMovements = this.movements.filter(m => m.productId && m.quantity > 0);
    
    const cmd: CreateDocumentCommand = {
      conceptId: Number(this.form.value.conceptId),
      warehouseId: this.form.value.warehouseId!,
      partnershipId: this.form.value.partnershipId ? Number(this.form.value.partnershipId) : undefined,
      deliveryDate: this.form.value.deliveryDate!,
      reference: this.form.value.reference || '',
      description: this.form.value.description || '',
      movements: validMovements
    };

    const success = await this.service.createDocument(cmd);
    if (success) {
      this.router.navigate(['/inventory/documents']);
    }
  }
}
