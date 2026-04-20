import { Component, inject, signal, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, Product, ProductType } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { lastValueFrom } from 'rxjs';

@Component({
  selector: 'app-product-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, MatIconModule, TranslatePipe],
  template: `
    <div class="fixed inset-0 z-[150] flex items-center justify-center bg-slate-900/40 dark:bg-slate-950/80 backdrop-blur-sm p-4">
      <div class="ic-modal-container industrial-card w-full max-w-4xl h-auto max-h-[90vh] flex flex-col overflow-hidden shadow-2xl border-primary/30 rounded-3xl bg-surface-bg animate-scale-in">
        
        <!-- Header copied from Price Modal style -->
        <div class="p-8 border-b border-surface-border">
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-6">
              <div class="w-12 h-12 bg-primary/20 rounded-xl flex items-center justify-center text-primary border border-primary/30">
                <mat-icon class="text-2xl">{{ isEdit() ? 'inventory' : 'add_box' }}</mat-icon>
              </div>
              <div>
                <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">
                  {{ (isEdit() ? 'catalog.edit_product' : 'catalog.new_product') | translate:(isEdit() ? 'Editar Producto' : 'Nuevo Producto') }}
                </h2>
                <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1 font-mono">
                  {{ isEdit() ? product()?.sku : 'Registro de nuevo ítem en el Catálogo Maestro' }}
                </p>
              </div>
            </div>
            <button (click)="close.emit()" class="p-2 bg-surface-bg border border-surface-border rounded-lg text-surface-text-muted hover:text-white hover:border-red-500 transition-colors">
              <mat-icon class="text-sm">close</mat-icon>
            </button>
          </div>
        </div>

        <!-- Form Body -->
        <form [formGroup]="form" (ngSubmit)="save()" class="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
            <!-- Basic Info -->
            <div class="space-y-6">
              <div class="space-y-2">
                <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block">Identificación Base</label>
                <div class="grid grid-cols-3 gap-4">
                  <div class="col-span-1">
                    <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">SKU *</label>
                    <input formControlName="sku" type="text" class="cell-input font-mono text-primary uppercase" placeholder="MAT-000">
                  </div>
                  <div class="col-span-2">
                    <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Nombre del Producto *</label>
                    <input formControlName="name" type="text" class="cell-input" placeholder="Ej. Aluminio Industrial 6061">
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-6">
                <div class="space-y-1.5">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Tipo de Recurso</label>
                  <select formControlName="product_type" class="cell-input cursor-pointer">
                    <option value="GOODS">Bien / Físico</option>
                    <option value="SERVICE">Servicio</option>
                  </select>
                </div>
                <div class="space-y-1.5">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Unidad de Medida (UOM) *</label>
                  <select formControlName="uom_id" class="cell-input cursor-pointer">
                    @for (u of masterData.uoms(); track u.id) {
                      <option [value]="u.id">{{ u.abbreviation }} - {{ u.name }}</option>
                    }
                  </select>
                </div>
              </div>
              
              <div class="space-y-1.5">
                <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Descripción / Especificaciones</label>
                <textarea formControlName="description" rows="3" class="cell-input resize-none" placeholder="Detalles técnicos del producto..."></textarea>
              </div>
            </div>

            <!-- Metadata / Fiscal / Logistics -->
            <div class="space-y-6">
              <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block">Clasificación y Cumplimiento</label>
              
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Categoría</label>
                  <select formControlName="category_id" class="cell-input cursor-pointer">
                    <option [value]="null">Sin categoría</option>
                    @for (c of masterData.categories(); track c.id) {
                      <option [value]="c.id">{{ c.name }}</option>
                    }
                  </select>
                </div>
                <div>
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Marca</label>
                  <select formControlName="brand_id" class="cell-input cursor-pointer">
                    <option [value]="null">Sin marca</option>
                    @for (b of masterData.brands(); track b.id) {
                      <option [value]="b.id">{{ b.name }}</option>
                    }
                  </select>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-6 p-4 bg-surface-bg/50 rounded-2xl border border-surface-border">
                <div class="space-y-1.5">
                  <label class="text-[9px] font-black text-cyan-500 uppercase tracking-widest mb-1 block">Código SAT</label>
                  <input formControlName="sat_product_code" type="text" class="cell-input font-mono text-cyan-500" placeholder="8 dígitos" maxlength="20">
                </div>
                <div class="space-y-1.5">
                  <label class="text-[9px] font-black text-purple-400 uppercase tracking-widest mb-1 block">Fracción HTS</label>
                  <input formControlName="hts_code" type="text" class="cell-input font-mono text-purple-400" placeholder="Código aduanal" maxlength="20">
                </div>
              </div>

              <!-- Toggles Optimized -->
              <div class="grid grid-cols-1 gap-3">
                <div class="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl transition-colors border border-transparent hover:border-white/5">
                   <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Objeto de Impuesto (IVA)</span>
                   <label class="relative inline-flex items-center cursor-pointer">
                     <input type="checkbox" formControlName="is_taxable" class="sr-only peer">
                     <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                   </label>
                </div>
                <div class="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl transition-colors border border-transparent hover:border-white/5">
                   <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Trazabilidad por Lotes</span>
                   <label class="relative inline-flex items-center cursor-pointer">
                     <input type="checkbox" formControlName="requires_batch" class="sr-only peer">
                     <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                   </label>
                </div>
                <div class="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl transition-colors border border-transparent hover:border-white/5">
                   <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Requiere Fecha Caducidad</span>
                   <label class="relative inline-flex items-center cursor-pointer">
                     <input type="checkbox" formControlName="requires_expiration" class="sr-only peer">
                     <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                   </label>
                </div>
              </div>
            </div>
          </div>
        </form>

        <!-- Footer Footer style -->
        <div class="p-8 border-t border-surface-border bg-surface-bg/30">
          <div class="flex items-center justify-between">
            <p class="text-[9px] text-surface-text-muted font-mono tracking-widest uppercase">
              <span class="font-black text-primary">TIP:</span> RECUERDA ASIGNAR PRECIO DESPUÉS DE GUARDAR
            </p>
            <div class="flex items-center gap-4">
              <button type="button" (click)="close.emit()" class="px-8 py-3 rounded-xl border border-surface-border text-[10px] font-black uppercase tracking-[0.2em] text-surface-text-muted hover:text-white transition-all">
                Cancelar
              </button>
              <button (click)="save()" [disabled]="form.invalid || loading()" 
                      class="px-10 py-3 bg-primary text-slate-950 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] hover:bg-primary-dark transition-all disabled:opacity-30 shadow-lg shadow-primary/20 italic">
                {{ (loading() ? 'common.saving' : (isEdit() ? 'Actualizar Producto' : 'Crear Producto')) | translate }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .cell-input {
      width: 100%;
      background-color: var(--color-input-bg);
      border: 1px solid var(--color-input-border);
      border-radius: 8px;
      padding: 10px 14px;
      color: var(--color-input-text);
      font-size: 11px;
      font-weight: 500;
      outline: none;
      transition: all 0.2s;
    }
    .cell-input:focus {
      border-color: rgba(0, 242, 255, 0.5);
      background: rgba(15, 23, 42, 0.8);
      box-shadow: 0 0 15px rgba(0, 242, 255, 0.1);
    }
    select.cell-input { appearance: none; }
    option { background: #0f172a; color: white; }
  `]
})
export class ProductModalComponent {
  masterData = inject(MasterDataService);
  private fb = inject(FormBuilder);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);

  product = signal<Product | null>(null);
  isEdit = signal(false);
  loading = signal(false);
  close = output<void>();
  saved = output<Product>();

  form = this.fb.group({
    sku: ['', [Validators.required, Validators.minLength(2)]],
    name: ['', [Validators.required]],
    product_type: ['GOODS' as ProductType],
    uom_id: ['', [Validators.required]],
    category_id: [null as string | null],
    brand_id: [null as string | null],
    description: [''],
    sat_product_code: [''],
    hts_code: [''],
    is_taxable: [true],
    allow_price_override: [true],
    requires_batch: [false],
    requires_expiration: [false]
  });

  open(product?: Product) {
    if (product) {
      this.product.set(product);
      this.isEdit.set(true);
      this.form.patchValue({
        sku: product.sku,
        name: product.name,
        product_type: product.product_type,
        uom_id: product.base_uom_id || (product as any).uom_id,
        category_id: product.category_id,
        brand_id: product.brand_id,
        description: product.description,
        sat_product_code: product.sat_product_code,
        hts_code: product.hts_code,
        is_taxable: product.is_taxable,
        allow_price_override: product.allow_price_override,
        requires_batch: product.requires_batch,
        requires_expiration: product.requires_expiration
      });
      
      // If global, disable all
      if (this.masterData.isGlobal(product)) {
        this.form.disable();
      } else {
        const roles = this.auth.roles();
        const isAdmin = roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin');
        if (!isAdmin) this.form.disable();
      }
    } else {
      this.product.set(null);
      this.isEdit.set(false);
      this.form.reset({
        product_type: 'GOODS',
        is_taxable: true,
        allow_price_override: true,
        requires_batch: false,
        requires_expiration: false
      });
      this.form.enable();
    }
  }

  async save() {
    if (this.form.invalid) return;

    this.loading.set(true);
    const data = this.form.getRawValue();

    try {
      if (this.isEdit()) {
        const res = await lastValueFrom(this.masterData.updateProduct(this.product()!.id, data as any));
        this.notifications.success('Actualizado', 'Producto guardado con éxito');
        this.saved.emit(res.data);
      } else {
        const res = await lastValueFrom(this.masterData.createProduct(data as any));
        this.notifications.success('Creado', 'Producto registrado con éxito');
        this.saved.emit(res.data);
      }
      this.close.emit();
    } catch (err: any) {
      this.notifications.error('Error', err?.error?.detail || 'No se pudo guardar el producto');
    } finally {
      this.loading.set(false);
    }
  }
}
