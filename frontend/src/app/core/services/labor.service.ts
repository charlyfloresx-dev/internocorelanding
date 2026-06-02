import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  HeadcountResponse,
  HeadcountHistoryResponse,
  BadgeClockInRequest,
  BadgeClockInResponse,
  CollaboratorBadgeRead,
  CollaboratorBadgeCreate,
} from '../models/mes.types';

@Injectable({ providedIn: 'root' })
export class LaborService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.productionUrl}/mes/labor`;

  // Signals
  headcount = signal<HeadcountResponse | null>(null);
  headcountHistory = signal<HeadcountHistoryResponse | null>(null);
  badges = signal<CollaboratorBadgeRead[]>([]);
  isLoading = signal(false);
  lastError = signal<string | null>(null);

  // Computed conveniences
  activeCount = computed(() => this.headcount()?.headcount.active ?? 0);
  totalRostered = computed(() => this.headcount()?.headcount.total_rostered ?? 0);

  // ── Headcount ─────────────────────────────────────────────────────────────

  async loadHeadcount(resourceId: string): Promise<void> {
    this.isLoading.set(true);
    this.lastError.set(null);
    try {
      const res = await firstValueFrom(
        this.http.get<{ data: HeadcountResponse }>(`${this.base}/headcount/${resourceId}`)
      );
      this.headcount.set(res.data ?? (res as any));
    } catch (e: any) {
      this.lastError.set(e?.error?.message ?? 'Error cargando headcount');
    } finally {
      this.isLoading.set(false);
    }
  }

  async loadHeadcountHistory(resourceId: string, date?: string): Promise<void> {
    const params = date ? `?date=${date}` : '';
    try {
      const res = await firstValueFrom(
        this.http.get<{ data: HeadcountHistoryResponse }>(
          `${this.base}/headcount-history/${resourceId}${params}`
        )
      );
      this.headcountHistory.set(res.data ?? (res as any));
    } catch { /* histórico no crítico */ }
  }

  // ── Badge Clock-In ─────────────────────────────────────────────────────────

  async clockInByBadge(req: BadgeClockInRequest): Promise<BadgeClockInResponse> {
    return firstValueFrom(
      this.http.post<BadgeClockInResponse>(`${this.base}/clock-in-by-badge`, req)
    );
  }

  // ── Badge Admin CRUD ───────────────────────────────────────────────────────

  async loadBadges(collaboratorId?: string): Promise<void> {
    const params = collaboratorId ? `?collaborator_id=${collaboratorId}` : '';
    try {
      const res = await firstValueFrom(
        this.http.get<{ data: CollaboratorBadgeRead[] }>(`${this.base}/badges${params}`)
      );
      this.badges.set(res.data ?? []);
    } catch { this.badges.set([]); }
  }

  createBadge(badge: CollaboratorBadgeCreate) {
    return firstValueFrom(this.http.post(`${this.base}/badges`, badge));
  }

  deactivateBadge(badgeId: string) {
    return firstValueFrom(this.http.patch(`${this.base}/badges/${badgeId}`, { is_active: false }));
  }
}
