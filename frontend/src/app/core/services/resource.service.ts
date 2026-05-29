import { Injectable, signal, inject, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ResourceRead,
  ResourceCreate,
  ResourceUpdate,
  ResourceGraphicResponse,
  ActiveWorkOrderResponse,
  PlannedWorkOrderResponse,
  FacilityRead,
  ProductionAreaRead,
} from '../models/mes.types';

@Injectable({ providedIn: 'root' })
export class ResourceService {
  private http = inject(HttpClient);
  private base = environment.productionUrl; // routes through /api/v1 → nginx → mes-service:8000

  // ── Query state ────────────────────────────────────────────────────────────

  readonly resource     = signal<ResourceRead | null>(null);
  readonly graphic      = signal<ResourceGraphicResponse | null>(null);
  readonly activeWO     = signal<ActiveWorkOrderResponse | null>(null);
  readonly plannedWOs   = signal<PlannedWorkOrderResponse[]>([]);
  readonly resourceList = signal<ResourceRead[]>([]);

  readonly isLoading       = signal(false);
  readonly isLoadingGraphic = signal(false);
  readonly error           = signal<string | null>(null);

  // ── Computed convenience signals ───────────────────────────────────────────

  readonly hourlySlots = computed(() => this.graphic()?.hours ?? []);
  readonly breaks      = computed(() => this.graphic()?.breaks ?? []);
  readonly cumulativeTable = computed(() => this.graphic()?.cumulative_table ?? []);
  readonly totalGoal   = computed(() => this.graphic()?.total_goal ?? 0);
  readonly totalActual = computed(() => this.graphic()?.total_actual ?? 0);
  readonly shiftName   = computed(() => this.graphic()?.shift_name ?? '—');
  readonly progressPct = computed(() => this.activeWO()?.progress_pct ?? 0);

  // ── loadResource ───────────────────────────────────────────────────────────

  async loadResource(code: string): Promise<void> {
    this.isLoading.set(true);
    this.error.set(null);
    try {
      const resp: any = await lastValueFrom(
        this.http.get(`${this.base}/mes/resources/${encodeURIComponent(code)}`)
      );
      this.resource.set(resp?.data ?? resp);
    } catch (err: any) {
      this.error.set(err?.error?.detail ?? `Recurso '${code}' no encontrado`);
      this.resource.set(null);
    } finally {
      this.isLoading.set(false);
    }
  }

  // ── loadGraphic ────────────────────────────────────────────────────────────

  async loadGraphic(code: string, targetDate?: string): Promise<void> {
    this.isLoadingGraphic.set(true);
    try {
      const params = targetDate ? `?target_date=${targetDate}` : '';
      const resp: any = await lastValueFrom(
        this.http.get(`${this.base}/mes/resources/${encodeURIComponent(code)}/graphic${params}`)
      );
      this.graphic.set(resp?.data ?? resp);
    } catch (err: any) {
      this.graphic.set(null);
    } finally {
      this.isLoadingGraphic.set(false);
    }
  }

  // ── loadActiveWorkOrder ────────────────────────────────────────────────────

  async loadActiveWorkOrder(code: string): Promise<void> {
    try {
      const resp: any = await lastValueFrom(
        this.http.get(`${this.base}/mes/resources/${encodeURIComponent(code)}/active-workorder`)
      );
      this.activeWO.set(resp?.data ?? resp);
    } catch {
      this.activeWO.set(null);
    }
  }

  // ── loadPlannedWorkOrders ──────────────────────────────────────────────────

  async loadPlannedWorkOrders(code: string): Promise<void> {
    try {
      const resp: any = await lastValueFrom(
        this.http.get(`${this.base}/mes/resources/${encodeURIComponent(code)}/planned-workorders`)
      );
      const data = resp?.data ?? resp;
      this.plannedWOs.set(Array.isArray(data) ? data : []);
    } catch {
      this.plannedWOs.set([]);
    }
  }

  // ── listResources ──────────────────────────────────────────────────────────

  async listResources(): Promise<ResourceRead[]> {
    try {
      const resp: any = await lastValueFrom(
        this.http.get(`${this.base}/mes/resources/`)
      );
      const data = resp?.data ?? resp;
      const list: ResourceRead[] = Array.isArray(data) ? data : [];
      this.resourceList.set(list);
      return list;
    } catch {
      this.resourceList.set([]);
      return [];
    }
  }

  // ── loadAll ────────────────────────────────────────────────────────────────
  /** Fetches resource details, graphic, active WO and planned WOs in parallel. */
  async loadAll(code: string): Promise<void> {
    await Promise.all([
      this.loadResource(code),
      this.loadGraphic(code),
      this.loadActiveWorkOrder(code),
      this.loadPlannedWorkOrders(code),
    ]);
  }

  reset(): void {
    this.resource.set(null);
    this.graphic.set(null);
    this.activeWO.set(null);
    this.plannedWOs.set([]);
    this.error.set(null);
  }

  // ── Mutation methods (Phase 156-B) ─────────────────────────────────────────

  async createResource(body: ResourceCreate): Promise<ResourceRead> {
    const resp: any = await lastValueFrom(
      this.http.post(`${this.base}/mes/resources/`, body)
    );
    return resp?.data ?? resp;
  }

  async updateResource(code: string, body: ResourceUpdate): Promise<ResourceRead> {
    const resp: any = await lastValueFrom(
      this.http.patch(`${this.base}/mes/resources/${encodeURIComponent(code)}`, body)
    );
    return resp?.data ?? resp;
  }

  async bulkCreateResources(rows: ResourceCreate[]): Promise<{ created: number; skipped: number; errors: any[] }> {
    const resp: any = await lastValueFrom(
      this.http.post(`${this.base}/mes/resources/bulk`, rows)
    );
    return resp?.data ?? resp;
  }

  // ── Config lists ───────────────────────────────────────────────────────────

  async listFacilities(): Promise<FacilityRead[]> {
    try {
      const resp: any = await lastValueFrom(
        this.http.get(`${this.base}/mes/resources/facilities`)
      );
      const data = resp?.data ?? resp;
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  }

  async listProductionAreas(facilityId?: string): Promise<ProductionAreaRead[]> {
    try {
      const params = facilityId ? `?facility_id=${facilityId}` : '';
      const resp: any = await lastValueFrom(
        this.http.get(`${this.base}/mes/resources/production-areas${params}`)
      );
      const data = resp?.data ?? resp;
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  }
}
