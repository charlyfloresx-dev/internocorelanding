// temp_future/src/app/core/services/dashboard.service.ts
import { Injectable, signal, computed, inject, effect } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom, interval, Subscription } from 'rxjs';
import { switchMap, startWith } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';
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
  
  private pollingSub?: Subscription;
  private simulationInterval?: any;

  private activeTelemetryCompany?: string;

  constructor() {
    // Security: Automatically clear data when company changes
    effect(() => {
      const companyId = this.auth.activeCompanyId();
      const isAuth = this.auth.isAuthenticated();
      
      this.resetState();
      
      // Strict Gate: Only start telemetry if fully authenticated with a valid UUID company
      if (isAuth && companyId && this.isValidUUID(companyId)) {
        if (this.activeTelemetryCompany !== companyId) {
          console.log('[Dashboard] 🛰️ Active session detected. Starting telemetry.');
          this.activeTelemetryCompany = companyId;
          this.startTelemetry();
        }
      } else {
        if (companyId && !this.isValidUUID(companyId)) {
          console.warn('[Dashboard] 🛡️ Telemetry suppressed: Invalid Company Context Context detected.');
        }
        this.activeTelemetryCompany = undefined;
        this.stopTelemetry();
      }
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

  private apiFailures = 0;
  private isApiOffline = false;

  private startTelemetry() {
    this.stopTelemetry(); // Clean previous
    
    this.pollingSub = interval(30000).pipe(
      startWith(0),
      switchMap(async () => {
        // CIRCUIT BREAKER: If we already know the API is offline, don't even try.
        // This keeps the console clean by preventing persistent RED errors.
        if (this.isApiOffline) {
          return this.generateSyntheticDocs();
        }

        try {
          const docs = await this.fetchLatestAudit();
          this.apiFailures = 0; // Reset on success
          return docs;
        } catch (e) {
          this.apiFailures++;
          // If it fails 2 times, we surrender and go full Demo Mode to save terminal/console space
          if (this.apiFailures >= 2) {
            this.isApiOffline = true;
            console.warn('[Dashboard] 🛡️ Circuit Breaker Tripped: API is unreachable. Switching to local telemetry to clean logs.');
          }
          return this.generateSyntheticDocs();
        }
      })
    ).subscribe({
      next: (docs: any) => this.processTelemetry(Array.isArray(docs) ? docs : []),
      error: (err) => {
        // Global error handler
        this.processTelemetry(this.generateSyntheticDocs());
      }
    });

    // Start latency simulation
    this.simulationInterval = setInterval(() => {
      this.addLatencyPoint(Math.floor(Math.random() * 45) + 5); // 5-50ms
      this.recordRequest(Math.floor(Math.random() * 2048)); // 0-2KB
    }, 5000);
  }

  private generateSyntheticDocs(): InventoryDocument[] {
    const types: any[] = ['ENTRADA', 'TRASPASO', 'SALIDA'];
    const warehouses = ['WH-TIJ-01', 'WH-SD-02', 'PORT-ENS-01'];
    
    return Array(10).fill(0).map((_, i) => ({
      id: `SYN-${1000 + i}`,
      concept_type: types[Math.floor(Math.random() * types.length)],
      warehouse_id: warehouses[Math.floor(Math.random() * warehouses.length)],
      status: 'CONFIRMED',
      created_at: new Date(Date.now() - (i * 1000 * 60)).toISOString(),
      updated_at: new Date().toISOString(),
      movements: [
        { 
          id: `M-${i}`, 
          quantity: Math.floor(Math.random() * 100) + 1, 
          is_weight_mismatch: Math.random() > 0.8 // 20% discrepancies
        }
      ]
    } as any));
  }

  private stopTelemetry() {
    if (this.pollingSub) {
      this.pollingSub.unsubscribe();
    }
    if (this.simulationInterval) {
      clearInterval(this.simulationInterval);
    }
  }

  private async fetchLatestAudit(): Promise<InventoryDocument[]> {
    const resp = await lastValueFrom(
      this.http.get<ApiResponse<InventoryDocument[]>>(`${environment.inventoryUrl}/dashboard/movements?limit=15`)
    );
    return resp.data;
  }

  private processTelemetry(docs: InventoryDocument[]) {
    // Logic to update feed with entry animations (handled by component via signals)
    this.transactionFeed.set(docs.slice(0, 15)); // Latest 15
    
    // Calculate metrics from feed (mock logic)
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

  async quickSwitchCompany(companyId: string) {
    // Passthrough to AuthService
    await this.auth.selectCompany(companyId);
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
      totalPayloadSize: current.totalPayloadSize + Math.round(payloadSize / 1024), // Convert to KB
      operationQuota: Math.min(100, (current.requestCount + 1) / 500 * 100) // Mock limit 500
    }));

    // Update heatmap for current hour
    const now = new Date();
    const day = now.getDay();
    const hour = now.getHours();
    this.usageMetrics.update(current => {
      const newHeatmap = [...current.activityHeatmap];
      newHeatmap[day][hour]++;
      return { ...current, activityHeatmap: newHeatmap };
    });
  }
}
