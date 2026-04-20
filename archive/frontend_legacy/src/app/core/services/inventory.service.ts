import { Injectable, signal, inject, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom, forkJoin, Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '@env/environment';
import { AuthService } from './auth.service';
import { ApiSimulationService } from './api-simulation.service';
import { InventoryItemDto, CreateInventoryItemCommand, AdjustStockCommand, Warehouse, ProductCategory, Partnership, Concept, CreateDocumentCommand, InventoryDocument, ApiResponse } from '@models/api.types';

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  private auth = inject(AuthService);
  private http = inject(HttpClient);

  private apiUrl = `${environment.inventoryUrl}`;
  private mdUrl = `${environment.masterDataUrl}`;

  // State Signals
  items = signal<InventoryItemDto[]>([]);
  documents = signal<InventoryDocument[]>([]);
  currentDocument = signal<InventoryDocument | null>(null);
  warehouses = signal<Warehouse[]>([]);
  physicalWarehouses = computed(() => this.warehouses().filter(w => w.type === 'PHYSICAL' || w.type === 'GENERAL'));
  transitWarehouses = computed(() => this.warehouses().filter(w => w.type === 'TRANSIT'));
  warehouseTypes = signal<any[]>([]);
  warehouseGroups = signal<any[]>([]);
  categories = signal<ProductCategory[]>([]);
  partnerships = signal<Partnership[]>([]);
  concepts = signal<Concept[]>([]);
  loading = signal<boolean>(false);
  folioPreview = signal<string>('');
  inventoryReadiness = signal<any | null>(null);

  // Get current company ID from AuthService for multitenancy
  public activeCompanyId = computed(() => this.auth.activeCompanyId());

  async loadItems() {
    this.loading.set(true);
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) {
      console.error('No se pudo cargar el inventario: ID de compañía no encontrado.');
      this.loading.set(false);
      return;
    }
    try {
      // Use the real dashboard stock endpoint
      const res = await lastValueFrom(this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/dashboard/stock`));
      
      // Map to InventoryItemDto if needed, or assume data matches
      // StockDashboardRow: product_id, sku, name, quantity, reserved, available, uom
      const mappedItems: InventoryItemDto[] = res.data.map(row => ({
        id: row.product_id,
        companyId: currentCompanyId,
        productId: row.product_id,
        sku: row.sku,
        name: row.name,
        description: '',
        price: { amount: 0, currency: 'USD' },
        stockQuantity: parseFloat(row.quantity),
        reservedQuantity: parseFloat(row.reserved),
        warehouseId: '',
        warehouseName: '',
        location: '',
        categoryId: '',
        categoryName: '',
        isActive: true
      }));
      this.items.set(mappedItems);
    } catch (error) {
      console.error("Failed to load inventory items", error);
    } finally {
      this.loading.set(false);
    }
  }

  // REPARACIÓN: Método que pide inventory-documents-list.component.ts
  async loadDocuments() {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return;
    try {
      const res = await lastValueFrom(this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/dashboard/movements`));
      
      // Map MovementDocumentRow to InventoryDocument list structure
      const mappedDocs: any[] = res.data.map(row => ({
        id: row.id,
        folio: row.folio,
        deliveryDate: row.date,
        conceptName: row.type,
        origin_name: row.origin,
        destination_name: row.destination,
        total_items: row.items_count,
        status: row.status as any,
        total_weight: row.total_weight
      }));
      this.documents.set(mappedDocs);
    } catch (error) {
      console.error("Error loading documents", error);
    }
  }

  async checkReadiness() {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return;
    try {
      const res = await lastValueFrom(this.http.get<ApiResponse<any>>(`${this.apiUrl}/readiness`));
      if (res.status === 'success') {
        this.inventoryReadiness.set(res.data);
      }
    } catch (error) {
      console.error("Error checking inventory readiness", error);
    }
  }

  async loadDocument(id: string) {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return;
    try {
      const res = await lastValueFrom(this.http.get<ApiResponse<any>>(`${this.apiUrl}/api/v1/inventory/vdetail/${id}`));
      
      // DocumentDetailEntity -> InventoryDocument mapping
      const doc = res.data;
      const mappedDoc: InventoryDocument = {
        id: doc.id,
        folio: doc.folio,
        sequence_number: 0,
        deliveryDate: doc.date,
        conceptId: doc.concept_id || '',
        conceptName: doc.type,
        conceptType: doc.type as any,
        warehouseId: doc.warehouse_id || '',
        warehouseName: doc.origin || '',
        reference: '',
        description: doc.notes || '',
        total_amount: 0,
        status: doc.status as any,
        movements: doc.items || []
      };
      this.currentDocument.set(mappedDoc);
    } catch (error) {
      console.error("Error loading document", error);
    }
  }

  // REPARACIÓN: Método que pide warehouse-list.component.ts
  async loadWarehouseCatalogs() {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return;

    try {
      const fallback = () => of({ status: 'error', data: [] as any });
      const [typesRes, groupsRes] = await lastValueFrom(
        forkJoin([
          this.http.get<ApiResponse<any[]>>(`${this.mdUrl}/warehouses/types`).pipe(catchError(fallback)),
          this.http.get<ApiResponse<any[]>>(`${this.mdUrl}/warehouses/groups`).pipe(catchError(fallback))
        ])
      );

      if (typesRes.status === 'success') this.warehouseTypes.set(typesRes.data);
      if (groupsRes.status === 'success') this.warehouseGroups.set(groupsRes.data);
    } catch (error) {
      console.error("Failed to load warehouse catalogs", error);
    }
  }

  async loadFolioPreview(conceptId: string) {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId || !conceptId) return;
    try {
      const res = await lastValueFrom(this.http.get<ApiResponse<{ nextFolio: string }>>(`${this.apiUrl}/api/v1/inventory/folio-preview/${conceptId}`));
      this.folioPreview.set(res.data.nextFolio);
    } catch (error) {
      console.error("Error loading folio preview", error);
    }
  }

  async loadCatalogs() {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return;

    try {
      const fallback = () => of({ status: 'error', data: [] as any });
      const [whRes, catRes, conceptRes] = await lastValueFrom(
        forkJoin([
          this.http.get<ApiResponse<Warehouse[]>>(`${this.mdUrl}/warehouses`).pipe(catchError(fallback)),
          this.http.get<ApiResponse<ProductCategory[]>>(`${this.mdUrl}/categories`).pipe(catchError(fallback)),
          this.http.get<ApiResponse<Concept[]>>(`${this.mdUrl}/concepts`).pipe(catchError(fallback))
        ])
      );

      if (whRes.status === 'success') this.warehouses.set(whRes.data);
      if (catRes.status === 'success') this.categories.set(catRes.data);
      if (conceptRes.status === 'success') this.concepts.set(conceptRes.data);
      
      // Partnerships remain hardcoded or handled separately if no endpoint exists
      this.partnerships.set([
        { id: '1', code: 'PROV-001', name: 'Distribuidora Central', type: 2, status: 'Gold' as any }
      ]);
    } catch (error) {
      console.error("Failed to load catalogs", error);
    }
  }

  async createItem(cmd: CreateInventoryItemCommand): Promise<boolean> {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return false;

    try {
      await lastValueFrom(this.http.post(`${this.mdUrl}/products/`, {
        name: cmd.name,
        sku: cmd.sku,
        description: cmd.description,
        product_type: 'RAW_MATERIAL', // Default for now
        uom_id: '1a7444c9-40df-51d5-833b-501fc84b67bb' // Safety PZA
      }));
      await this.loadItems();
      return true;
    } catch (error) {
      return false;
    }
  }

  async adjustStock(cmd: AdjustStockCommand): Promise<boolean> {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return false;

    try {
      // Use transactions endpoint for adjustments
      await lastValueFrom(this.http.post(`${this.apiUrl}/api/v1/inventory/transactions`, {
        product_id: cmd.itemId, // Assuming itemId is actually productId in the backend link
        uom_id: '1a7444c9-40df-51d5-833b-501fc84b67bb',
        warehouse_id: '1a7444c9-40df-51d5-833b-501fc84b67bb', // Placeholder, should be the item's warehouse
        transaction_type: 'ADJUSTMENT',
        concept_id: 'eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e', // Adjustment concept
        quantity_change: cmd.quantityChange,
        comments: cmd.reason
      }));
      await this.loadItems();
      return true;
    } catch (error) {
      return false;
    }
  }

  async createDocument(cmd: CreateDocumentCommand): Promise<boolean> {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return false;

    try {
      await lastValueFrom(this.http.post(`${this.apiUrl}/api/v1/inventory/documents`, {
        warehouse_id: cmd.warehouseId,
        type: 'ENTRY', // Or derived from concept
        concept_id: cmd.conceptId,
        notes: cmd.description,
        correlation_id: uuid.v4(),
        items: cmd.movements.map(m => ({
          product_id: m.productId,
          quantity: m.quantity,
          unit_price: m.unitPrice,
          uom_id: '1a7444c9-40df-51d5-833b-501fc84b67bb'
        }))
      }));
      return true;
    } catch (error) {
      return false;
    }
  }

  searchItems(query: string, warehouseId?: string): Observable<ApiResponse<any[]>> {
    let url = `${this.apiUrl}/search/variants?q=${query}`;
    if (warehouseId) {
      url = `${this.apiUrl}/search/products/search?q=${query}&warehouse_id=${warehouseId}`;
    }
    return this.http.get<ApiResponse<any[]>>(url, {
      headers: { 'X-Company-ID': this.activeCompanyId() || '' }
    });
  }
}