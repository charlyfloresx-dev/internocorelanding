
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { InventoryService } from '@services/inventory.service';
import { InventoryItemDto } from '@models/api.types';

type ModalMode = 'create' | 'adjust' | null;

@Component({
  selector: 'app-inventory-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
           <h1 class="text-2xl font-bold text-white tracking-tight">Inventario Maestro</h1>
           <p class="text-slate-400 text-sm">Gestión de SKUs y Existencias por Almacén</p>
        </div>
        <button (click)="openCreateModal()" class="bg-sky-600 hover:bg-sky-500 text-white font-bold py-2 px-4 rounded-lg shadow-lg shadow-sky-900/20 transition-all flex items-center gap-2">
           <i class="fa-solid fa-plus"></i> Nuevo Artículo
        </button>
      </div>

      <!-- Stats Cards (Simple) -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-slate-800 p-4 rounded-xl border border-slate-700">
          <div class="text-slate-400 text-xs font-bold uppercase">Total SKUs</div>
          <div class="text-2xl font-bold text-white mt-1">{{ service.items().length }}</div>
        </div>
        <div class="bg-slate-800 p-4 rounded-xl border border-slate-700">
          <div class="text-slate-400 text-xs font-bold uppercase">Valor Total</div>
          <div class="text-2xl font-bold text-emerald-400 mt-1">{{ totalValue() | currency }}</div>
        </div>
        <div class="bg-slate-800 p-4 rounded-xl border border-slate-700">
          <div class="text-slate-400 text-xs font-bold uppercase">Items Bajos en Stock</div>
          <div class="text-2xl font-bold text-yellow-500 mt-1">{{ lowStockCount() }}</div>
        </div>
      </div>

      <!-- Data Table -->
      <div class="bg-slate-800 rounded-xl border border-slate-700 shadow-xl overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-slate-300">
            <thead class="bg-slate-900/50 text-slate-400 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-700">
              <tr>
                <th class="px-6 py-4">SKU / Nombre</th>
                <th class="px-6 py-4">Ubicación</th>
                <th class="px-6 py-4">Categoría</th>
                <th class="px-6 py-4">Precio</th>
                <th class="px-6 py-4">Existencia</th>
                <th class="px-6 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700">
              @if (service.loading()) {
                <tr><td colspan="6" class="px-6 py-8 text-center text-slate-500"><i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Cargando inventario...</td></tr>
              } @else if (service.items().length === 0) {
                 <tr><td colspan="6" class="px-6 py-8 text-center text-slate-500">No hay artículos registrados.</td></tr>
              }
              
              @for (item of service.items(); track item.id) {
                <tr class="hover:bg-slate-700/50 transition-colors group">
                  <td class="px-6 py-4">
                    <div class="flex flex-col">
                      <span class="font-bold text-white text-base">{{ item.name }}</span>
                      <span class="text-xs text-sky-500 font-mono">{{ item.sku }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                     <div class="flex flex-col">
                       <span class="text-white text-xs">{{ item.warehouseName }}</span>
                       @if (item.location) {
                         <span class="text-[10px] text-slate-500"><i class="fa-solid fa-map-pin mr-1"></i>{{ item.location }}</span>
                       }
                     </div>
                  </td>
                  <td class="px-6 py-4">
                    <span class="px-2 py-1 rounded bg-slate-700 text-xs">{{ item.categoryName }}</span>
                  </td>
                  <td class="px-6 py-4 font-mono text-white">
                    {{ item.price.amount | currency: item.price.currency }}
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                       <span [class]="getStockColor(item.stockQuantity)">{{ item.stockQuantity }}</span>
                       @if (item.stockQuantity < 20) {
                         <i class="fa-solid fa-triangle-exclamation text-yellow-500 text-xs" title="Stock Bajo"></i>
                       }
                       @if (item.reservedQuantity > 0) {
                         <span class="text-[10px] text-slate-500 bg-slate-800 px-1 rounded border border-slate-700" title="Reservado">
                           Res: {{ item.reservedQuantity }}
                         </span>
                       }
                    </div>
                  </td>
                  <td class="px-6 py-4 text-right">
                    <button (click)="openAdjustModal(item)" class="text-slate-400 hover:text-white px-3 py-1 rounded border border-slate-600 hover:bg-slate-600 transition-colors text-xs font-bold mr-2">
                      <i class="fa-solid fa-scale-balanced mr-1"></i> Ajustar
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

    </div>

    <!-- MODAL: CREATE ITEM -->
    @if (modalMode() === 'create') {
      <div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
        <div class="bg-slate-800 rounded-2xl shadow-2xl border border-slate-700 w-full max-w-lg overflow-hidden animate-fade-in-up">
           <div class="p-6 border-b border-slate-700 bg-slate-900/50 flex justify-between items-center">
             <h3 class="text-xl font-bold text-white">Nuevo Artículo</h3>
             <button (click)="closeModal()" class="text-slate-500 hover:text-white"><i class="fa-solid fa-times"></i></button>
           </div>
           
           <form [formGroup]="createForm" (ngSubmit)="submitCreate()" class="p-6 space-y-4">
             <div class="grid grid-cols-2 gap-4">
               <div class="col-span-2">
                 <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Nombre</label>
                 <input formControlName="name" class="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white focus:border-sky-500 outline-none">
               </div>
               <div>
                 <label class="block text-xs font-bold text-slate-500 uppercase mb-1">SKU</label>
                 <input formControlName="sku" class="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white focus:border-sky-500 outline-none">
               </div>
               <div>
                 <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Categoría</label>
                 <select formControlName="categoryId" class="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white focus:border-sky-500 outline-none">
                   @for (cat of service.categories(); track cat.id) {
                     <option [value]="cat.id">{{ cat.name }}</option>
                   }
                 </select>
               </div>
               
               <!-- Warehouse Selection (Dynamic) -->
               <div class="col-span-2">
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Almacén Destino</label>
                  <select formControlName="warehouseId" class="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white focus:border-sky-500 outline-none">
                    @for (wh of service.warehouses(); track wh.id) {
                      <option [value]="wh.id">{{ wh.name }}</option>
                    }
                 </select>
               </div>

               <div>
                 <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Precio Unitario</label>
                 <input type="number" formControlName="price" class="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white focus:border-sky-500 outline-none">
               </div>
               <div>
                 <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Stock Inicial</label>
                 <input type="number" formControlName="initialStockQuantity" class="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white focus:border-sky-500 outline-none">
               </div>
               <div class="col-span-2">
                 <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Descripción</label>
                 <textarea formControlName="description" rows="2" class="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white focus:border-sky-500 outline-none"></textarea>
               </div>
             </div>
             
             <div class="pt-4 flex justify-end gap-3">
               <button type="button" (click)="closeModal()" class="px-4 py-2 rounded bg-slate-700 text-white hover:bg-slate-600">Cancelar</button>
               <button type="submit" [disabled]="createForm.invalid" class="px-6 py-2 rounded bg-sky-600 text-white font-bold hover:bg-sky-500 disabled:opacity-50">Crear</button>
             </div>
           </form>
        </div>
      </div>
    }

    <!-- MODAL: ADJUST STOCK -->
    @if (modalMode() === 'adjust') {
       <div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
        <div class="bg-slate-800 rounded-2xl shadow-2xl border border-slate-700 w-full max-w-md overflow-hidden animate-fade-in-up">
           <div class="p-6 border-b border-slate-700 bg-slate-900/50">
             <h3 class="text-xl font-bold text-white">Ajuste de Inventario</h3>
             <p class="text-slate-400 text-sm mt-1">{{ selectedItem?.sku }} - {{ selectedItem?.name }}</p>
           </div>
           
           <div class="p-6 space-y-4">
             <div class="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700">
               <span class="text-slate-400 text-sm">Stock Actual</span>
               <div class="text-right">
                  <div class="text-2xl font-bold text-white">{{ selectedItem?.stockQuantity }}</div>
                  <div class="text-xs text-slate-500">{{ selectedItem?.warehouseName }}</div>
               </div>
             </div>

             <div>
               <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Cantidad a Ajustar (+/-)</label>
               <input type="number" [(ngModel)]="adjustQty" class="w-full bg-slate-900 border border-slate-700 rounded p-3 text-white text-lg font-mono focus:border-sky-500 outline-none" placeholder="Ej. 10 o -5">
               <p class="text-xs text-slate-500 mt-1">Use valores negativos para salidas.</p>
             </div>

             <div>
               <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Motivo</label>
               <input type="text" [(ngModel)]="adjustReason" class="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white focus:border-sky-500 outline-none" placeholder="Ej. Recepción de proveedor, Merma...">
             </div>

             <div class="pt-4 flex justify-end gap-3">
               <button (click)="closeModal()" class="px-4 py-2 rounded bg-slate-700 text-white hover:bg-slate-600">Cancelar</button>
               <button (click)="submitAdjust()" [disabled]="!adjustQty || !adjustReason" class="px-6 py-2 rounded bg-sky-600 text-white font-bold hover:bg-sky-500 disabled:opacity-50">Confirmar</button>
             </div>
           </div>
        </div>
      </div>
    }
  `
})
export class InventoryDashboardComponent implements OnInit {
  public service = inject(InventoryService);
  fb: FormBuilder = inject(FormBuilder);
  
  modalMode = signal<ModalMode>(null);
  selectedItem: InventoryItemDto | null = null;
  
  // Forms & Inputs
  createForm = this.fb.group({
    name: ['', Validators.required],
    sku: ['', Validators.required],
    description: [''],
    price: [0, [Validators.required, Validators.min(0)]],
    initialStockQuantity: [0, [Validators.required, Validators.min(0)]],
    categoryId: ['1'], // Default cat ID
    warehouseId: ['wh-01', Validators.required]
  });

  adjustQty: number | null = null;
  adjustReason: string = '';

  // Stats - Computed signals
  totalValue = computed(() => 
    this.service.items().reduce((acc, item) => acc + (item.price.amount * item.stockQuantity), 0)
  );

  lowStockCount = computed(() => 
    this.service.items().filter(item => item.stockQuantity < 20).length
  );

  ngOnInit() {
    this.service.loadItems();
    this.service.loadCatalogs(); // Load Categories & Warehouses
  }

  // Helpers
  getStockColor(qty: number) {
    if (qty <= 10) return 'text-red-500 font-bold';
    if (qty <= 20) return 'text-yellow-500 font-bold';
    return 'text-green-500 font-bold';
  }

  openCreateModal() {
    // Reset form with valid defaults if available
    const defaultCat = this.service.categories()[0]?.id?.toString() || '1';
    const defaultWh = this.service.warehouses()[0]?.id || 'wh-01';
    
    this.createForm.reset({ 
      categoryId: defaultCat, 
      warehouseId: defaultWh, 
      price: 0, 
      initialStockQuantity: 0 
    });
    this.modalMode.set('create');
  }

  openAdjustModal(item: InventoryItemDto) {
    this.selectedItem = item;
    this.adjustQty = null;
    this.adjustReason = '';
    this.modalMode.set('adjust');
  }

  closeModal() {
    this.modalMode.set(null);
    this.selectedItem = null;
  }

  async submitCreate() {
    if (this.createForm.invalid) return;
    const success = await this.service.createItem(this.createForm.value as any);
    if (success) this.closeModal();
  }

  async submitAdjust() {
    if (!this.selectedItem || !this.adjustQty) return;
    const success = await this.service.adjustStock({
      itemId: this.selectedItem.id,
      quantityChange: this.adjustQty,
      reason: this.adjustReason
    });
    if (success) this.closeModal();
  }
}
