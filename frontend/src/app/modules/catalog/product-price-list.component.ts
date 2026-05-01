import { Component, inject, signal, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MasterDataService, Product, ProductPrice, PartnerType, ProductType } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';
import { InventoryService } from '../../core/services/inventory.service';
import { PartnerModalComponent } from '../../shared/components/partner-modal.component';
import { SideDrawerService } from '../../core/services/side-drawer.service';

@Component({
  selector: 'app-product-price-list',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, MatIconModule, PartnerModalComponent],
  template: `
      <div class="flex flex-col h-full bg-surface-bg animate-fade-in">
        <!-- Header Section (Inside Drawer) -->
        <div class="mb-8 p-1">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/20">
              <mat-icon class="text-2xl">inventory_2</mat-icon>
            </div>
            <div>
              <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic">
                {{ isEdit ? 'Configuración Maestra' : 'Nuevo Producto' }}
              </h2>
              <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-0.5">
                {{ product?.sku || 'PENDIENTE' }} • {{ product?.name || 'REGISTRO INICIAL' }}
              </p>
            </div>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
          <!-- INDUSTRIAL TABS -->
          <div class="flex items-center gap-6 mb-8 border-b border-surface-border sticky top-0 bg-surface-bg z-20 pb-0">
            <button (click)="activeTab.set('INFO')" 
                    class="pb-4 text-[10px] font-black uppercase tracking-widest transition-all relative group"
                    [class]="activeTab() === 'INFO' ? 'text-primary' : 'text-surface-text-muted hover:text-surface-text'">
              <div class="flex items-center gap-2">
                <mat-icon class="text-xs">inventory_2</mat-icon>
                <span>Datos Maestros</span>
              </div>
              @if (activeTab() === 'INFO') { <div class="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-t-full shadow-[0_-4px_10px_rgba(0,229,255,0.4)]"></div> }
            </button>
            
            @if (isEdit) {
              <button (click)="activeTab.set('GLOBAL')" 
                      class="pb-4 text-[10px] font-black uppercase tracking-widest transition-all relative"
                      [class]="activeTab() === 'GLOBAL' ? 'text-emerald-400' : 'text-surface-text-muted hover:text-surface-text'">
                <div class="flex items-center gap-2">
                  <mat-icon class="text-xs">payments</mat-icon>
                  <span>Listas de Precio</span>
                </div>
                @if (activeTab() === 'GLOBAL') { <div class="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-400 rounded-t-full"></div> }
              </button>
              <button (click)="activeTab.set('B2B')" 
                      class="pb-4 text-[10px] font-black uppercase tracking-widest transition-all relative"
                      [class]="activeTab() === 'B2B' ? 'text-cyan-400' : 'text-surface-text-muted hover:text-surface-text'">
                <div class="flex items-center gap-2">
                  <mat-icon class="text-xs">handshake</mat-icon>
                  <span>Acuerdos B2B</span>
                </div>
                 @if (activeTab() === 'B2B') { <div class="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan-400 rounded-t-full"></div> }
              </button>
              <button (click)="activeTab.set('LOGISTICA')" 
                      class="pb-4 text-[10px] font-black uppercase tracking-widest transition-all relative"
                      [class]="activeTab() === 'LOGISTICA' ? 'text-amber-400' : 'text-surface-text-muted hover:text-surface-text'">
                <div class="flex items-center gap-2">
                  <mat-icon class="text-xs">local_shipping</mat-icon>
                  <span>Logística</span>
                </div>
                @if (activeTab() === 'LOGISTICA') { <div class="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-t-full"></div> }
              </button>
            }
          </div>

          <!-- GENERAL INFO TAB -->
          @if (activeTab() === 'INFO') {
            <form [formGroup]="infoForm" class="space-y-8 animate-fade-in">
              <div class="space-y-6">
                <div class="space-y-2">
                  <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block">Identificación Industrial</label>
                  <div class="grid grid-cols-3 gap-4">
                    <div class="col-span-1">
                      <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">SKU *</label>
                      <input formControlName="sku" type="text" class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase">
                    </div>
                    <div class="col-span-2">
                      <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Nombre Comercial *</label>
                      <input formControlName="name" type="text" class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all">
                    </div>
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Tipo</label>
                    <select formControlName="product_type" class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all cursor-pointer">
                      <option value="GOODS">Bien / Físico</option>
                      <option value="SERVICE">Servicio</option>
                    </select>
                  </div>
                  <div>
                    <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Unidad (UOM) *</label>
                    <select formControlName="uom_id" class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all cursor-pointer">
                      @for (u of masterData.uoms(); track u.id) {
                        <option [value]="u.id">{{ u.abbreviation }} - {{ u.name }}</option>
                      }
                    </select>
                  </div>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Categoría</label>
                    <select formControlName="category_id" class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all cursor-pointer">
                      <option [ngValue]="null">Sin categoría</option>
                      @for (cat of masterData.categories(); track cat.id) {
                        <option [value]="cat.id">{{ cat.name }}</option>
                      }
                    </select>
                  </div>
                  <div>
                    <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Marca</label>
                    <select formControlName="brand_id" class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all cursor-pointer">
                      <option [ngValue]="null">Sin marca</option>
                      @for (br of masterData.brands(); track br.id) {
                        <option [value]="br.id">{{ br.name }}</option>
                      }
                    </select>
                  </div>
                </div>

                <div>
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Descripción Técnica</label>
                  <textarea formControlName="description" rows="3" class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all resize-none"></textarea>
                </div>

                <div class="p-6 bg-emerald-500/5 rounded-2xl border border-emerald-500/20 space-y-6">
                  <label class="text-[10px] font-black text-emerald-500 uppercase tracking-[0.2em] block">Compliance Fiscal</label>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="text-[9px] font-black text-emerald-500/60 uppercase tracking-widest mb-1 block">Código SAT</label>
                      <input formControlName="sat_product_code" type="text" class="w-full bg-surface-bg/50 border border-emerald-500/30 rounded-xl p-3 text-[11px] font-mono font-bold text-emerald-500 outline-none focus:border-emerald-500 transition-all" placeholder="8 dígitos">
                    </div>
                    <div>
                      <label class="text-[9px] font-black text-purple-400 uppercase tracking-widest mb-1 block">Fracción HTS</label>
                      <input formControlName="hts_code" type="text" class="w-full bg-surface-bg/50 border border-purple-400/30 rounded-xl p-3 text-[11px] font-mono font-bold text-purple-400 outline-none focus:border-purple-400 transition-all">
                    </div>
                  </div>
                </div>

                <div class="grid grid-cols-1 gap-3">
                  <div class="flex items-center justify-between p-4 bg-surface-card border border-surface-border rounded-2xl hover:border-primary/30 transition-all">
                     <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest">Objeto de Impuesto (IVA)</span>
                     <label class="relative inline-flex items-center cursor-pointer">
                       <input type="checkbox" formControlName="is_taxable" class="sr-only peer">
                       <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                     </label>
                  </div>
                  <div class="flex items-center justify-between p-4 bg-surface-card border border-surface-border rounded-2xl hover:border-primary/30 transition-all">
                     <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest">Trazabilidad por Lotes</span>
                     <label class="relative inline-flex items-center cursor-pointer">
                       <input type="checkbox" formControlName="requires_batch" class="sr-only peer">
                       <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                     </label>
                  </div>
                </div>
              </div>
            </form>
          }

          <!-- GLOBAL TAB -->
          @if (activeTab() === 'GLOBAL') {
            <div class="space-y-6 animate-fade-in">
              <div class="grid grid-cols-1 gap-4 p-4 bg-surface-card rounded-2xl border border-surface-border">
                <div class="grid grid-cols-3 gap-4">
                  <div>
                    <label class="block text-[9px] font-black text-primary uppercase tracking-widest mb-2">Moneda</label>
                    <select [(ngModel)]="currency" (change)="loadPrices()" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all">
                      <option value="USD">USD</option>
                      <option value="MXN">MXN</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-[9px] font-black text-primary uppercase tracking-widest mb-2">Nodo</label>
                    <select [(ngModel)]="warehouseId" (change)="loadPrices()" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all">
                      <option [ngValue]="null">Global</option>
                      @for (w of warehouses; track w.id) {
                        <option [ngValue]="w.id">{{ w.code }}</option>
                      }
                    </select>
                  </div>
                  <div>
                    <label class="block text-[9px] font-black text-primary uppercase tracking-widest mb-2">Unidad</label>
                    <select [(ngModel)]="unitType" (change)="loadPrices()" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all">
                      <option value="BASE">Base</option>
                      <option value="SALE">Venta</option>
                    </select>
                  </div>
                </div>
              </div>

              <div class="border border-surface-border rounded-2xl overflow-hidden">
                <table class="w-full text-left border-collapse">
                  <thead>
                    <tr class="bg-surface-card/80 border-b border-surface-border">
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest w-16 text-center border-r border-surface-border">LVL</th>
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest border-r border-surface-border">Propósito</th>
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest w-40 text-right bg-primary/5">Monto</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-surface-border">
                    @for (tier of tiers; track tier) {
                      <tr class="hover:bg-primary/5 transition-colors group">
                        <td class="px-6 py-3 border-r border-surface-border text-center">
                          <span class="text-xs font-mono font-black text-surface-text-muted">{{ tier }}</span>
                        </td>
                        <td class="px-6 py-3 border-r border-surface-border">
                          <span class="text-[9px] text-surface-text-muted uppercase tracking-widest font-black">{{ getTierDescription(tier) }}</span>
                        </td>
                        <td class="px-6 py-3 bg-surface-card/20">
                          <div class="flex items-center justify-end gap-2">
                            <span class="text-[9px] font-bold text-surface-text-muted/60">{{ currency }}</span>
                            <input 
                              type="number" 
                              [(ngModel)]="tempPrices[tier]"
                              (keydown.enter)="savePrice(tier); focusNextRow(tier)"
                              [id]="'price-input-' + tier"
                              class="w-24 bg-transparent border-none text-xs font-mono font-bold text-surface-text outline-none text-right focus:text-primary"
                            />
                          </div>
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            </div>
          }

          <!-- B2B TAB -->
          @if (activeTab() === 'B2B') {
            <div class="space-y-6 animate-fade-in">
              <div class="flex items-center justify-between mb-2">
                <select [(ngModel)]="currencyB2B" (change)="loadAgreements()" class="w-32 bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-cyan-500">
                  <option value="USD">USD</option>
                  <option value="MXN">MXN</option>
                </select>
                <button (click)="openAddPartnerModal()" class="btn-primary py-2 px-4 text-[9px] italic">Nuevo Socio</button>
              </div>

              <!-- Partner Modal logic would need refactoring if it's a dialog -->
              @if (isAddingPartner()) {
                <app-partner-modal (onSaved)="onPartnerSaved($event)" (onClosed)="isAddingPartner.set(false)"></app-partner-modal>
              }

              <div class="border border-surface-border rounded-2xl overflow-hidden">
                <table class="w-full text-left border-collapse">
                  <thead>
                    <tr class="bg-surface-card/80 border-b border-surface-border">
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest border-r border-surface-border">Partner</th>
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest text-right bg-cyan-400/5">Pactado</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-surface-border">
                    @for (partner of partners(); track partner.id) {
                      <tr class="hover:bg-cyan-400/5 transition-colors group">
                        <td class="px-6 py-3 border-r border-surface-border">
                          <span class="text-xs font-bold text-surface-text">{{ partner.name }}</span>
                        </td>
                        <td class="px-6 py-3">
                           <div class="flex items-center justify-end gap-2">
                            <span class="text-[9px] font-bold text-surface-text-muted/60">{{ currencyB2B }}</span>
                            <input type="number" [(ngModel)]="tempAgreements[partner.id]" (keydown.enter)="saveAgreement(partner)" class="w-24 bg-transparent border-none text-xs font-mono font-bold text-surface-text outline-none text-right focus:text-cyan-400">
                           </div>
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            </div>
          }

          <!-- LOGISTICA TAB -->
          @if (activeTab() === 'LOGISTICA') {
            <div class="space-y-6 animate-fade-in">
              <div class="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-4">
                <form [formGroup]="variantForm" (submit)="saveVariant()" class="grid grid-cols-1 gap-4">
                  <div class="grid grid-cols-2 gap-3">
                    <input formControlName="brand" type="text" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-bold uppercase" placeholder="PROVEEDOR">
                    <input formControlName="mfg_part_number" type="text" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold uppercase" placeholder="N° PARTE">
                  </div>
                  <div class="flex gap-3">
                    <input formControlName="unit_price" type="number" class="flex-1 bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold" placeholder="COSTO REF.">
                    <button type="submit" [disabled]="variantForm.invalid" class="px-6 bg-amber-500 text-slate-950 rounded-xl text-[9px] font-black uppercase tracking-widest hover:bg-amber-400 transition-all">Vincular</button>
                  </div>
                </form>
              </div>

              <div class="border border-surface-border rounded-2xl overflow-hidden">
                <table class="w-full text-left border-collapse">
                  <tbody class="divide-y divide-surface-border">
                    @for (v of variants(); track v.id) {
                      <tr class="hover:bg-amber-500/5 transition-colors">
                        <td class="px-6 py-4">
                          <div class="flex flex-col">
                            <span class="text-[10px] font-black text-amber-500 uppercase">{{ v.brand }}</span>
                            <span class="text-xs font-mono font-bold text-surface-text">{{ v.mfg_part_number }}</span>
                          </div>
                        </td>
                        <td class="px-6 py-4 text-right">
                          <span class="text-xs font-mono font-bold text-surface-text">$ {{ v.unit_price | number:'1.2-2' }}</span>
                          <button (click)="removeVariant(v.id)" class="ml-4 p-2 text-surface-text-muted hover:text-red-500">
                            <mat-icon class="text-sm">delete</mat-icon>
                          </button>
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            </div>
          }
        </div>

        <!-- Sticky Footer Action -->
        <div class="pt-8 mt-auto border-t border-surface-border">
          <button (click)="finalSave()" 
                  [disabled]="loadingInfo()"
                  class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic overflow-hidden group relative">
            <div class="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            <mat-icon class="text-lg">verified</mat-icon>
            <span>{{ isEdit ? 'Sincronizar Datos Maestros' : 'Crear Producto Maestro' }}</span>
          </button>
        </div>
      </div>
  `,
  styles: [`
    :host { display: block; height: 100%; }
    .custom-scrollbar::-webkit-scrollbar { width: 3px; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0, 229, 255, 0.2); border-radius: 10px; }
  `]
})
export class ProductPriceListComponent implements OnInit {
  masterData = inject(MasterDataService);
  inventoryService = inject(InventoryService);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);
  private fb = inject(FormBuilder);
  drawerService = inject(SideDrawerService);

  @ViewChild('partnerModal') partnerModal!: PartnerModalComponent;

  product: any = null;
  isEdit = false;
  activeTab = signal<'INFO' | 'GLOBAL' | 'B2B' | 'LOGISTICA'>('INFO');
  
  set data(val: any) {
    if (val) {
      this.product = val.product || null;
      this.isEdit = !!this.product;
      if (val.activeTab) this.activeTab.set(val.activeTab);
      if (this.product) {
        this.patchInfoForm();
        this.loadPrices();
        this.loadPartners();
        this.loadAgreements();
        this.loadVariants();
      }
    }
  }

  currency = 'USD';
  warehouseId: string | null = null;
  unitType: 'BASE' | 'SALE' = 'BASE';
  
  warehouses: any[] = [];
  prices = signal<ProductPrice[]>([]);
  tempPrices: { [key: number]: number } = {};
  tiers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  currencyB2B = 'USD';
  partners = signal<any[]>([]);
  agreements = signal<any[]>([]);
  tempAgreements: { [key: string]: number } = {};
  isAddingPartner = signal(false);
  
  loadingInfo = signal(false);
  loadingVariants = signal(false);
  variants = signal<any[]>([]);

  infoForm = this.fb.group({
    sku: ['', [Validators.required]],
    name: ['', [Validators.required]],
    product_type: ['GOODS' as ProductType],
    uom_id: ['', [Validators.required]],
    category_id: [null as string | null],
    brand_id: [null as string | null],
    description: [''],
    sat_product_code: [''],
    hts_code: [''],
    is_taxable: [true],
    requires_batch: [false],
    requires_expiration: [false]
  });

  variantForm = this.fb.group({
    brand: ['', [Validators.required]],
    mfg_part_number: ['', [Validators.required]],
    unit_price: [0, [Validators.required, Validators.min(0)]]
  });

  ngOnInit() {
    this.loadWarehouses();
    if (!this.isEdit) {
      // Setup for new product
      this.activeTab.set('INFO');
    }
  }

  patchInfoForm() {
    if (!this.product) return;
    this.infoForm.patchValue({
      sku: this.product.sku,
      name: this.product.name,
      product_type: this.product.product_type,
      uom_id: this.product.base_uom_id || this.product.uom_id,
      category_id: this.product.category_id,
      brand_id: this.product.brand_id,
      description: this.product.description,
      sat_product_code: this.product.sat_product_code,
      hts_code: this.product.hts_code,
      is_taxable: this.product.is_taxable,
      requires_batch: this.product.requires_batch,
      requires_expiration: this.product.requires_expiration
    });
    
    if (this.masterData.isGlobal(this.product)) {
      this.infoForm.disable();
    }
  }

  finalSave() {
    if (this.infoForm.invalid) {
      this.notifications.warning('Formulario Incompleto', 'Por favor rellene los campos obligatorios.');
      return;
    }
    
    this.loadingInfo.set(true);
    const formData = this.infoForm.getRawValue();

    const request = this.isEdit 
      ? this.masterData.updateProduct(this.product.id, formData as any)
      : this.masterData.createProduct(formData as any);

    request.subscribe({
      next: (res) => {
        this.notifications.success('Éxito', this.isEdit ? 'Producto actualizado' : 'Producto creado');
        this.drawerService.notifyRefresh();
        if (!this.isEdit) {
          this.drawerService.close();
        } else {
          this.product = res.data;
          this.loadingInfo.set(false);
        }
      },
      error: (err) => {
        this.notifications.error('Error', err?.error?.detail || 'Operación fallida');
        this.loadingInfo.set(false);
      }
    });
  }

  loadWarehouses() {
    this.masterData.getWarehouses().subscribe(res => {
      this.warehouses = res.data;
    });
  }

  loadPartners() {
    this.masterData.getPartners().subscribe(res => {
      this.partners.set(res.data);
    });
  }

  loadAgreements() {
    if (!this.product) return;
    this.masterData.getAgreements(this.product.id, this.currencyB2B).subscribe(res => {
      this.agreements.set(res.data);
      this.tempAgreements = {};
      res.data.forEach((a: any) => {
        this.tempAgreements[a.partner_id] = a.amount;
      });
    });
  }

  saveAgreement(partner: any) {
    const amount = this.tempAgreements[partner.id];
    if (!amount) return;

    const payload = {
      product_id: this.product.id,
      partner_id: partner.id,
      amount: amount,
      currency: this.currencyB2B
    };

    this.masterData.upsertAgreement(payload).subscribe({
      next: () => this.loadAgreements()
    });
  }

  openAddPartnerModal() {
    this.isAddingPartner.set(true);
  }

  onPartnerSaved(partner: any) {
    this.loadPartners();
    this.isAddingPartner.set(false);
  }

  loadPrices() {
    if (!this.product) return;
    this.masterData.getPrices(this.product.id, this.warehouseId, this.currency, this.unitType).subscribe(res => {
      this.prices.set(res.data);
      this.tempPrices = {};
      res.data.forEach((p: any) => {
        this.tempPrices[p.price_list_index] = p.amount;
      });
    });
  }

  savePrice(tier: number) {
    const amount = this.tempPrices[tier];
    if (!amount) return;

    const payload: Partial<ProductPrice> = {
      product_id: this.product.id,
      price_list_index: tier,
      amount: amount,
      currency: this.currency,
      unit_type: this.unitType,
      warehouse_id: this.warehouseId,
      is_active: true
    };

    this.masterData.upsertPrice(payload).subscribe({
      next: () => this.loadPrices()
    });
  }

  getTierDescription(tier: number): string {
    const descriptions: { [key: number]: string } = {
      1: 'Público General',
      2: 'Mayorista',
      3: 'Distribuidor',
      4: 'Inter-Compañía',
      5: 'Gubernamental',
      6: 'Preferencial A',
      7: 'Preferencial B',
      8: 'Promoción',
      9: 'Costo Base',
      10: 'Liquidación'
    };
    return descriptions[tier] || 'Personalizado';
  }

  focusNextRow(currentTier: number) {
    if (currentTier < 10) {
      setTimeout(() => {
        const nextInput = document.getElementById(`price-input-${currentTier + 1}`);
        if (nextInput) nextInput.focus();
      }, 50);
    }
  }

  async loadVariants() {
    if (!this.product) return;
    try {
      const data = await this.inventoryService.getProductVariants(this.product.id);
      this.variants.set(data || []);
    } catch (err) {
      console.error('[Variants] Error loading:', err);
    }
  }

  async saveVariant() {
    if (this.variantForm.invalid) return;
    this.loadingVariants.set(true);

    const data = {
      ...this.variantForm.value,
      product_id: this.product.id,
      internal_sku: this.product.sku
    };

    try {
      await this.inventoryService.upsertVariant(data);
      this.notifications.success('Éxito', 'Variante registrada');
      this.variantForm.reset({ unit_price: 0 });
      await this.loadVariants();
    } catch (err: any) {
      this.notifications.error('Error', err?.error?.message || 'Falla al registrar');
    } finally {
      this.loadingVariants.set(false);
    }
  }

  async removeVariant(id: string) {
    if (!confirm('¿Eliminar variante?')) return;
    try {
      await this.inventoryService.deleteVariant(id);
      await this.loadVariants();
    } catch (err) {
      console.error('[Variants] Error deleting:', err);
    }
  }
}
