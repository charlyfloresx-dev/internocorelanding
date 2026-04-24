import { Injectable, inject, signal, effect, computed, untracked } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError, of, lastValueFrom } from 'rxjs';
import { tap } from 'rxjs/operators';
import { AuthService } from './auth.service';
import { SystemHealthService } from './system-health.service';
import { environment } from '../../../environments/environment';

export const SYSTEM_USER_ID = '00000000-0000-0000-0000-000000000000';

export enum PartnerType {
  CUSTOMER = 'CUSTOMER',
  SUPPLIER = 'SUPPLIER',
  BOTH = 'BOTH'
}

export type ProductStatus = 'DRAFT' | 'ACTIVE' | 'INACTIVE' | 'DISCONTINUED';
export type ProductType = 'GOODS' | 'SERVICE';
export type VersionStatus = 'DESIGN' | 'EXPERIMENTAL' | 'UNDER_REVIEW' | 'PUBLISHED' | 'DEPRECATED' | 'ARCHIVED' | 'DRAFT';

export interface BaseRead {
  id: string;
  company_id: string | null;
}

export interface Brand extends BaseRead {
  name: string;
  code: string;
  translation_key?: string;
}

export interface Category extends BaseRead {
  name: string;
  code: string;
  translation_key?: string;
}

export interface Concept extends BaseRead {
  name: string;
  code: string;
  type: 'ENTRY' | 'OUTPUT' | 'TRANSFER' | 'IN' | 'OUT' | 'ENTRADA' | 'SALIDA' | 'TRASPASO';
  requires_external_entity: boolean;
  requires_target_warehouse: boolean;
  operation_type?: string;
  affect_stock?: boolean;  // Does this concept affect stock levels?
  is_system?: boolean;     // System-managed (cannot be deleted)
  is_active?: boolean;      // Visibility flag

  translation_key?: string | null;
}



export interface UOM extends BaseRead {
  code: string;
  name: string;
  abbreviation: string;
  conversion_factor: number;
  plural?: string;
  translation_key?: string;
}

export interface Warehouse extends BaseRead {
  name: string;
  code: string;
  capacity: number;
  current_occupancy?: number;
  status: 'ACTIVE' | 'INACTIVE';
  country_code?: string;
}

export interface Partner extends BaseRead {
  name: string;
  code: string;
  tax_id: string; // RFC/TaxID
  type: PartnerType;
  email?: string;
  status: 'ACTIVE' | 'INACTIVE';
  last_transaction_id?: string;
}

export interface ProductVersion {
  id: string;
  version_number: number;
  version_status: VersionStatus;
  is_active: boolean;
  is_validated: boolean;
  change_reason?: string;
}

export interface Product extends BaseRead {
  name: string;
  sku: string;
  description?: string;
  product_type: ProductType;
  status: ProductStatus;
  
  // Phase 33.5: Fiscal & Commercial
  sat_product_code?: string;
  hts_code?: string;
  is_taxable: boolean;
  allow_price_override: boolean;
  
  category_id?: string;
  brand_id?: string;
  requires_batch?: boolean;
  requires_expiration?: boolean;
  
  base_uom_id?: string;
  group_id?: string;
  created_at: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
  version_id: number;
  is_active: boolean;
  versions?: ProductVersion[];
  
  // Financial metadata
  last_price?: number;
  currency?: string;
}

export interface ProductPrice {
  id: string;
  product_id: string;
  price_list_index: number;
  amount: number;
  currency: string;
  unit_type: 'BASE' | 'SALE';
  warehouse_id?: string | null;
  effective_date: string;
  is_active: boolean;
}

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  message: string;
  meta: {
    trace_id?: string;
    latency?: string;
  };
}


@Injectable({
  providedIn: 'root'
})
export class MasterDataService {
  private http = inject(HttpClient);
  private health = inject(SystemHealthService);
  private apiUrl = environment.masterDataUrl;
  private auth = inject(AuthService);

  // === Catalogs State (Signals) ===
  public warehouses = signal<Warehouse[]>([]);
  public concepts = signal<Concept[]>([]);
  public uoms = signal<UOM[]>([]);
  public categories = signal<Category[]>([]);
  public brands = signal<Brand[]>([]);
  public loading = signal<boolean>(false);

