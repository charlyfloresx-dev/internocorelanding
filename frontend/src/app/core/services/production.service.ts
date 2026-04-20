import { Injectable, signal, inject, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, of, lastValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';
import { SystemHealthService } from './system-health.service';
import { 
  ProductionDashboardDto, 
  WorkOrderDto, 
  DowntimeLogDto, 
  ApiResponse,
  ProductionStatDto
} from '../models/domain.types';

@Injectable({
  providedIn: 'root'
})
export class ProductionService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private health = inject(SystemHealthService);
  private apiUrl = environment.productionUrl; // Use productionUrl from environment

  // --- State Signals ---
  public dashboard = signal<ProductionDashboardDto | null>(null);
  public hourlyProduction = computed(() => this.dashboard()?.hourly_stats || []);
  public activeOrders = computed(() => this.dashboard()?.active_orders || []);
  public recentDowntime = computed(() => this.dashboard()?.recent_downtime || []);
  
  public isLoading = signal<boolean>(false);
  public lastError = signal<string | null>(null);

  /**
   * Industrial KPIs computed from dashboard state
   */
  public kpis = computed(() => {
    const data = this.dashboard();
    if (!data) return [];

    return [
      { 
        label: 'OEE (Turno)', 
        value: `${data.oee}%`, 
        trend: '↗ +3% vs Ayer', 
        trendColor: 'text-green-400',
        iconColor: 'text-violet-400', 
        icon: 'fa-solid fa-chart-line' 
      },
      { 
        label: 'Tiempo Muerto (Turno)', 
        value: `${data.downtime_minutes} min`, 
        trend: '↗ +5 min', 
        trendColor: 'text-red-400', 
        iconColor: 'text-yellow-400', 
        icon: 'fa-solid fa-clock' 
      },
      { 
        label: 'Órdenes Activas', 
        value: data.active_orders_count.toString(), 
        trend: '↗ +1 Hoy', 
        trendColor: 'text-green-400',
        iconColor: 'text-sky-400', 
        icon: 'fa-solid fa-list-check' 
      }
    ];
  });

  /**
   * Overall OEE Signal
   */
  public oee = computed(() => this.dashboard()?.oee || 0);

  /**
   * Load the production dashboard data
   */
  async loadDashboard() {
    const companyId = this.auth.activeCompanyId();
    if (!companyId) return;

    this.isLoading.set(true);
    this.lastError.set(null);

    try {
      // Use the real dashboard endpoint if available, or simulation if not
      const resp = await lastValueFrom(
        this.http.get<ApiResponse<ProductionDashboardDto>>(`${this.apiUrl}/api/v1/production/dashboard`)
      );

      if (resp.status === 'success') {
        this.dashboard.set(resp.data);
        this.health.reportSuccess('inventory'); // Reuse inventory health for now or extend
      }
    } catch (err) {
      console.warn('[ProductionService] Backend failing. Fallback to simulation.');
      this.lastError.set('Backend unavailable. Showing simulated data.');
      this.dashboard.set(this.getMockData());
      this.health.reportFailure('inventory');
    } finally {
      this.isLoading.set(false);
    }
  }

  /**
   * Ported Work Order retrieval
   */
  async getWorkOrders() {
    try {
       const resp = await lastValueFrom(
         this.http.get<ApiResponse<WorkOrderDto[]>>(`${this.apiUrl}/api/v1/production/work-orders`)
       );
       return resp.data;
    } catch (err) {
       return [];
    }
  }

  private getMockData(): ProductionDashboardDto {
    return {
      oee: 82.4,
      downtime_minutes: 45,
      active_orders_count: 5,
      average_efficiency: 78.2,
      hourly_stats: [
        { hour: '08:00', actual: 120, goal: 150, status: 'warning' },
        { hour: '09:00', actual: 160, goal: 150, status: 'excellent' },
        { hour: '10:00', actual: 145, goal: 150, status: 'good' }
      ],
      active_orders: [],
      recent_downtime: []
    };
  }
}
