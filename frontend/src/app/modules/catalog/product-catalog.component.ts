import { Component, inject, signal, computed, OnInit, effect } from '@angular/core';
import { TranslationService } from '../../core/services/translation.service';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MasterDataService, Product, SYSTEM_USER_ID, ProductStatus, VersionStatus } from '../../core/services/master-data.service';
import { AuthService } from '../../core/services/auth.service';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { NotificationService } from '../../core/services/notification.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { ProductPriceListComponent } from './product-price-list.component';
import { PriceImportDashboardComponent } from './price-import-dashboard.component';

@Component({
  selector: 'app-product-catalog',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatDialogModule, TranslatePipe],
  template: `
    <div class="space-y-8 animate-fade-in">
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 class="text-4xl font-black text-surface-text tracking-tighter uppercase italic">
            {{ 'catalog.title' | translate:'Centro de Control de Catálogo' }}
          </h1>
          <p class="text-surface-text-muted font-mono text-xs tracking-widest uppercase mt-2">
            {{ 'catalog.subtitle' | translate:'Gestión centralizada de productos y variantes maestras' }}
          </p>
        </div>
        
        <div class="flex items-center gap-3">
          <button class="btn-primary py-2 px-6 flex items-center gap-2" (click)="createNewProduct()">
            <mat-icon class="text-sm">add</mat-icon>
            <span class="text-[10px] font-black uppercase tracking-[0.2em] italic">{{ 'catalog.new_product' | translate:'Nuevo Producto' }}</span>
          </button>
          
          <button class="bg-surface-card hover:bg-surface-border text-surface-text-muted hover:text-primary transition-all p-3 rounded-xl border border-surface-border shadow-sm active:scale-95" (click)="loadProducts()" [title]="'common.refresh' | translate:'Refrescar'">
            <mat-icon class="text-sm">refresh</mat-icon>
          </button>

          <button class="flex items-center gap-3 bg-cyan-500/10 hover:bg-cyan-500 text-cyan-600 hover:text-white border-2 border-cyan-500/30 hover:border-cyan-500 transition-all py-2.5 px-6 rounded-xl shadow-lg shadow-cyan-500/5 active:scale-95 group" 
                  (click)="openImportDashboard()" 
                  title="Importar Precios Masivo">
            <mat-icon class="text-lg group-hover:rotate-12 transition-transform">upload_file</mat-icon>
            <span class="text-[10px] font-black uppercase tracking-[0.2em] italic hidden md:block">Importar Precios</span>
          </button>
        </div>
      </div>

      <!-- Catalog Grid -->
      <div class="grid grid-cols-1 gap-8">
        <div class="industrial-card glass-card border-neon-blue-30">
          <div class="p-6 border-b border-surface-border flex items-center justify-between bg-surface-bg/30">
            <h2 class="text-xs font-black text-surface-text uppercase tracking-[0.2em]">
              {{ 'catalog.product_list' | translate:'Lista de Productos Maestros' }}
            </h2>
            <div class="flex items-center gap-4">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded bg-primary/20 border border-primary/50"></div>
                <span class="text-[9px] font-bold text-surface-text-muted uppercase">{{ 'catalog.origin.global' | translate:'Global' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded bg-surface-bg border border-surface-border"></div>
                <span class="text-[9px] font-bold text-surface-text-muted uppercase">{{ 'catalog.origin.private' | translate:'Privado' }}</span>
              </div>
            </div>
          </div>

          <div class="relative overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-surface-bg/50">
                  <th class="px-6 py-3 text-[9px] font-black text-surface-text-muted uppercase tracking-widest w-10"></th>
                  <th class="px-6 py-3 text-[9px] font-black text-surface-text-muted uppercase tracking-widest">{{ 'catalog.table.sku' | translate:'SKU' }}</th>
                  <th class="px-6 py-3 text-[9px] font-black text-surface-text-muted uppercase tracking-widest">{{ 'catalog.table.product' | translate:'Producto' }}</th>
                  <th class="px-6 py-3 text-[9px] font-black text-surface-text-muted uppercase tracking-widest">{{ 'catalog.table.fiscal' | translate:'Fiscal / SAT' }}</th>
                  <th class="px-6 py-3 text-[9px] font-black text-surface-text-muted uppercase tracking-widest">{{ 'catalog.table.type' | translate:'Tipo / Estado' }}</th>
                  <th class="px-6 py-3 text-[9px] font-black text-surface-text-muted uppercase tracking-widest">{{ 'catalog.table.origin' | translate:'Origen' }}</th>
                  <th class="px-6 py-3 text-[9px] font-black text-surface-text-muted uppercase tracking-widest text-right">{{ 'catalog.table.actions' | translate:'Acciones' }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-surface-border">
                @for (product of displayedProducts(); track product.id) {
                  <tr 
                    class="hover:bg-white/5 transition-colors group relative hover:z-50"
                    [ngClass]="{'bg-primary/5': masterData.isGlobal(product)}"
                  >
                    <td class="px-6 py-4">
                      <button 
                        (click)="toggleExpand(product.id)"
                        class="text-surface-text-muted hover:text-primary transition-colors"
                      >
                        <mat-icon class="text-sm transition-transform" [class.rotate-90]="isExpanded(product.id)">
                          chevron_right
                        </mat-icon>
                      </button>
                    </td>
                    <td class="px-6 py-4">
                      <span class="text-[10px] font-mono font-bold text-surface-text uppercase tracking-tighter">{{ product.sku }}</span>
                    </td>
                    <td class="px-6 py-4">
                      <div class="flex flex-col">
                        <span class="text-xs font-bold text-surface-text group-hover:text-primary transition-colors">
                          {{ product.name }}
                        </span>
                        <div class="flex items-center gap-2 mt-1">
                          @if (masterData.isSystemCreated(product)) {
                            <span class="text-[8px] bg-primary/20 text-primary px-1.5 py-0.5 rounded font-black tracking-tighter">{{ 'catalog.system' | translate:'SISTEMA' }}</span>
                          }
                          <span class="text-[8px] font-mono text-surface-text-muted">v.{{ product.version_id }}</span>
                        </div>
                      </div>
                    </td>
                    <td class="px-6 py-4">
                      <div class="flex items-center gap-3">
                        <span class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">{{ product.product_type }}</span>
                        <span 
                          class="text-[8px] font-black px-2 py-0.5 rounded-full tracking-tighter"
                          [ngClass]="getStatusClass(product.status)"
                        >
                          {{ product.status }}
                        </span>
                      </div>
                    </td>
                    <td class="px-6 py-4">
                      <div class="flex flex-col gap-0.5">
                        <span class="text-[9px] font-mono text-cyan-400 font-bold" *ngIf="product.sat_product_code">SAT: {{ product.sat_product_code }}</span>
                        <span class="text-[9px] font-mono text-purple-400 font-bold" *ngIf="product.hts_code">HTS: {{ product.hts_code }}</span>
                        <span class="text-[8px] text-surface-text-muted uppercase" *ngIf="!product.sat_product_code && !product.hts_code">{{ 'common.pending' | translate:'PENDIENTE' }}</span>
                      </div>
                    </td>
                    <td class="px-6 py-4">
                      @if (masterData.isGlobal(product)) {
                        <div class="flex items-center gap-1.5">
                          <mat-icon class="text-primary text-xs w-3 h-3">public</mat-icon>
                          <span class="text-[9px] font-black text-primary uppercase tracking-widest">{{ 'catalog.origin.global' | translate:'Global' }}</span>
                        </div>
                      } @else {
                        <div class="flex items-center gap-1.5">
                          <mat-icon class="text-surface-text-muted text-xs w-3 h-3">business</mat-icon>
                          <span class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">{{ 'catalog.origin.private' | translate:'Privado' }}</span>
                        </div>
                      }
                    </td>
                    <td class="px-6 py-4 text-right">
                      <div class="flex items-center justify-end gap-1">
                        <button 
                          (click)="manageLogistics(product)"
                          class="p-2 text-surface-text-muted hover:text-amber-400 transition-colors"
                          title="Gestionar Logística (Variantes/Proveedores)"
                        >
                          <mat-icon class="text-sm">local_shipping</mat-icon>
                        </button>
                        <button 
                          (click)="managePrices(product)"
                          class="p-2 text-surface-text-muted hover:text-emerald-400 transition-colors relative"
                          [title]="'catalog.manage_prices' | translate:'Gestionar Precios'"
                        >
                          <mat-icon class="text-sm">payments</mat-icon>
                          @if (getMissingFields(product).length > 0) {
                            <div class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-amber-500 rounded-full border-2 border-surface-bg shadow-sm"></div>
                            @if (showActiveTooltip() && getFirstMissingProductId() === product.id) {
                               <div class="absolute right-[110%] top-[-50px] w-72 bg-surface-bg border-4 border-amber-500 rounded-3xl p-5 shadow-[0_30px_90px_rgba(245,158,11,0.4)] z-[9999] flex flex-col gap-4 animate-fade-in text-surface-text" 
                                    style="pointer-events: all;"
                                    (click)="$event.stopPropagation()">
                                 <div class="flex items-center justify-between border-b border-surface-border pb-3">
                                   <div class="flex items-center gap-2">
                                     <mat-icon class="text-xl text-amber-500">warning</mat-icon>
                                     <span class="text-[10px] font-black uppercase tracking-widest italic text-amber-500">Acción Requerida</span>
                                   </div>
                                   <button (click)="closeTooltip(); $event.stopPropagation()" class="text-surface-text-muted hover:text-primary transition-colors">
                                     <mat-icon class="text-sm">close</mat-icon>
                                   </button>
                                 </div>
                                 <p class="text-[10px] font-bold leading-tight text-left">
                                   Completa la configuración maestra para habilitar la trazabilidad:
                                 </p>
                                 <div class="flex flex-wrap gap-1">
                                   @for (m of getMissingFields(product); track m) {
                                     <span class="px-2 py-1 bg-amber-500/10 text-amber-600 rounded-lg text-[8px] font-black uppercase tracking-tighter border border-amber-500/20">SIN {{ m }}</span>
                                   }
                                 </div>
                                 
                                 <div class="grid grid-cols-2 gap-2 mt-2">
                                   <button (click)="editProduct(product); closeTooltip(); $event.stopPropagation()" 
                                           class="py-3 bg-surface-card hover:bg-surface-border text-surface-text rounded-xl text-[8px] font-black uppercase tracking-widest transition-all border border-surface-border flex flex-col items-center justify-center gap-1 group/btn shadow-sm">
                                     <mat-icon class="text-xs">edit_note</mat-icon>
                                     <span class="mt-1">Datos</span>
                                   </button>
                                   
                                   <button (click)="managePrices(product); closeTooltip(); $event.stopPropagation()" 
                                           class="py-3 bg-emerald-500 text-white rounded-xl text-[8px] font-black uppercase tracking-widest hover:bg-emerald-600 transition-all flex flex-col items-center justify-center gap-1 group/btn shadow-lg shadow-emerald-500/20">
                                     <mat-icon class="text-xs">payments</mat-icon>
                                     <span class="mt-1">Precios</span>
                                   </button>
                                 </div>
                                 
                                 <button (click)="manageLogistics(product); closeTooltip(); $event.stopPropagation()" 
                                         class="py-3 bg-amber-500 text-white rounded-xl text-[8px] font-black uppercase tracking-widest hover:bg-amber-600 transition-all flex flex-col items-center justify-center gap-1 group/btn w-full shadow-lg shadow-amber-500/20">
                                   <mat-icon class="text-xs">local_shipping</mat-icon>
                                   <span class="mt-1">Logística</span>
                                 </button>
                                 
                                 <div class="absolute top-1/2 -translate-y-1/2 -right-[10px] w-5 h-5 bg-surface-bg border-t-4 border-r-4 border-amber-500 transform rotate-45 z-[-1]"></div>
                               </div>
                             }
                           }
                        </button>
                        
                        @if (masterData.isGlobal(product)) {
                          <button class="p-2 text-surface-text-muted/30 cursor-not-allowed" title="Solo Lectura">
                            <mat-icon class="text-sm">lock</mat-icon>
                          </button>
                        } @else {
                          <button 
                            class="p-2 text-surface-text-muted hover:text-primary transition-colors"
                            (click)="editProduct(product)"
                          >
                            <mat-icon class="text-sm">edit</mat-icon>
                          </button>

                          <button 
                            *ngIf="isAdmin()"
                            class="p-2 text-surface-text-muted hover:text-red-400 transition-colors"
                            (click)="deleteProduct(product)"
                          >
                            <mat-icon class="text-sm">delete</mat-icon>
                          </button>
                        }
                      </div>
                    </td>
                  </tr>

                  <!-- Detail View (Versions) -->
                  @if (isExpanded(product.id)) {
                    <tr class="bg-black/20">
                      <td colspan="7" class="px-12 py-6">
                        <div class="border-l-2 border-primary/30 pl-6 space-y-4">
                          <h3 class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-4">Historial de Versiones</h3>
                          
                          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            @for (version of product.versions; track version.id) {
                              <div class="glass-card p-4 border-white/5 hover:border-primary/30 transition-all group/version">
                                <div class="flex items-center justify-between mb-3">
                                  <span class="text-[10px] font-mono font-bold text-surface-text">REV.{{ version.version_number }}</span>
                                  <span 
                                    class="text-[8px] font-black px-2 py-0.5 rounded-full tracking-tighter"
                                    [ngClass]="getVersionStatusClass(version.version_status)"
                                  >
                                    {{ version.version_status }}
                                  </span>
                                </div>
                                <div class="flex items-center gap-2 mb-2">
                                  <mat-icon class="text-[10px] w-3 h-3" [class.text-neon-green]="version.is_active" [class.text-surface-text-muted]="!version.is_active">
                                    {{ version.is_active ? 'check_circle' : 'radio_button_unchecked' }}
                                  </mat-icon>
                                  <span class="text-[9px] font-bold uppercase tracking-widest" [class.text-surface-text]="version.is_active" [class.text-surface-text-muted]="!version.is_active">
                                    {{ version.is_active ? 'Activa' : 'Inactiva' }}
                                  </span>
                                </div>
                                <p class="text-[9px] text-surface-text-muted italic leading-relaxed">
                                  {{ version.change_reason || 'Sin descripción' }}
                                </p>
                              </div>
                            } @empty {
                              <div class="col-span-full py-4 text-center border border-dashed border-surface-border rounded-lg">
                                <span class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">No hay versiones</span>
                              </div>
                            }
                          </div>
                        </div>
                      </td>
                    </tr>
                  }
                } @empty {
                  <tr>
                    <td colspan="7" class="px-6 py-12 text-center">
                      <div class="flex flex-col items-center gap-2">
                        <mat-icon class="text-surface-text-muted/20 text-4xl h-10 w-10">inventory_2</mat-icon>
                        <span class="text-xs font-bold text-surface-text-muted uppercase tracking-widest">No hay productos</span>
                      </div>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .glow-text {
      text-shadow: 0 0 20px rgba(var(--primary-rgb), 0.3);
    }
    .glass-card {
      background: var(--color-surface-card);
      backdrop-filter: blur(10px);
      border: 1px solid var(--color-surface-border);
    }
    .dark .glass-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .border-neon-blue-30 {
      border-color: rgba(0, 242, 255, 0.3);
    }
  `]
})
export class ProductCatalogComponent implements OnInit {
  masterData = inject(MasterDataService);
  protected translationService = inject(TranslationService);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);
  private dialog = inject(MatDialog);
  
  products = signal<Product[]>([]);
  expandedIds = signal<Set<string>>(new Set());
  selectedProductForPrice = signal<Product | null>(null);
  showIncompletePanel = signal(true);
  filterIncomplete = signal(false);
  isAdmin = signal(false);
  drawerService = inject(SideDrawerService);

  constructor() {
    effect(() => {
      const roles = this.auth.roles();
      this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));
    });
  }

  openImportDashboard(): void {
    const ref = this.dialog.open(PriceImportDashboardComponent, {
      width: '760px',
      maxWidth: '95vw',
      panelClass: 'ic-dark-dialog',
      disableClose: false
    });
    // Auto-refresh: when Areli closes the importer, the catalog prices update instantly
    ref.afterClosed().subscribe(() => this.loadProducts());
  }

  /** Products missing at least one critical field */
  incompleteProducts = computed(() =>
    this.products().filter(p => !this.masterData.isGlobal(p) && this.getMissingFields(p).length > 0)
  );

  /** Displayed list (filtered or full) */
  displayedProducts = computed(() =>
    this.filterIncomplete()
      ? this.incompleteProducts()
      : this.products()
  );

  ngOnInit() {
    this.loadProducts();
    this.drawerService.refresh$.subscribe(() => this.loadProducts());
  }

  loadProducts() {
    this.masterData.getProducts().subscribe({
      next: (response) => {
        if (response.status === 'success') {
          this.products.set(response.data);
        }
      },
      error: () => {
        // Fallback mock data respecting the specs
        this.products.set([
          {
            id: '1',
            sku: 'RAW-ALU-001',
            name: 'Aluminio 6061-T6',
            company_id: null, // GLOBAL
            version_id: 1,
            created_by: SYSTEM_USER_ID,
            created_at: new Date().toISOString(),
            product_type: 'GOODS',
            status: 'ACTIVE',
            is_taxable: true,
            allow_price_override: false,
            is_active: true,
            versions: [
              { id: 'v1', version_number: 1, version_status: 'PUBLISHED', is_active: true, is_validated: true, change_reason: 'Versión inicial aprobada' },
              { id: 'v2', version_number: 2, version_status: 'DESIGN', is_active: false, is_validated: false, change_reason: 'Ajuste de aleación experimental' }
            ]
          },
          {
            id: '2',
            sku: 'PRD-BOLT-M8',
            name: 'Tornillo M8 x 25mm',
            company_id: 'comp-789', // PRIVATE
            version_id: 2,
            created_by: 'user-456',
            created_at: new Date().toISOString(),
            product_type: 'GOODS',
            status: 'DRAFT',
            is_taxable: true,
            allow_price_override: true,
            is_active: true,
            versions: [
              { id: 'v3', version_number: 1, version_status: 'ARCHIVED', is_active: false, is_validated: true },
              { id: 'v4', version_number: 2, version_status: 'DRAFT', is_active: true, is_validated: false, change_reason: 'Rediseño de rosca' }
            ]
          }
        ]);
      }
    });
  }

  toggleExpand(id: string) {
    const next = new Set(this.expandedIds());
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    this.expandedIds.set(next);
  }

  isExpanded(id: string): boolean {
    return this.expandedIds().has(id);
  }

  getStatusClass(status: ProductStatus): string {
    switch (status) {
      case 'ACTIVE': return 'bg-neon-green/20 text-neon-green border border-neon-green/30';
      case 'DRAFT': return 'bg-amber-500/20 text-amber-400 border border-amber-500/30';
      case 'INACTIVE': return 'bg-red-500/20 text-red-400 border border-red-500/30';
      default: return 'bg-surface-bg border border-surface-border text-surface-text-muted';
    }
  }

  createNewProduct() {
    const actId = this.auth.activeCompanyId();
    if (!actId) {
      this.notifications.error(
        this.translationService.translate('common.invalid_context', 'Invalid Context'),
        this.translationService.translate('auth.must_select_company', 'You must select a company.')
      );
      return;
    }
    
    // Open Product Form in Drawer
    this.drawerService.open(ProductPriceListComponent, {
      title: 'Nuevo Producto',
      subtitle: 'Configuración Maestra de Item',
      icon: 'add_box'
    }, { activeTab: 'INFO' });
  }

  getVersionStatusClass(status: VersionStatus): string {
    switch (status) {
      case 'PUBLISHED': return 'bg-neon-green/20 text-neon-green';
      case 'DESIGN': return 'bg-blue-500/20 text-blue-400';
      case 'UNDER_REVIEW': return 'bg-purple-500/20 text-purple-400';
      case 'EXPERIMENTAL': return 'bg-pink-500/20 text-pink-400';
      case 'ARCHIVED': return 'bg-surface-bg text-surface-text-muted';
      default: return 'bg-amber-500/20 text-amber-400';
    }
  }

  managePrices(product: Product) {
    this.drawerService.open(ProductPriceListComponent, {
      title: 'Gestión de Precios',
      subtitle: product.sku + ' - ' + product.name,
      icon: 'payments'
    }, { product, activeTab: 'GLOBAL' });
  }

  editProduct(product: Product) {
    if (this.masterData.isGlobal(product)) {
      this.notifications.warning(
        this.translationService.translate('common.access_denied', 'Access Denied'),
        this.translationService.translate('catalog.global_readonly_msg', 'Global records are read-only.')
      );
      return;
    }
    
    this.drawerService.open(ProductPriceListComponent, {
      title: 'Editar Producto',
      subtitle: product.sku + ' - ' + product.name,
      icon: 'edit_note'
    }, { product, activeTab: 'INFO' });
  }

  manageLogistics(product: Product) {
    this.drawerService.open(ProductPriceListComponent, {
      title: 'Logística de Producto',
      subtitle: product.sku + ' - ' + product.name,
      icon: 'local_shipping'
    }, { product, activeTab: 'LOGISTICA' });
  }

  async deleteProduct(product: Product) {
    if (!confirm(`¿Estás seguro de eliminar el producto ${product.sku}?`)) return;

    this.masterData.deleteProduct(product.id).subscribe({
      next: (res) => {
        if (res.status === 'success') {
          this.notifications.success('Eliminado', product.sku);
          this.loadProducts();
        }
      },
      error: (err) => {
        this.notifications.error('Error', err?.error?.detail || 'No se pudo eliminar el producto');
      }
    });
  }

  /** Returns list of missing critical field labels for a product */
  getMissingFields(p: Product): string[] {
    const missing: string[] = [];
    if (!p.last_price) missing.push('Precio');
    if (!p.sat_product_code) missing.push('SAT');
    if (!p.category_id) missing.push('Categoría');
    return missing;
  }

  showActiveTooltip = signal<boolean>(true);

  closeTooltip() {
    this.showActiveTooltip.set(false);
  }

  getFirstMissingProductId(): string | null {
    const prod = this.displayedProducts().find(p => this.getMissingFields(p).length > 0);
    return prod ? prod.id : null;
  }
}