  /**
   * SIGNAL-SAFE: true once catalogs have been fetched at least once for the current tenant.
   * Use this in component computed() guards to prevent sending null concept_id to backend.
   */
  public readonly catalogsLoaded = computed(() =>
    !this.loading() && this.concepts().length > 0
  );

  /**
   * Three-state catalog readiness for defensive UI.
   * LOADING — fetch in progress (block submit buttons)
   * READY   — concepts loaded, concept_id can be resolved
   * ERROR   — no concepts found after load (show fallback / retry)
   */
  public readonly conceptCatalogState = computed<'LOADING' | 'READY' | 'ERROR'>(() => {
    if (this.loading()) return 'LOADING';
    return this.concepts().length > 0 ? 'READY' : 'ERROR';
  });

  constructor() {
    this.setupAutoSync();
  }

  private lastSyncedCompanyId: string | null = null;
  /**
   * Industrial Guard: Automatically syncs master data whenever company context changes.
   */
  private setupAutoSync() {
    effect(() => {
      const companyId = this.auth.activeCompanyId();
      
      // Industrial Guard: Use untracked to prevent reading signals inside refreshCatalogs 
      // (like 'loading') from becoming dependencies that cause an infinite loop.
      untracked(() => {
        if (companyId === this.lastSyncedCompanyId && companyId !== null) {
          console.log(`[MasterDataService] 💤 Company context already synced: ${companyId}. Skipping refresh.`);
          return;
        }

        if (companyId) {
          console.log(`[MasterDataService] 🔄 Company context detected: ${companyId}. Refreshing catalogs...`);
          this.lastSyncedCompanyId = companyId;
          this.refreshCatalogs();
        } else {
          this.lastSyncedCompanyId = null;
          this.clearState();
        }
      });
    }, { allowSignalWrites: true });
  }

