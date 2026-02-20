import { Injectable, signal, inject } from '@angular/core';
import { catchError, of } from 'rxjs';
import { ApiSimulationService } from './api-simulation.service';
import { AuthService } from './auth.service';
import { ToastService } from './toast.service';
import { 
  ProductionDashboardDto, 
  ProductionStatDto, 
  WorkOrderDto, 
  DowntimeLogDto, 
  CreateDowntimeCommand, 
  Issue, 
  TrendPointDto, 
  ParetoItemDto 
} from '@models/api.types';

export interface KPI {
  label: string;
  value: string;
  trend: string;       
  trendColor: string;
  iconColor: string; 
  icon: string;
}

@Injectable({
  providedIn: 'root'
})
export class ProductionDataService {
  private api = inject(ApiSimulationService);
  private auth = inject(AuthService);
  private toast = inject(ToastService);

  // --- State Signals ---
  hourlyProduction = signal<ProductionStatDto[]>([]);
  activeOrders = signal<WorkOrderDto[]>([]);
  downtimeLogs = signal<DowntimeLogDto[]>([]);
  issuesCatalog = signal<Issue[]>([]);
  trendData = signal<TrendPointDto[]>([]);
  paretoData = signal<ParetoItemDto[]>([]);
  loading = signal<boolean>(false);
  kpis = signal<KPI[]>([]);

  /**
   * Carga principal del Dashboard con fallback a Demo.
   */
  loadDashboard() {
    const companyId = this.auth.currentContext()?.companyId;
    if (!companyId) return;

    this.loading.set(true);
    
    this.api.getProductionDashboard(companyId).pipe(
      catchError(err => {
        console.warn('Backend de producción en desarrollo. Cargando Mock Data.');
        return of({ data: this.getMockFallbackData() });
      })
    ).subscribe({
      next: (res) => {
        const data = res.data;
        this.hourlyProduction.set(data.hourlyStats);
        this.activeOrders.set(data.activeOrders);
        this.downtimeLogs.set(data.recentDowntime);
        this.trendData.set(data.weeklyTrend);
        this.paretoData.set(data.downtimePareto);
        
        this.updateKPIs(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  /**
   * Carga las órdenes de trabajo. 
   * Usado en el monitor de líneas y listados.
   */
  loadWorkOrders() {
    const companyId = this.auth.currentContext()?.companyId;
    if (!companyId) return;

    this.api.getProductionDashboard(companyId).pipe(
      catchError(() => of({ data: this.getMockFallbackData() }))
    ).subscribe({
      next: (res) => this.activeOrders.set(res.data.activeOrders)
    });
  }

  /**
   * Carga el catálogo de causas de paro
   */
  loadIssues() {
    this.api.getIssues().subscribe(res => this.issuesCatalog.set(res.data));
  }

  /**
   * Registra un nuevo evento de tiempo muerto
   */
  registerDowntime(cmd: CreateDowntimeCommand): Promise<boolean> {
    const companyId = this.auth.currentContext()?.companyId;
    if (!companyId) return Promise.resolve(false);
    // Implementación pendiente de conexión real, por ahora el modal simula
    return Promise.resolve(true);
  }

  /**
   * Genera los objetos KPI para la UI
   */
  private updateKPIs(data: ProductionDashboardDto) {
    const newKpis: KPI[] = [
      { 
        label: 'OEE (Turno)', 
        value: `${data.oee}%`, 
        trend: '↗ +3% vs Ayer', 
        trendColor: 'text-green-500',
        iconColor: 'text-violet-400', 
        icon: 'fa-solid fa-chart-line' 
      },
      { 
        label: 'Tiempo Muerto (Turno)', 
        value: `${data.downtimeMinutes} min`, 
        trend: '↗ +5 min', 
        trendColor: 'text-red-500', 
        iconColor: 'text-yellow-400', 
        icon: 'fa-solid fa-clock' 
      },
      { 
        label: 'Órdenes Activas', 
        value: data.activeOrdersCount.toString(), 
        trend: '↗ +1 Hoy', 
        trendColor: 'text-green-500',
        iconColor: 'text-sky-400', 
        icon: 'fa-solid fa-list-check' 
      }
    ];
    this.kpis.set(newKpis);
  }

  private getMockFallbackData(): ProductionDashboardDto {
    return {
      oee: 84.5,
      downtimeMinutes: 12,
      activeOrdersCount: 3,
      averageEfficiency: 76,
      hourlyStats: [],
      activeOrders: [],
      recentDowntime: [],
      weeklyTrend: [],
      downtimePareto: []
    };
  }
}