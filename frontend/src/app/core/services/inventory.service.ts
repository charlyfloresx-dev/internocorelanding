import { Injectable, signal, inject, computed } from '@angular/core';
import { lastValueFrom } from 'rxjs';
import { AuthService } from './auth.service';
import { ApiSimulationService } from './api-simulation.service';
import { InventoryItemDto, CreateInventoryItemCommand, AdjustStockCommand, Warehouse, ProductCategory, Partnership, Concept, CreateDocumentCommand } from '@models/api.types';

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  private auth = inject(AuthService);
  private api = inject(ApiSimulationService);

  // State Signals
  items = signal<InventoryItemDto[]>([]);
  documents = signal<any[]>([]);
  warehouses = signal<Warehouse[]>([]);
  warehouseTypes = signal<any[]>([]);
  warehouseGroups = signal<any[]>([]);
  categories = signal<ProductCategory[]>([]);
  partnerships = signal<Partnership[]>([]);
  concepts = signal<Concept[]>([]);
  loading = signal<boolean>(false);

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
      // Pass companyId to ensure multitenancy
      const res = await lastValueFrom(this.api.getInventoryItems(currentCompanyId));
      this.items.set(res.data);
    } catch (error) {
      // Error is handled by the global apiInterceptor
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
      const res = await lastValueFrom(this.api.getDocuments(currentCompanyId));
      this.documents.set(res.data);
    } catch (error) {
      console.error("Error loading documents", error);
    }
  }

  // REPARACIÓN: Método que pide warehouse-list.component.ts
  async loadWarehouseCatalogs() {
    // Por ahora vacío para que compile el componente
    console.log('Cargando catálogos de almacén...');
  }

  async loadCatalogs() {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return;

    try {
        const [whRes, catRes, partnerRes, conceptRes] = await Promise.all([
            lastValueFrom(this.api.getWarehouses(currentCompanyId)),
            lastValueFrom(this.api.getProductCategories()),
            lastValueFrom(this.api.getPartnerships()),
            lastValueFrom(this.api.getConcepts())
        ]);

        this.warehouses.set(whRes.data);
        this.categories.set(catRes.data);
        this.partnerships.set(partnerRes.data);
        this.concepts.set(conceptRes.data);
    } catch(error) {
        console.error("Failed to load catalogs", error);
    }
  }

  async createItem(cmd: CreateInventoryItemCommand): Promise<boolean> {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return false;
    
    try {
      const res = await lastValueFrom(this.api.createInventoryItem(currentCompanyId, cmd));
      this.items.update(current => [...current, res.data]);
      return true;
    } catch (error) {
      return false;
    }
  }

  async adjustStock(cmd: AdjustStockCommand): Promise<boolean> {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return false;

    try {
      await lastValueFrom(this.api.adjustStock(currentCompanyId, cmd));
      this.items.update(items => items.map(item => 
        item.id === cmd.itemId 
          ? { ...item, stockQuantity: item.stockQuantity + cmd.quantityChange }
          : item
      ));
      return true;
    } catch (error) {
      return false;
    }
  }

  async createDocument(cmd: CreateDocumentCommand): Promise<boolean> {
    const currentCompanyId = this.activeCompanyId();
    if (!currentCompanyId) return false;

    try {
      await lastValueFrom(this.api.createDocument(currentCompanyId, cmd));
      return true;
    } catch (error) {
      return false;
    }
  }
}