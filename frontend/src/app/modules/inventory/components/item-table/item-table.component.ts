// temp_future/src/app/modules/inventory/components/item-table/item-table.component.ts
import { Component, Input, Output, EventEmitter, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormArray, FormGroup } from '@angular/forms';
import { ExcelNavigationDirective } from '../../../../shared/directives/excel-navigation.directive';
import { validateMovementMass } from '../../../../core/utils/inventory.utils';
import { InventoryService } from '../../../../core/services/inventory.service';
import { ProductRead } from '../../../../core/models/domain.types';
import { Subject, debounceTime, distinctUntilChanged, switchMap, of } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-item-table',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ExcelNavigationDirective],
  template: `
    <div class="industrial-card mt-6 bg-slate-900/40 rounded-2xl border border-white/5 shadow-2xl">
      <div class="p-6 border-b border-white/5 flex items-center justify-between">
        <h3 class="text-[10px] font-black text-cyan-500 uppercase tracking-[0.3em]">Partidas de Inventario</h3>
        <button (click)="addItem.emit()" 
                class="text-[9px] font-black text-white px-3 py-1.5 bg-cyan-600/20 border border-cyan-500/50 rounded-lg hover:bg-cyan-500/30 transition-all">
          + AGREGAR SKU
        </button>
      </div>

      <div class="overflow-x-auto custom-scrollbar" [icExcelNav]="movements.controls" (smartPaste)="onPaste($any($event))" (lastCellTab)="addItem.emit()">
        <table class="w-full text-left" [formGroup]="parentForm">
          <thead>
            <tr class="bg-black/20">
              <th class="px-6 py-4 text-[9px] font-bold text-slate-500 uppercase tracking-widest w-[300px]">Material / Partida</th>
              <th class="px-6 py-4 text-[9px] font-bold text-slate-500 uppercase tracking-widest">Localidad</th>
              <th class="px-6 py-4 text-[9px] font-bold text-slate-500 uppercase tracking-widest text-right">Cantidad</th>
              <th class="px-6 py-4 text-[9px] font-bold text-slate-500 uppercase tracking-widest text-right">Peso Masa (Kg)</th>
              <th class="px-6 py-4 text-[9px] font-bold text-slate-500 uppercase tracking-widest text-center">Estado</th>
            </tr>
          </thead>
          <tbody formArrayName="movements" class="divide-y divide-white/5">
            <tr *ngFor="let m of movements.controls; let i = index" [formGroupName]="i" 
                class="hover:bg-white/5 transition-colors group relative">
              
              <!-- SKU / Description -->
              <td class="px-6 py-4 relative">
                <input formControlName="sku" [attr.data-row]="i" [attr.data-col]="0"
                       (input)="onSkuInput($event, i)"
                       (focus)="activeRow.set(i)"
                       (blur)="onSkuBlur()"
                       class="w-full bg-transparent border-none text-[11px] font-mono text-cyan-400 focus:outline-none placeholder:text-slate-700 search-input"
                       placeholder="BUSCAR SKU..." autocomplete="off">
                
                <div *ngIf="m.get('name')?.value" class="mt-1 text-[9px] text-slate-500 font-bold uppercase truncate">
                  {{ m.get('name')?.value }}
                </div>

                <!-- Search Results Dropdown -->
                <div *ngIf="activeRow() === i && searchResults().length > 0" 
                     class="absolute left-6 right-6 top-full z-50 bg-slate-900 border border-cyan-500/30 rounded-xl shadow-2xl mt-1 overflow-hidden">
                  <div *ngFor="let result of searchResults()" 
                       (mousedown)="selectProduct(result, i)"
                       class="p-3 hover:bg-cyan-500/10 cursor-pointer border-b border-white/5 last:border-none flex justify-between items-center transition-colors">
                    <div class="flex flex-col">
                      <span class="text-[10px] font-mono text-cyan-400">{{ result.sku }}</span>
                      <span class="text-[9px] text-slate-400 uppercase font-bold">{{ result.name }}</span>
                    </div>
                    <span class="text-[8px] bg-slate-800 px-2 py-0.5 rounded-full text-slate-500 font-mono">STOCK: INF</span>
                  </div>
                </div>
              </td>

              <!-- Location -->
              <td class="px-6 py-4">
                <input formControlName="location_code" [attr.data-row]="i" [attr.data-col]="1"
                       class="w-24 bg-transparent border-none text-[10px] font-bold text-slate-300 text-center focus:outline-none">
              </td>

              <!-- Quantity -->
              <td class="px-6 py-4 text-right">
                <input type="number" formControlName="quantity" [attr.data-row]="i" [attr.data-col]="2"
                       (input)="onValueChange(i)"
                       class="w-20 bg-transparent border-none text-[11px] font-black text-white text-right focus:outline-none">
              </td>

              <!-- Weight (Forensic Validation) -->
              <td class="px-6 py-4 text-right relative group/weight">
                <input type="number" formControlName="weight" [attr.data-row]="i" [attr.data-col]="3"
                       (input)="onValueChange(i)"
                       [class.text-red-500]="isInvalid(i)"
                       class="w-24 bg-transparent border-none text-[11px] font-black text-white text-right focus:outline-none transition-all">
                
                <!-- Forensic Tooltip -->
                <div class="forensic-tooltip">
                   <div class="flex items-center gap-2 mb-2 border-b border-cyan-500/20 pb-2">
                     <span class="text-[9px] font-black text-cyan-400">ANÁLISIS DE MASA</span>
                   </div>
                   <div class="space-y-1 text-[8px] font-bold">
                     <div class="flex justify-between">
                       <span class="text-slate-500">ESPERADO:</span>
                       <span class="text-white">{{ expectedWeight(i) | number:'1.4-4' }} Kg</span>
                     </div>
                     <div class="flex justify-between">
                       <span class="text-slate-500">TOLERANCIA:</span>
                       <span class="text-cyan-600">± 0.0001</span>
                     </div>
                   </div>
                </div>
              </td>

              <!-- Status Icon -->
              <td class="px-6 py-4 text-center">
                <button (click)="removeRow(i)" class="opacity-0 group-hover:opacity-100 p-2 text-slate-600 hover:text-red-500 transition-all">
                  <span class="material-icons text-xs">delete</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
  `,
})
export class ItemTableComponent {
  private service = inject(InventoryService);
  
