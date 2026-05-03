// temp_future/src/app/core/services/dashboard.service.ts
import { Injectable, signal, computed, inject, effect } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom, Subscription, filter } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';
import { WebSocketService } from './websocket.service';
import { InventoryDocument, ApiResponse } from '../models/domain.types';

export interface IntegrityMetrics {
  totalValidations: number;
  successful: number;
  discrepancies: number;
  healthPercentage: number;
}

export interface LatencyPoint {
  timestamp: number;
  value: number;
}

export interface UsageMetrics {
  totalPayloadSize: number; // in KB
  requestCount: number;
  operationQuota: number; // Percentage
  activityHeatmap: number[][]; // 7x24 grid
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private ws = inject(WebSocketService);
  private apiUrl = environment.masterDataUrl;

  // === Signals (Live State) ===
  transactionFeed = signal<InventoryDocument[]>([]);
  integrityMetrics = signal<IntegrityMetrics>({
    totalValidations: 0,
    successful: 0,
    discrepancies: 0,
    healthPercentage: 100
  });
  
  latencyHistory = signal<LatencyPoint[]>([]);
  averageLatency = computed(() => {
    const history = this.latencyHistory();
    if (history.length === 0) return 0;
    const sum = history.reduce((acc, p) => acc + p.value, 0);
    return Math.round(sum / history.length);
  });
  
  usageMetrics = signal<UsageMetrics>({
    totalPayloadSize: 0,
    requestCount: 0,
    operationQuota: 0,
    activityHeatmap: Array(7).fill(0).map(() => Array(24).fill(0))
  });
  
  private simulationInterval?: any;
  private activeTelemetryCompany?: string | null = null;

  constructor() {
    // Security: Automatically clear data when company changes
    effect(() => {
      const companyId = this.auth.activeCompanyId();
      const isAuth = this.auth.isAuthenticated();
      
      console.log(`[DashboardService] 🏢 Company scope changed: ${companyId}`);
      this.resetState();
      
      if (isAuth && companyId && this.isValidUUID(companyId)) {
        if (this.activeTelemetryCompany !== companyId) {
          console.log('[Dashboard] 🛰️ Active session detected. Starting telemetry.');
          this.activeTelemetryCompany = companyId;
          this.fetchInitialDashboardData();
        }
      } else {
        this.activeTelemetryCompany = null;
        this.stopTelemetry();
      }
    });

    // Escuchar actualizaciones de inventario en tiempo real vía WebSocket
    this.ws.messages$.pipe(
      filter((msg: any) => msg.type === 'INVENTORY_UPDATE' || msg.type === 'DASHBOARD_RESET')
    ).subscribe((msg: any) => {
       console.log(`[DashboardService] 🚀 Real-time event received (${msg.type}):`, msg.payload);
       
       if (msg.type === 'DASHBOARD_RESET') {
         this.fetchInitialDashboardData();
         return;
       }

       // Actualizar el feed de transacciones localmente
       this.transactionFeed.update(prev => [msg.payload, ...prev].slice(0, 50));
    });
  }

  private isValidUUID(id: string | null): boolean {
    return !!id && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
  }

  private resetState() {
    console.log('[Dashboard] Resetting state for tenant isolation.');
    this.transactionFeed.set([]);
    this.latencyHistory.set([]);
    this.usageMetrics.set({
      totalPayloadSize: 0,
      requestCount: 0,
      operationQuota: 0,
      activityHeatmap: Array(7).fill(0).map(() => Array(24).fill(0))
    });
    this.integrityMetrics.set({
      totalValidations: 0,
      successful: 0,
      discrepancies: 0,
      healthPercentage: 100
    });
  }

  private async fetchInitialDashboardData() {
    try {
      const docs = await this.fetchLatestAudit();
      this.processTelemetry(docs || []);
      this.startSimulation();
    } catch (e) {
      console.error('[Dashboard] Error fetching initial data:', e);
      this.processTelemetry([]);
    }
  }

  private startSimulation() {
    this.stopTelemetry();
    // Start latency simulation
    this.simulationInterval = setInterval(() => {
      this.addLatencyPoint(Math.floor(Math.random() * 45) + 5); // 5-50ms
      this.recordRequest(Math.floor(Math.random() * 2048)); // 0-2KB
    }, 5000);
  }

  private stopTelemetry() {
    if (this.simulationInterval) {
      clearInterval(this.simulationInterval);
      this.simulationInterval = undefined;
    }
  }

  private async fetchLatestAudit(): Promise<InventoryDocument[]> {
    try {
      const resp = await lastValueFrom(
        this.http.get<ApiResponse<InventoryDocument[]>>(`${environment.inventoryUrl}/dashboard/movements?limit=15`)
      );
      return resp.data || [];
    } catch (e) {
      return [];
    }
  }

  private processTelemetry(docs: InventoryDocument[]) {
    this.transactionFeed.set(docs.slice(0, 15));
    
    const total = docs.length;
    const discrepancies = docs.filter(d => (d.movements || []).some((m: any) => m.is_weight_mismatch)).length;
    const successful = total - discrepancies;
    
    this.integrityMetrics.set({
      totalValidations: total,
      successful: successful,
      discrepancies: discrepancies,
      healthPercentage: total > 0 ? (successful / total) * 100 : 100
    });
  }

  addLatencyPoint(ms: number) {
    this.latencyHistory.update(current => {
      const next = [...current, { timestamp: Date.now(), value: ms }];
      return next.slice(-20); // Keep last 20 points
    });
  }

  recordRequest(payloadSize: number) {
    this.usageMetrics.update(current => ({
      ...current,
      requestCount: current.requestCount + 1,
      totalPayloadSize: current.totalPayloadSize + Math.round(payloadSize / 1024),
      operationQuota: Math.min(100, (current.requestCount + 1) / 500 * 100)
    }));

    const now = new Date();
    const day = now.getDay();
    const hour = now.getHours();
    this.usageMetrics.update(current => {
      const newHeatmap = [...current.activityHeatmap];
      newHeatmap[day][hour]++;
      return { ...current, activityHeatmap: newHeatmap };
    });
  }

  async quickSwitchCompany(companyId: string) {
    console.log(`[DashboardService] Quick switching to: ${companyId}`);
    try {
      await this.auth.selectCompany(companyId);
      // resetState() will be triggered by the effect in constructor
    } catch (e) {
      console.error('[DashboardService] Error switching company:', e);
    }
  }
}
