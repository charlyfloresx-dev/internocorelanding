import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiResponse, BrandRead, CategoryRead, ProductRead, UOMRead } from '../../modules/catalog/models/catalog.types';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class MasterDataService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly apiUrl = 'http://localhost:8003/api/v1'; // Puerto del Master Data Service (Directo)

  /**
   * PRODUCTS
   */
  getProducts(): Observable<ApiResponse<ProductRead[]>> {
    const url = `${this.apiUrl}/products`;
    const companyId = this.auth.activeCompanyId();
    console.log(`[MasterDataService] 🚀 Consultando productos en: ${url} con Company-Id: ${companyId}`);
    return this.http.get<ApiResponse<ProductRead[]>>(url);
  }

  /**
   * UNITS OF MEASURE (UOM)
   */
  getUoms(): Observable<ApiResponse<UOMRead[]>> {
    return this.http.get<ApiResponse<UOMRead[]>>(`${this.apiUrl}/ums`);
  }

  /**
   * CATEGORIES
   */
  getCategories(): Observable<ApiResponse<CategoryRead[]>> {
    return this.http.get<ApiResponse<CategoryRead[]>>(`${this.apiUrl}/categories`);
  }

  /**
   * BRANDS
   */
  getBrands(): Observable<ApiResponse<BrandRead[]>> {
    return this.http.get<ApiResponse<BrandRead[]>>(`${this.apiUrl}/brands`);
  }
}