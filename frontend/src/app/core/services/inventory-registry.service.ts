import { Injectable, signal, inject } from '@angular/core';
import { InventoryService } from './inventory.service';
import { firstValueFrom } from 'rxjs';

/**
 * InventoryRegistryService
 * [Performance Layer]
 * Manages an in-memory O(1) map of all SKUs to their metadata.
 * Hydrates upon entering the inventory module to provide zero-latency lookups for industrial handhelds.
 */
@Injectable({ providedIn: 'root' })
export class InventoryRegistryService {
  private invService = inject(InventoryService);
  
  // High-Performance Map for SKU lookups
  private _productsBySku = signal<Map<string, any>>(new Map());
  private _productsById = signal<Map<string, any>>(new Map());
  
  isLoaded = signal(false);
  isLoading = signal(false);

  /**
   * Initializes the registry by fetching the quick catalog from the backend.
   */
  async hydrate() {
    if (this.isLoaded() || this.isLoading()) return;

    console.log('[Registry] ⚡ Hydrating Industrial Catalog Cache...');
    this.isLoading.set(true);
    
    try {
      const products = await firstValueFrom(this.invService.getQuickCatalog()) as any[];
      const skuMap = new Map<string, any>();
      const idMap = new Map<string, any>();
      
      products.forEach((p: any) => {
        skuMap.set(p.sku, p);
        idMap.set(p.id, p);
      });
      
      this._productsBySku.set(skuMap);
      this._productsById.set(idMap);
      this.isLoaded.set(true);
      console.log(`[Registry] ✅ Hydrated ${products.length} SKUs in memory.`);
    } catch (error) {
      console.error('[Registry] ❌ Failed to hydrate catalog:', error);
    } finally {
      this.isLoading.set(false);
    }
  }

  /**
   * Instant search by SKU.
   */
  getProductBySku(sku: string | null) {
    if (!sku) return null;
    return this._productsBySku().get(sku.trim().toUpperCase()) || this._productsBySku().get(sku.trim());
  }

  /**
   * Instant search by Product ID.
   */
  getProductById(id: string | null) {
    if (!id) return null;
    return this._productsById().get(id);
  }

  /**
   * Clears the cache (e.g., on logout).
   */
  clear() {
    this._productsBySku.set(new Map());
    this._productsById.set(new Map());
    this.isLoaded.set(false);
  }
}