  /**
   * UPSERTS A B2B PRICE AGREEMENT
   */
  upsertAgreement(payload: any): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(`${this.apiUrl}/prices/agreements`, payload)
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * GETS B2B PRICE AGREEMENTS FOR PRODUCT
   */
  getAgreements(productId: string, currency?: string): Observable<ApiResponse<any[]>> {
    let params: any = {};
    if (currency) params.currency = currency;
    return this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/prices/products/${productId}/agreements`, { params })
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * Loads all core catalogs in parallel.
   */
  /**
   * Industrial Pattern: Unit of Measure Resolution
   */
  public resolveUomByCode(code: string): UOM | undefined {
    return this.uoms().find(u => u.code.toUpperCase() === code.toUpperCase());
  }

  public async refreshCatalogs(): Promise<void> {
    if (this.loading()) return;
    
    this.loading.set(true);
    try {
      const [wh, con, uom, cat, br] = await Promise.all([
        lastValueFrom(this.getWarehouses()),
        lastValueFrom(this.getConcepts()),
        lastValueFrom(this.getUoms()),
        lastValueFrom(this.getCategories()),
        lastValueFrom(this.getBrands())
      ]);

      this.warehouses.set(wh.data || []);
      this.concepts.set(con.data || []);
      this.uoms.set(uom.data || []);
      this.categories.set(cat.data || []);
      this.brands.set(br.data || []);
      
      console.log(`[MasterDataService] ✅ Catalogs synced: ${wh.data?.length || 0} warehouses, ${con.data?.length || 0} concepts.`);
    } catch (err) {
      console.error('[MasterDataService] ❌ Failed to refresh catalogs:', err);
    } finally {
      this.loading.set(false);
    }
  }

  private clearState() {
    this.warehouses.set([]);
    this.concepts.set([]);
    this.uoms.set([]);
    this.categories.set([]);
    this.brands.set([]);
    console.log('[MasterDataService] 🔒 Catalog state cleared.');
  }

  // ═══════════════════════════════════════════════════════
  // CONCEPT RESOLUTION HELPERS (Signal-Safe)
  // ═══════════════════════════════════════════════════════

  /**
   * Resolves a concept by its deterministic code (e.g. 'INT-TRA', 'PUR-REC').
   * Returns null if the catalog is still loading — NEVER resolves during LOADING state.
   * Use inside a computed() in components to get a reactive, null-safe concept ID.
   *
   * Standard system codes:
   *   INT-TRA  — Inter-Company Transfer (Traspaso Inter-Empresa)
   *   PUR-REC  — Purchase Receipt (Recepción de Compra)
   *   PUR-RET  — Purchase Return (Devolución a Proveedor)
   *   ADJ-POS  — Positive Adjustment (Ajuste Positivo)
   *   ADJ-NEG  — Negative Adjustment (Ajuste Negativo)
   *   SCRAP    — Material Scrap (Merma/Baja)
   */
  public resolveConceptByCode(code: string): Concept | null {
    // Guard: Return null if catalog is not ready yet — prevents sending null concept_id
    if (!this.catalogsLoaded()) return null;
    return this.concepts().find(c => c.code.toUpperCase() === code.toUpperCase()) ?? null;
  }

  /**
   * Filters concepts by their movement type.
   * Useful for dropdowns: e.g., show only EXIT concepts for a manual exit form.
   */
  resolveConceptsByType(type: Concept['type']): Concept[] {
    if (!this.catalogsLoaded()) return [];
    return this.concepts().filter(c => c.type === type);
  }

  /**
   * Reactive computed: use in templates or computed() for a filtered concept list.
   * Returns an empty array during LOADING — prevents rendering stale options.
   */
  conceptsForType(type: Concept['type']) {
    return computed(() => this.resolveConceptsByType(type));
  }



  // Helper to check if a record is global
  isGlobal(record: BaseRead): boolean {
    return record.company_id === null;
  }

  // Helper to check if a record is system-created
  isSystemCreated(record: Product): boolean {
    return record.created_by === SYSTEM_USER_ID;
  }

  /**
   * Pattern: Cache-Then-Fallback (Industrial Resilience)
   * Writes to localStorage on success, falls back on network failure.
   */
  private fetchWithFallback<T>(cacheKey: string, request: Observable<ApiResponse<T>>): Observable<ApiResponse<T>> {
    return request.pipe(
      tap(res => {
        if (res.status === 'success') {
          localStorage.setItem(`ic_cache_${cacheKey}`, JSON.stringify(res));
          this.health.reportSuccess('masterData');
        }
      }),
      catchError(err => {
        this.health.reportFailure('masterData');
        const cached = localStorage.getItem(`ic_cache_${cacheKey}`);
        if (cached) {
          console.warn(`[MasterDataService] ⚠️ Serving cached ${cacheKey} due to network error.`);
          try {
            return of(JSON.parse(cached) as ApiResponse<T>);
          } catch {}
        }
        return throwError(() => err);
      })
    );
  }

  private productCache = signal<ApiResponse<Product[]> | null>(null);


  // --- PRODUCTS ---
  getProducts(q?: string, warehouseId?: string): Observable<ApiResponse<Product[]>> {
    let url = q ? `${this.apiUrl}/products/?q=${encodeURIComponent(q)}` : `${this.apiUrl}/products/`;
    
    if (warehouseId) {
      url += (url.includes('?') ? '&' : '?') + `warehouse_id=${warehouseId}`;
    }
    
    const req = this.http.get<ApiResponse<Product[]>>(url);
    
    // Solo cacheamos la lista completa (sin query y sin warehouse)
    if (!q && !warehouseId) {
      return this.fetchWithFallback('products', req);
    }
    return req.pipe(catchError(this.handleError));
  }

  getProduct(id: string): Observable<ApiResponse<Product>> {
    return this.http.get<ApiResponse<Product>>(`${this.apiUrl}/products/${id}`).pipe(
      catchError(this.handleError)
    );
  }

  createProduct(product: Partial<Product>): Observable<ApiResponse<Product>> {
    return this.http.post<ApiResponse<Product>>(`${this.apiUrl}/products/`, product).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  updateProduct(id: string, product: Partial<Product>): Observable<ApiResponse<Product>> {
    return this.http.patch<ApiResponse<Product>>(`${this.apiUrl}/products/${id}`, product).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  deleteProduct(id: string): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`${this.apiUrl}/products/${id}`).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  // --- UOMs ---
  getUoms(): Observable<ApiResponse<UOM[]>> {
    const req = this.http.get<ApiResponse<UOM[]>>(`${this.apiUrl}/uoms/`);
    return this.fetchWithFallback('uoms', req);
  }

  updateUom(id: string, uom: Partial<UOM>): Observable<ApiResponse<UOM>> {
    return this.http.patch<ApiResponse<UOM>>(`${this.apiUrl}/uoms/${id}`, uom).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  createUom(uom: Partial<UOM>): Observable<ApiResponse<UOM>> {
    return this.http.post<ApiResponse<UOM>>(`${this.apiUrl}/uoms/`, uom).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  deleteUom(id: string): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`${this.apiUrl}/uoms/${id}`).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  // --- CATEGORIES ---
  getCategories(): Observable<ApiResponse<Category[]>> {
    const req = this.http.get<ApiResponse<Category[]>>(`${this.apiUrl}/categories/`, { headers: { 'X-Silent-Error': 'true' } });
    return this.fetchWithFallback('categories', req);
  }

  createCategory(category: Partial<Category>): Observable<ApiResponse<Category>> {
    return this.http.post<ApiResponse<Category>>(`${this.apiUrl}/categories/`, category).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  updateCategory(id: string, category: Partial<Category>): Observable<ApiResponse<Category>> {
    return this.http.patch<ApiResponse<Category>>(`${this.apiUrl}/categories/${id}`, category).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  deleteCategory(id: string): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`${this.apiUrl}/categories/${id}`).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  // --- BRANDS ---
  getBrands(): Observable<ApiResponse<Brand[]>> {
    const req = this.http.get<ApiResponse<Brand[]>>(`${this.apiUrl}/brands/`, { headers: { 'X-Silent-Error': 'true' } });
    return this.fetchWithFallback('brands', req);
  }

  createBrand(brand: Partial<Brand>): Observable<ApiResponse<Brand>> {
    return this.http.post<ApiResponse<Brand>>(`${this.apiUrl}/brands/`, brand).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  updateBrand(id: string, brand: Partial<Brand>): Observable<ApiResponse<Brand>> {
    return this.http.patch<ApiResponse<Brand>>(`${this.apiUrl}/brands/${id}`, brand).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  deleteBrand(id: string): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`${this.apiUrl}/brands/${id}`).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  // --- WAREHOUSES ---
  getWarehouses(): Observable<ApiResponse<Warehouse[]>> {
    const req = this.http.get<ApiResponse<Warehouse[]>>(`${this.apiUrl}/warehouses/`);
    return this.fetchWithFallback('warehouses', req);
  }

  createWarehouse(warehouse: Partial<Warehouse>): Observable<ApiResponse<Warehouse>> {
    return this.http.post<ApiResponse<Warehouse>>(`${this.apiUrl}/warehouses/`, warehouse).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  updateWarehouse(id: string, warehouse: Partial<Warehouse>): Observable<ApiResponse<Warehouse>> {
    return this.http.patch<ApiResponse<Warehouse>>(`${this.apiUrl}/warehouses/${id}`, warehouse).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  deleteWarehouse(id: string): Observable<ApiResponse<boolean>> {
    return this.http.delete<ApiResponse<boolean>>(`${this.apiUrl}/warehouses/${id}`).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  getPartners(): Observable<ApiResponse<Partner[]>> {
    const req = this.http.get<ApiResponse<Partner[]>>(`${this.apiUrl}/partners/`);
    return this.fetchWithFallback('partners', req);
  }

  createPartner(partner: Partial<Partner>): Observable<ApiResponse<Partner>> {
    return this.http.post<ApiResponse<Partner>>(`${this.apiUrl}/partners/`, partner).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  updatePartner(id: string, partner: Partial<Partner>): Observable<ApiResponse<Partner>> {
    return this.http.patch<ApiResponse<Partner>>(`${this.apiUrl}/partners/${id}`, partner).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  deletePartner(id: string): Observable<ApiResponse<boolean>> {
    return this.http.delete<ApiResponse<boolean>>(`${this.apiUrl}/partners/${id}`).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  // --- CONCEPTS ---
  getConcepts(): Observable<ApiResponse<Concept[]>> {
    const req = this.http.get<ApiResponse<Concept[]>>(`${this.apiUrl}/concepts/`);
    return this.fetchWithFallback('concepts', req);
  }

  createConcept(concept: Partial<Concept>): Observable<ApiResponse<Concept>> {
    return this.http.post<ApiResponse<Concept>>(`${this.apiUrl}/concepts/`, concept).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  updateConcept(id: string, concept: Partial<Concept>): Observable<ApiResponse<Concept>> {
    return this.http.patch<ApiResponse<Concept>>(`${this.apiUrl}/concepts/${id}`, concept).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }

  deleteConcept(id: string): Observable<ApiResponse<boolean>> {
    return this.http.delete<ApiResponse<boolean>>(`${this.apiUrl}/concepts/${id}`).pipe(
      tap(() => this.health.reportSuccess('masterData')),
      catchError(this.handleError)
    );
  }


  // --- PRICING (Phase 33.5) ---
  getPrices(productId: string, warehouseId?: string | null, currency: string = 'USD', unitType: string = 'BASE'): Observable<ApiResponse<ProductPrice[]>> {
    let url = `${this.apiUrl}/prices/products/${productId}/prices?currency=${currency}&unit_type=${unitType}`;
    if (warehouseId) url += `&warehouse_id=${warehouseId}`;
    
    return this.http.get<ApiResponse<ProductPrice[]>>(url).pipe(
      catchError(this.handleError)
    );
  }

  upsertPrice(payload: Partial<ProductPrice>): Observable<ApiResponse<ProductPrice>> {
    // Specific upsert endpoint for a product
    return this.http.post<ApiResponse<ProductPrice>>(`${this.apiUrl}/prices/products/${payload.product_id}/prices`, payload).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Industrial Secure Download Bridge
   * Bypasses Chrome Blob naming restrictions by using one-time session tickets.
   */
  downloadPriceTemplate(entityId?: string): void {
    const ticketUrl = `${this.apiUrl}/prices/export/ticket`;
    const body = entityId ? { entity_id: entityId } : {};

    this.http.post<ApiResponse<{ticket: string, export_url: string}>>(ticketUrl, body).subscribe({
      next: (response) => {
        if (response.status === 'success' && response.data) {
          const nativeUrl = `${this.apiUrl.replace('/api/v1', '')}${response.data.export_url}`;
          console.log(`[MasterData] Fetching secure payload: ${response.data.ticket}`);
          
          // Download blob silently and force the name via Angular DOM manipulation
          this.http.get(nativeUrl, { responseType: 'blob' }).subscribe({
             next: (blob) => {
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                // HARD FORCE absolute naming to prevent browser UUID fallback
                a.download = entityId ? `Lista_Precios_${entityId.substring(0,6)}.csv` : 'Plantilla_General_Industrial.csv';
                
                document.body.appendChild(a);
                a.click();
                
                setTimeout(() => {
                  document.body.removeChild(a);
                  window.URL.revokeObjectURL(downloadUrl);
                }, 100);
             },
             error: (e) => console.error('[MasterDataService] Error downloading secure blob:', e)
          });
        }
      },
      error: (err) => {
        console.error('[MasterDataService] Failed to generate download ticket:', err);
        this.health.reportFailure('masterData');
      }
    });
  }

  importPrices(file: File): Observable<ApiResponse<{procesados: number, errores: any[]}>> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<ApiResponse<{procesados: number, errores: any[]}>>(`${this.apiUrl}/prices/import`, formData).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: HttpErrorResponse) {
    if (error.status === 409) {
      return throwError(() => new Error('COLLISION_ERROR: Los datos fueron modificados por otro proceso. Por favor, actualice la página.'));
    }
    return throwError(() => error);
  }
}