  @Input() parentForm!: FormGroup;
  @Output() addItem = new EventEmitter<void>();

  searchResults = signal<ProductRead[]>([]);
  activeRow = signal<number | null>(null);
  private searchSubject = new Subject<{ query: string, index: number }>();

  constructor() {
    this.searchSubject.pipe(
      takeUntilDestroyed(),
      debounceTime(300),
      distinctUntilChanged((prev, curr) => prev.query === curr.query),
      switchMap(({ query, index }) => {
        if (!query || query.length < 2) return of([]);
        const warehouseId = this.parentForm.get('warehouse_id')?.value;
        if (!warehouseId) return of([]);
        return this.service.searchProducts(query, warehouseId);
      })
    ).subscribe(results => {
      this.searchResults.set(results);
    });
  }

  get movements() {
    return this.parentForm.get('movements') as FormArray;
  }

  onValueChange(index: number) {
    const row = this.movements.at(index);
    const qty = row.get('quantity')?.value || 0;
    const factor = row.get('uom_factor')?.value || 1;
    const weight = row.get('weight')?.value || 0;
    
    const isValid = validateMovementMass(qty, factor, weight);
    row.get('is_weight_mismatch')?.setValue(!isValid);
  }

  isInvalid(index: number): boolean {
    return this.movements.at(index).get('is_weight_mismatch')?.value === true;
  }

  expectedWeight(index: number): number {
    const row = this.movements.at(index);
    return (row.get('quantity')?.value || 0) * (row.get('uom_factor')?.value || 1);
  }

  onPaste(data: string[][]) {
    data.forEach(row => {
      // Logic to map pasted SKU/Qty to form rows
      console.log('Smart Paste Row:', row);
    });
  }

  onSkuInput(event: any, index: number) {
    const query = event.target.value;
    this.activeRow.set(index);
    this.searchSubject.next({ query, index });
  }

  onSkuBlur() {
    // Small delay to allow mousedown on results
    setTimeout(() => this.activeRow.set(null), 200);
  }

  selectProduct(product: ProductRead, index: number) {
    const row = this.movements.at(index);
    row.patchValue({
      product_id: product.id,
      sku: product.sku,
      name: product.name,
      uom_factor: product.version_id || 1 // Fallback factor
    });
    this.searchResults.set([]);
    this.activeRow.set(null);
    this.onValueChange(index);
  }

  removeRow(index: number) {
    this.movements.removeAt(index);
  }
}
