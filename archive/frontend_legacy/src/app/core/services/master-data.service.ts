import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, catchError } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse, UOMRead, ProductCreatePayload, ProductRead } from '@models/api.types';

@Injectable({
  providedIn: 'root'
})
export class MasterDataService {
  // Assuming environment variable for the master data service URL (e.g., http://localhost:8003)
  private apiUrl = `${environment.masterDataUrl}/api/v1`;
  private http = inject(HttpClient);
  loading = signal(false);

  /**
   * Listar Unidades de Medida
   * Devuelve una lista de todas las Unidades de Medida (UM) para la compañía actual.
   * @returns Observable<ApiResponse<UOMRead[]>>
   */
  listUoms(): Observable<ApiResponse<UOMRead[]>> {
    return this.http.get<ApiResponse<UOMRead[]>>(`${this.apiUrl}/ums/`);
  }

  /**
   * Listar productos de la compañía actual.
   * @returns Observable<ApiResponse<ProductRead[]>>
   */
  getProducts(): Observable<ApiResponse<ProductRead[]>> {
    this.loading.set(true);
    return this.http.get<ApiResponse<ProductRead[]>>(`${this.apiUrl}/products/`).pipe(
      tap(() => this.loading.set(false)),
      catchError(err => {
        this.loading.set(false);
        throw err;
      })
    );
  }

  // Future methods for Brands and Categories will be added here.
}