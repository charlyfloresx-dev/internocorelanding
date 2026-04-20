import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse, InventorySummary, MovementDocumentRow, DashboardDTO } from '@models/api.types';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.inventoryUrl}/dashboard`;

  /**
   * Returns aggregated counts for the top dashboard cards.
   */
  getSummary(): Observable<ApiResponse<InventorySummary>> {
    return this.http.get<ApiResponse<InventorySummary>>(`${this.apiUrl}/summary`);
  }

  /**
   * Returns a paginated and filtered list of inventory documents (Ledger).
   */
  getMovements(limit: number = 50, offset: number = 0, type?: string): Observable<ApiResponse<MovementDocumentRow[]>> {
    let url = `${this.apiUrl}/movements?limit=${limit}&offset=${offset}`;
    if (type) {
      url += `&type=${type}`;
    }
    return this.http.get<ApiResponse<MovementDocumentRow[]>>(url);
  }

  /**
   * Returns the consolidated Mission Control dashboard metrics.
   */
  getMissionControl(warehouseId: string): Observable<ApiResponse<DashboardDTO>> {
    return this.http.get<ApiResponse<DashboardDTO>>(`${this.apiUrl}/mission-control?warehouse_id=${warehouseId}`);
  }
}
