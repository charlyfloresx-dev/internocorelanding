import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { environment } from '../../../../../environments/environment';
import { KanbanBoard, OpportunityResponse } from '../models/opportunity.model';

@Injectable({
  providedIn: 'root'
})
export class AssetCrmService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/asset-manager/v1/opportunities`;

  /**
   * Obtiene el tablero Kanban con las oportunidades agrupadas por estado.
   * Utiliza el endpoint real si está disponible, o mocks si está en modo offline UI.
   */
  getKanbanBoard(): Observable<KanbanBoard> {
    // Para validación visual inmediata y flujo, devolvemos un mock representativo de Tijuana
    // Esto luego se cambia al endpoint real: return this.http.get<KanbanBoard>(`${this.apiUrl}/board`);
    
    const mockBoard: KanbanBoard = {
      columns: [
        {
          id: 'DETECTED',
          title: 'Detectadas',
          opportunities: [
            {
              id: 'opp-001',
              cve_cat: 'PK-020-027',
              address: 'VENUSTIANO CARRANZA 6315',
              status: 'DETECTED',
              valor_m2_zona: { amount: 6500, currency: 'MXN' },
              superficie: 180.5,
              adeudo_detectado: { amount: 125000, currency: 'MXN' },
              historical_base_value: { amount: 2500, currency: 'MXN' },
              appreciation_rate: 1.6, // 160% de plusvalía (2500 -> 6500)
              roi_projected: 0.35, // 35%
              risk_buffer: 0.10,
              owner_name: 'JUAN PEREZ (Predial)',
              created_at: new Date().toISOString()
            },
            {
              id: 'opp-002',
              cve_cat: 'PK-020-119',
              address: 'PRESIDENTES 2210',
              status: 'DETECTED',
              valor_m2_zona: { amount: 4500, currency: 'MXN' },
              superficie: 300.0,
              adeudo_detectado: { amount: 45000, currency: 'MXN' },
              historical_base_value: { amount: 1500, currency: 'MXN' },
              appreciation_rate: 2.0, // 200% de plusvalía
              roi_projected: 0.22, // 22%
              risk_buffer: 0.10,
              created_at: new Date(Date.now() - 86400000).toISOString()
            }
          ]
        },
        {
          id: 'IN_ANALYSIS',
          title: 'En Análisis',
          opportunities: [
            {
              id: 'opp-003',
              cve_cat: 'ZL-015-088',
              address: 'ZONA RIO 102',
              status: 'IN_ANALYSIS',
              valor_m2_zona: { amount: 15000, currency: 'MXN' },
              superficie: 50.0,
              adeudo_detectado: { amount: 500000, currency: 'MXN' },
              historical_base_value: { amount: 5000, currency: 'MXN' },
              appreciation_rate: 2.0, // 200% de plusvalía
              roi_projected: 0.15, // 15% (Rojo)
              risk_buffer: 0.20,
              owner_name: 'INMOBILIARIA DEL NORTE',
              created_at: new Date(Date.now() - 172800000).toISOString()
            }
          ]
        },
        {
          id: 'EXECUTED',
          title: 'Ejecutadas',
          opportunities: []
        }
      ]
    };

    return of(mockBoard).pipe(delay(500));
  }

  updateOpportunityStatus(id: string, newStatus: string): Observable<void> {
    // return this.http.patch<void>(`${this.apiUrl}/${id}/status`, { status: newStatus });
    console.log(`Updated opportunity ${id} to ${newStatus}`);
    return of(void 0).pipe(delay(300));
  }
}
