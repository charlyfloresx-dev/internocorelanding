// temp_future/src/app/core/services/inventory.service.ts
import { Injectable, signal, inject, computed, effect } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom, of, throwError, Observable } from 'rxjs';
import { tap, catchError, map } from 'rxjs/operators';
import { MasterDataService } from './master-data.service';
import { SystemHealthService } from './system-health.service';
import { AuthService } from './auth.service';

import { environment } from '../../../environments/environment';
import { 
  InventoryItem, 
  InventoryDocument, 
  UOMRead, 
  CategoryRead, 
  BrandRead,
  ProductRead,
  ApiResponse
} from '../models/domain.types';

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  private http = inject(HttpClient);
  private masterData = inject(MasterDataService);
  private health = inject(SystemHealthService);
  private auth = inject(AuthService);
  private apiUrl = environment.inventoryUrl;


  // === Signals (Reflective state from MasterData) ===
  public items = signal<InventoryItem[]>([]);
  public warehouses = this.masterData.warehouses;
  public concepts = this.masterData.concepts;
  public uoms = this.masterData.uoms as any;
  public categories = this.masterData.categories as any;
  public brands = this.masterData.brands as any;
  public loading = this.masterData.loading;

  // === Concept Resolution (delegates — single injection point for components) ===
  /** true once concepts are loaded for the active tenant. Use as submit guard. */
  public readonly catalogsLoaded = this.masterData.catalogsLoaded;
  /** 'LOADING' | 'READY' | 'ERROR' — drive defensive UI states. */
  public readonly conceptCatalogState = this.masterData.conceptCatalogState;
  /** Signal-safe concept lookup by deterministic code (e.g. 'INT-TRA'). */
  resolveConceptByCode = (code: string) => this.masterData.resolveConceptByCode(code);

  public selectedWarehouseId = signal<string | null>(null);
  public movementsCache = signal<any[] | null>(null);

  private lastLoadedCompanyId: string | null = null;
  private loadPromise: Promise<void> | null = null;

  constructor() {}


  /**
   * Loads all master data for the inventory module.
   * Industrial Guard: Only loads once per company change unless forced.
   */
  async loadCatalogs(force: boolean = false) {
    // Delegation to MasterDataService for industrial state consistency
    await this.masterData.refreshCatalogs();
  }


  /** Reload only warehouses — useful for retry after session is established. */
  async reloadWarehouses(): Promise<any[]> {
    await this.masterData.refreshCatalogs();
    return this.warehouses();
  }


  private async safeGet<T>(url: string, fallback: T): Promise<T> {
    try {
      const res = await lastValueFrom(
        this.http.get<ApiResponse<T>>(url, { headers: { 'X-Silent-Error': 'true' } })
      );
      if (res?.status === 'success' && res?.data != null) {
        return res.data;
      }
      return fallback;
    } catch (e: any) {
      console.error(`[safeGet] FAILED ${url} → status=${e?.status} msg=${e?.error?.message || e?.message}`);
      return fallback;
    }
  }

  /**
   * POST a new inventory document to the ledger.

   * On success, purges specific browser memory to prevent stale state.
   */
  async createDocument(doc: Partial<InventoryDocument>, clientRequestId: string): Promise<InventoryDocument> {
    this.loading.set(true);
    try {
      const response = await lastValueFrom(
        this.http.post<ApiResponse<any>>(`${this.apiUrl}/inventory/documents`, doc, {
          headers: { 'X-Client-Request-ID': clientRequestId }
        })
      );
      
      // Memory Management: Clear residual form data and movements cache
      this.clearConfirmationCache();
      this.movementsCache.set(null); 
      
      return response.data; // Return the inner data (with generated id)
    } finally {
      this.loading.set(false);
    }
  }

  async getDocument(id: string): Promise<any> {
    this.loading.set(true);
    try {
      const response = await lastValueFrom(
        this.http.get<ApiResponse<any>>(`${this.apiUrl}/inventory/vdetail/${id}`)
      );
      return response.data;
    } finally {
      this.loading.set(false);
    }
  }

  private clearConfirmationCache() {
    // Specifically clear inventory-related pending data
    const keysToRemove = Object.keys(sessionStorage).filter(k => k.startsWith('inventory_draft_'));
    keysToRemove.forEach(k => sessionStorage.removeItem(k));
    console.log('[Memory] Inventory confirmation cache purged.');
  }

  async getProductBySku(sku: string): Promise<any> {
    const res = await lastValueFrom(
      this.http.get<ApiResponse<any>>(`${this.apiUrl}/search/products/search`, { 
        params: { q: sku } 
      })
    );
    return res.data && res.data.length > 0 ? res.data[0] : null;
  }

  async searchProducts(query: string, warehouseId?: string): Promise<any[]> {
    const params: any = { q: query };
    if (warehouseId) params.warehouse_id = warehouseId;
    const res = await lastValueFrom(
      this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/search/products/search`, { 
        params
      })
    );
    return res.data;
  }
  async getStock(warehouseId: string, productId: string): Promise<any> {
    const res = await lastValueFrom(
      this.http.get<any>(`${this.apiUrl}/inventory/levels/${productId}/${warehouseId}`)
    );
    // The backend endpoint might return raw data instead of an ApiResponse object
    return res.data !== undefined ? res.data : res;
  }

  async getDashboardSummary(): Promise<any> {
    const url = `${this.apiUrl}/dashboard/summary`;
    return this.fetchWithFallback('dashboard_summary', url);
  }

  async getMissionControl(warehouse_id: string): Promise<any> {
    const url = `${this.apiUrl}/dashboard/mission-control?warehouse_id=${warehouse_id}`;
    return this.fetchWithFallback(`mission_control_${warehouse_id}`, url);
  }

  async getConsolidatedMissionControl(): Promise<any[]> {
    const url = `${this.apiUrl}/dashboard/consolidated`;
    return this.fetchWithFallback<any[]>(`mission_control_consolidated`, url);
  }

  /**
   * Local Helper for Industrial Fallback
   */
  private async fetchWithFallback<T>(cacheKey: string, url: string): Promise<T> {
    try {
      const res = await lastValueFrom(this.http.get<ApiResponse<T>>(url));
      if (res.status === 'success') {
        localStorage.setItem(`ic_inv_cache_${cacheKey}`, JSON.stringify(res.data));
        this.health.reportSuccess('inventory');
        return res.data;
      }
      throw new Error(res.message);
    } catch (err) {
      this.health.reportFailure('inventory');
      const cached = localStorage.getItem(`ic_inv_cache_${cacheKey}`);
      if (cached) {
        console.warn(`[InventoryService] ⚠️ Fallback to cache for ${cacheKey}`);
        return JSON.parse(cached);
      }
      throw err;
    }
  }


  async getMovements(limit: number = 5, warehouseId?: string, force: boolean = false): Promise<any[]> {
    if (!force && this.movementsCache() && !warehouseId) {
       console.log('[InventoryService] 🧠 Serving movements from memory cache.');
       return this.movementsCache()!.slice(0, limit);
    }

    const params: any = { limit: limit.toString() };
    if (warehouseId) params.warehouse_id = warehouseId;

    const res = await lastValueFrom(
      this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/dashboard/movements`, {
        params
      })
    );
    
    // Cache the list if it's the general one
    if (!warehouseId && res.status === 'success') {
      this.movementsCache.set(res.data);
    }

    return res.data;
  }

  async getSummary(warehouseId?: string): Promise<any> {
    const params: any = {};
    if (warehouseId) params.warehouse_id = warehouseId;
    const res = await lastValueFrom(
      this.http.get<ApiResponse<any>>(`${this.apiUrl}/dashboard/summary`, { params })
    );
    return res.data;
  }

  async resetDemoData(): Promise<any> {
    try {
      const res = await lastValueFrom(
        this.http.post<ApiResponse<any>>(`${this.apiUrl}/admin/demo-reset`, {})
      );
      return res;
    } catch (e: any) {
      // Don't let this propagate to the error interceptor
      console.warn('[Demo] demo-reset request error:', e?.status, e?.error?.message);
      throw e;
    }
  }

  async verifyDemoDataFreshness(companyId: string) {
    const DEMO_CO_ID = 'ad6cc8a6-34f9-42df-8f29-28254e0ad242';
    if (!companyId || companyId !== DEMO_CO_ID) return;

    const lastSeed = localStorage.getItem('demo_last_seed');
    const today = new Date().toISOString().split('T')[0];
    
    if (lastSeed === today) {
      console.log('[Demo] Datos de hoy ya confirmados, omitiendo seed.');
      return;
    }

    console.log('[Demo] Iniciando auto-seed diario...');
    try {
      await this.resetDemoData();
      localStorage.setItem('demo_last_seed', today);
      console.log('[Demo] Auto-seed completado con éxito.');
    } catch (e: any) {
      // If 403, the backend rejected - update localStorage to avoid retrying in loop
      if (e?.status === 403) {
        console.warn('[Demo] Permiso denegado en demo-reset (403). Revisa que el rol sea admin.');
      } else {
        console.warn('[Demo] Fallo el auto-seed, se usaran datos residuales.', e?.status);
      }
    }
  }

  async getReadiness(): Promise<any> {
    const res = await lastValueFrom(
      this.http.get<ApiResponse<any>>(`${this.apiUrl}/readiness`)
    );
    return res.data;
  }

  // === Inter-Company Transfer (ICT) Lifecycle ===
  
  /** [Company B] Get transfers shipped to us but not yet received. */
  async getPendingInboundTransfers(): Promise<any[]> {
    const res = await lastValueFrom(
      this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/inventory/transfers/inter-company/inbound/pending`)
    );
    return res.data;
  }

  /** [Both] Get details of a specific inter-company transfer by ID. */
  async getTransferDetail(transferId: string): Promise<any> {
    const res = await lastValueFrom(
      this.http.get<ApiResponse<any>>(`${this.apiUrl}/inventory/transfers/inter-company/${transferId}`)
    );
    return res.data;
  }

  /** [Scanner/Handheld] Look up a transfer by its human-readable folio number. */
  async getTransferByFolio(folio: string): Promise<any> {
    const res = await lastValueFrom(
      this.http.get<ApiResponse<any>>(`${this.apiUrl}/inventory/transfers/inter-company/by-folio/${folio}`)
    );
    return res.data;
  }

  /**
   * [Company B] Confirm receipt of stock from a transfer with optional damage reporting.
   * concept_id defaults to PUR-REC for standard receipts or INT-TRA for inter-company.
   * The backend will use concept_id to categorize the inbound movement in the Kardex.
   */
  async receiveTransfer(
    transferId: string,
    receivedQty?: number,
    damagedQty: number = 0,
    notes?: string,
    conceptId?: string   // Optional: resolved upstream by the component
  ): Promise<any> {
    const body: any = {
      received_quantity: receivedQty,
      damaged_quantity: damagedQty,
      notes: notes
    };
    // Only inject concept_id if provided — backend has its own fallback for receipt
    if (conceptId) body.concept_id = conceptId;

    const res = await lastValueFrom(
      this.http.post<ApiResponse<any>>(`${this.apiUrl}/inventory/transfers/inter-company/${transferId}/receive`, body)
    );
    return res.data;
  }

  /** [WMS] Direct inventory receipt (Blind Receipt) without a prior document. */
  async receiveDirect(payload: any): Promise<any> {
    const res = await lastValueFrom(
      this.http.post<ApiResponse<any>>(`${this.apiUrl}/inventory/direct-receipt`, payload)
    );
    return res.data;
  }

  /** [Company A] Reclaim stock from an orphan/abandoned transfer. */
  async revertTransfer(transferId: string, reason: string): Promise<any> {
    const body = { reason };
    const res = await lastValueFrom(
      this.http.post<ApiResponse<any>>(`${this.apiUrl}/inventory/transfers/inter-company/${transferId}/revert`, body)
    );
    return res.data;
  }

  // ─── Typed Payload Interfaces (Inline — co-located with methods) ────────────

  /**
   * [Company A] Push a new inter-company transfer out.
   * concept_id MUST be provided. Use resolveConceptByCode('INT-TRA') in the component.
   * If concept_id is null, the component should block the submit.
   */
  async initiateInterCompanyTransfer(payload: {
    from_warehouse_id: string;
    to_warehouse_id: string;       // Destination warehouse (other company)
    product_id: string;
    quantity: number;
    uom_id: string;
    unit_price?: number;
    currency?: string;
    concept_id: string;            // REQUIRED — e.g. 'INT-TRA' UUID
    notes?: string;
    customs_pedimento?: string;    // Anexo 24: Pedimento number
    exchange_rate_dof?: number;    // Binational: DOF exchange rate
    [key: string]: any;            // Allow extra fields (compliance metadata)
  }): Promise<any> {
    const res = await lastValueFrom(
      this.http.post<ApiResponse<any>>(`${this.apiUrl}/inventory/transfers/inter-company/initiate`, payload, {
        headers: { 'X-Silent-Error': 'true' }
      })
    );
    return res.data;
  }

  /**
   * [Internal] Dispatch a standard transfer between warehouses of the same company.
   * concept_id is required for backend traceability — defaults to INT-TRA if not specified.
   */
  async dispatchInternalTransfer(payload: {
    origin_warehouse_id: string;
    destination_warehouse_id: string;
    product_id: string;
    quantity: number;
    uom_id: string;
    concept_id: string;            // REQUIRED — resolved via resolveConceptByCode
    notes?: string;
    [key: string]: any;
  }): Promise<any> {
    const body = {
      from_warehouse_id: payload.origin_warehouse_id,
      to_warehouse_id: payload.destination_warehouse_id,
      product_id: payload.product_id,
      quantity: payload.quantity,
      uom_id: payload.uom_id,
      concept_id: payload.concept_id,  // ← Propagated to backend
      notes: payload.notes
    };
    const res = await lastValueFrom(
      this.http.post<ApiResponse<any>>(`${this.apiUrl}/inventory/transfers/dispatch`, body, {
        headers: { 'X-Silent-Error': 'true' }
      })
    );
    return res.data;
  }

  /** [Anexo 24] Fetch picking suggestion (batches + locations) for a product. */
  async getFifoPreview(productId: string, warehouseId: string): Promise<any[]> {
    const res = await lastValueFrom(
      this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/inventory/fifo-preview/${productId}/${warehouseId}`)
    );
    return res.data || [];
  }

  /**
   * High-Efficiency: Creates an initial inventory entry (opening balance) for a product.
   * Concept is typically 'APERTURA' or 'ENTRADA_INICIAL'.
   */
  async createOpeningBalance(productId: string, warehouseId: string, quantity: number, uomId: string): Promise<any> {
    const openingConcept = this.concepts().find(c => 
      c.code === 'APERTURA' || 
      c.name.toUpperCase().includes('APERTURA') || 
      c.name.toUpperCase().includes('ENTRADA INICIAL')
    );

    if (!openingConcept) {
      throw new Error('Concepto de "APERTURA" no encontrado en el catálogo maestro.');
    }

    const doc: any = {
      warehouse_id: warehouseId,
      concept_id: openingConcept.id,
      document_type: 'RECEIPT', // Opening is an IN
      external_reference: 'ALTA_EXPRESS_WIZARD',
      items: [
        {
          product_id: productId,
          quantity: quantity,
          uom_id: uomId,
          unit_price: 0, // Opening doesn't necessarily set price here if using master price
          notes: 'Apertura inicial vía Wizard'
        }
      ]
    };

    return this.createDocument(doc, `opening-${productId}-${Date.now()}`);
  }

  // === Industrial Variants (Supplier Mappings) ===
  
  /**
   * Retrieves all supplier-specific variants for a master product.
   */
  async getProductVariants(productId: string): Promise<any[]> {
    const res = await lastValueFrom(
      this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/inventory/products/${productId}/variants`)
    );
    return res.data;
  }

  /**
   * Creates or updates a variant mapping.
   */
  async upsertVariant(variant: any): Promise<any> {
    const res = await lastValueFrom(
      this.http.post<ApiResponse<any>>(`${this.apiUrl}/inventory/variants`, variant)
    );
    return res.data;
  }

  /**
   * Removes a variant mapping.
   */
  async deleteVariant(variantId: string): Promise<any> {
    const res = await lastValueFrom(
      this.http.delete<ApiResponse<any>>(`${this.apiUrl}/inventory/variants/${variantId}`)
    );
    return res.data;
  }

  /**
   * [Anexo 24] Global compliance view: Stock levels by Pedimento.
   */
  async getCustomsBalances(warehouseId?: string, limit: number = 50, offset: number = 0, query?: string): Promise<ApiResponse<any[]>> {
    const params: any = { limit: limit.toString(), offset: offset.toString() };
    if (warehouseId) params.warehouse_id = warehouseId;
    if (query) params.q = query;
    
    return lastValueFrom(
      this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/reporting/customs/balances`, { params })
    );
  }

  /**
   * [Phase 42.8] Executes an internal relocation between locations.
   */
  async relocateStock(payload: {
    product_id: string;
    uom_id: string;
    warehouse_id: string;
    quantity: number;
    from_location: string;
    to_location: string;
    notes?: string;
  }): Promise<ApiResponse<any>> {
    return lastValueFrom(
      this.http.post<ApiResponse<any>>(`${this.apiUrl}/inventory/relocate`, payload)
    );
  }

  /**
   * [Industrial Registry] Optimized fetch for all products metadata.
   */
  getQuickCatalog(): Observable<any[]> {
    return this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/search/products/quick-catalog`).pipe(
      map((res: ApiResponse<any[]>) => res.data)
    );
  }

  /**
   * [Phase 49] Density Guard: Checks real-time occupancy and capacity.
   */
  async getLocationDensity(warehouseId: string, locationCode: string): Promise<ApiResponse<any>> {
    return lastValueFrom(
      this.http.get<ApiResponse<any>>(`${this.apiUrl}/inventory/locations/${locationCode}/density`, {
        params: { warehouse_id: warehouseId }
      })
    );
  }

  /**
   * [Phase 49] Exports a detailed stock sheet for physical audit.
   */
  exportAuditCsv(warehouseId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/warehouses/${warehouseId}/audit-export`, {
      responseType: 'blob'
    });
  }

  /**
   * [Phase 49] Submits a cycle count reconciliation for a location.
   */
  async submitCycleCount(warehouseId: string, location: string, items: { product_id: string, sku: string, difference: number, status: string }[]): Promise<any> {
    const payload = {
      location,
      items
    };
    return lastValueFrom(
      this.http.post<ApiResponse<any>>(`${this.apiUrl}/warehouses/${warehouseId}/cycle-count`, payload)
    );
  }
}
