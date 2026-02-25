import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError, finalize } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { ApiResponse, Warehouse } from '@models/api.types';
import { SystemHealthService } from './system-health.service';

@Injectable({
  providedIn: 'root'
})
export class WmsService {
  private http = inject(HttpClient);
  private apiUrl = environment.wmsUrl; // Puerto 8002
  private health = inject(SystemHealthService);

  // Signal para estado de carga (UX)
  loading = signal<boolean>(false);

  /**
   * Obtiene la lista de almacenes disponibles.
   * Implementa Cache-Then-Fallback para resiliencia offline.
   */
  getWarehouses(): Observable<Warehouse[]> {
    this.loading.set(true);
    return this.http.get<ApiResponse<Warehouse[]>>(`${this.apiUrl}/warehouses/`).pipe(
      map(response => {
        this.health.updateStatus('wms', true);
        const data = response.data || [];
        localStorage.setItem('interno_cache_warehouses', JSON.stringify(data));
        return data;
      }),
      catchError(err => {
        this.health.updateStatus('wms', false);
        console.warn('[WmsService] ⚠️ API Error (Warehouses). Serving from cache.', err);
        const cached = localStorage.getItem('interno_cache_warehouses');
        return of(cached ? JSON.parse(cached) : []);
      }),
      finalize(() => this.loading.set(false))
    );
  }
}