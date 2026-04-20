import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiResponse, BrandRead, CategoryRead, ProductRead, UOMRead } from '../models/catalog.types';

@Injectable({
  providedIn: 'root'
})
export class MasterDataService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:8003/api/v1'; // Puerto del Master Data Service

  /**
   * PRODUCTS
   */
  getProducts(): Observable<ApiResponse<ProductRead[]>> {
    console.log('[MasterData] 📡 Intentando conectar al Backend Python en: ' + this.apiUrl);
    return this.http.get<ApiResponse<ProductRead[]>>(`${this.apiUrl}/products`);
  }

  /**
   * UNITS OF MEASURE (UOM)
   */
  getUoms(): Observable<ApiResponse<UOMRead[]>> {
    console.log('[MasterData] 📡 Intentando conectar al Backend Python en: ' + this.apiUrl);
    return this.http.get<ApiResponse<UOMRead[]>>(`${this.apiUrl}/ums`);
  }

  /**
   * CATEGORIES
   */
  getCategories(): Observable<ApiResponse<CategoryRead[]>> {
    console.log('[MasterData] 📡 Intentando conectar al Backend Python en: ' + this.apiUrl);
    return this.http.get<ApiResponse<CategoryRead[]>>(`${this.apiUrl}/categories`);
  }

  /**
   * BRANDS
   */
  getBrands(): Observable<ApiResponse<BrandRead[]>> {
    console.log('[MasterData] 📡 Intentando conectar al Backend Python en: ' + this.apiUrl);
    return this.http.get<ApiResponse<BrandRead[]>>(`${this.apiUrl}/brands`);
  }
}