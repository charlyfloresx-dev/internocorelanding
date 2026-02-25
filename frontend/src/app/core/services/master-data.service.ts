import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { SystemHealthService } from './system-health.service';
import { ApiResponse, ProductRead, ProductReadWithVersions, UOMRead, CategoryRead, BrandRead } from '../models/master-data.types';
import { map, Observable, finalize, catchError, of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class MasterDataService {
  private http = inject(HttpClient);
  private apiUrl = environment.masterDataUrl;
  private health = inject(SystemHealthService);

  // Signal para estado de carga (UX)
  loading = signal<boolean>(false);

  /**
   * Obtiene la lista de productos.
   * El interceptor se encarga de inyectar el X-Company-Id.
   */
  getProducts(): Observable<ProductRead[]> {
    this.loading.set(true);
    return this.http.get<ApiResponse<ProductRead[]>>(`${this.apiUrl}/products/`).pipe(
      map(response => {
        this.health.updateStatus('masterData', true);
        const data = response.data || [];
        localStorage.setItem('interno_cache_products', JSON.stringify(data));
        return data;
      }),
      catchError(err => {
        this.health.updateStatus('masterData', false);
        console.warn('[MasterDataService] ⚠️ API Error (Products). Serving from cache.', err);
        const cached = localStorage.getItem('interno_cache_products');
        return of(cached ? JSON.parse(cached) : []);
      }),
      finalize(() => this.loading.set(false))
    );
  }

  /**
   * Obtiene el detalle de un producto con sus versiones.
   */
  getProductById(id: string): Observable<ProductReadWithVersions> {
    this.loading.set(true);
    return this.http.get<ApiResponse<ProductReadWithVersions>>(`${this.apiUrl}/products/${id}`).pipe(
      map(response => {
        if (!response.data) throw new Error('Product not found');
        return response.data;
      }),
      finalize(() => this.loading.set(false))
    );
  }

  /**
   * Obtiene la lista de Unidades de Medida.
   * RUTA OPENAPI: /api/v1/ums/ (No confundir con /uoms/)
   */
  getUOMs(): Observable<UOMRead[]> {
    this.loading.set(true);
    // CORRECCIÓN: Uso estricto de /ums/ según Swagger
    return this.http.get<ApiResponse<UOMRead[]>>(`${this.apiUrl}/ums/`).pipe(
      map(response => {
        this.health.updateStatus('masterData', true);
        const data = response.data || [];
        localStorage.setItem('interno_cache_uoms', JSON.stringify(data));
        return data;
      }),
      catchError(err => {
        this.health.updateStatus('masterData', false);
        console.warn('[MasterDataService] ⚠️ API Error (UOMs). Serving from cache.', err);
        const cached = localStorage.getItem('interno_cache_uoms');
        return of(cached ? JSON.parse(cached) : []);
      }),
      finalize(() => this.loading.set(false))
    );
  }

  /**
   * Obtiene la lista de Categorías.
   * RUTA OPENAPI: /api/v1/categories/
   */
  getCategories(): Observable<CategoryRead[]> {
    this.loading.set(true);
    return this.http.get<ApiResponse<CategoryRead[]>>(`${this.apiUrl}/categories/`).pipe(
      map(response => {
        this.health.updateStatus('masterData', true);
        const data = response.data || [];
        localStorage.setItem('interno_cache_categories', JSON.stringify(data));
        return data;
      }),
      catchError(err => {
        this.health.updateStatus('masterData', false);
        console.warn('[MasterDataService] ⚠️ API Error (Categories). Serving from cache.', err);
        const cached = localStorage.getItem('interno_cache_categories');
        return of(cached ? JSON.parse(cached) : []);
      }),
      finalize(() => this.loading.set(false))
    );
  }

  /**
   * Obtiene la lista de Marcas.
   * RUTA OPENAPI: /api/v1/brands/
   */
  getBrands(): Observable<BrandRead[]> {
    this.loading.set(true);
    return this.http.get<ApiResponse<BrandRead[]>>(`${this.apiUrl}/brands/`).pipe(
      map(response => {
        this.health.updateStatus('masterData', true);
        const data = response.data || [];
        localStorage.setItem('interno_cache_brands', JSON.stringify(data));
        return data;
      }),
      catchError(err => {
        this.health.updateStatus('masterData', false);
        console.warn('[MasterDataService] ⚠️ API Error (Brands). Serving from cache.', err);
        const cached = localStorage.getItem('interno_cache_brands');
        return of(cached ? JSON.parse(cached) : []);
      }),
      finalize(() => this.loading.set(false))
    );
  }
}