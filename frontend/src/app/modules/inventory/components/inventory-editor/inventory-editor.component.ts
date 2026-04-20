// temp_future/src/app/modules/inventory/components/inventory-editor/inventory-editor.component.ts
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormArray, ReactiveFormsModule, Validators } from '@angular/forms';
import { InventoryService } from '../../../../core/services/inventory.service';
import { DocumentHeaderComponent } from '../document-header/document-header.component';
import { ItemTableComponent } from '../item-table/item-table.component';
import { DocumentFooterComponent } from '../document-footer/document-footer.component';
import { calculateTotals } from '../../../../core/utils/inventory.utils';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-inventory-editor',
  standalone: true,
  imports: [
    CommonModule, 
    ReactiveFormsModule, 
    DocumentHeaderComponent, 
    ItemTableComponent, 
    DocumentFooterComponent
  ],
  template: `
    <div class="max-w-7xl mx-auto p-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      <!-- Top Actions Bar -->
      <div class="flex justify-between items-center bg-slate-900/40 p-6 rounded-2xl border border-white/5 backdrop-blur-md">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-cyan-500/20 rounded-xl flex items-center justify-center text-cyan-400 border border-cyan-500/30">
            <span class="material-icons">receipt_long</span>
          </div>
          <div>
            <h1 class="text-2xl font-black text-white tracking-tighter uppercase italic">Nuevo Movimiento</h1>
            <p class="text-[9px] text-slate-500 font-bold uppercase tracking-[0.3em]">Ledger v2.1 // Registro Industrial</p>
          </div>
        </div>

        <div class="flex gap-4">
          <button class="px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-white transition-all">
            DESCARTAR
          </button>
          <button (click)="onSubmit()"
                  [disabled]="editorForm.invalid || isSubmitting()"
                  class="px-8 py-3 bg-cyan-600 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] text-white shadow-lg shadow-cyan-500/20 hover:bg-cyan-500 transition-all active:scale-95 disabled:opacity-50">
            {{ isSubmitting() ? 'PROCESANDO...' : 'CONFIRMAR EN LEDGER' }}
          </button>
        </div>
      </div>

      <!-- Granular Components -->
      <app-document-header (headerChanged)="onHeaderChange($event)"></app-document-header>
      
      <app-item-table [parentForm]="editorForm" (addItem)="addMovement()"></app-item-table>

      <app-document-footer 
        [totalWeight]="totals().totalWeight" 
        [totalQuantity]="totals().totalItems"
        [movements]="editorForm.value.movements">
      </app-document-footer>

    </div>
  `
})
export class InventoryEditorComponent implements OnInit {
  private fb = inject(FormBuilder);
  private service = inject(InventoryService);
  private toast = inject(ToastService);

  editorForm: FormGroup;
  isSubmitting = signal(false);
  clientRequestId = crypto.randomUUID();

  constructor() {
    this.editorForm = this.fb.group({
      concept_type: [null, Validators.required],
      concept_id: ['', Validators.required],
      warehouse_id: ['', Validators.required],
      destination_warehouse_id: [null],
      notes: [''],
      movements: this.fb.array([])
    });
  }

  ngOnInit() {
    this.service.loadCatalogs();
    this.addMovement(); // Start with one row
  }

  get movements() {
    return this.editorForm.get('movements') as FormArray;
  }

  totals = computed(() => {
    return calculateTotals(this.editorForm.value.movements || []);
  });

  onHeaderChange(headerData: any) {
    this.editorForm.patchValue(headerData);
  }

  addMovement() {
    const row = this.fb.group({
      product_id: ['', Validators.required],
      sku: ['', Validators.required],
      name: [''],
      quantity: [0, [Validators.required, Validators.min(0.0001)]],
      uom_factor: [1],
      weight: [0, [Validators.required, Validators.min(0.0001)]],
      location_code: [''],
      is_weight_mismatch: [false]
    });
    this.movements.push(row);
  }

  async onSubmit() {
    if (this.editorForm.valid) {
      this.isSubmitting.set(true);
      try {
        await this.service.createDocument(this.editorForm.value, this.clientRequestId);
        
        this.toast.success('DOCUMENTO CONFIRMADO EN LEDGER', 'ÉXITO INDUSTRIAL');
        
        // Regenerate for next document if staying on page
        this.clientRequestId = crypto.randomUUID();
        this.editorForm.reset();
        this.movements.clear();
        this.addMovement();
      } catch (e) {
        // Error handling is managed by global errorInterceptor
      } finally {
        this.isSubmitting.set(false);
      }
    }
  }
}
