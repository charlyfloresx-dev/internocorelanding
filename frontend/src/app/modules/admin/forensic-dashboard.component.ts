import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { interval, Subscription } from 'rxjs';
import { firstValueFrom } from 'rxjs';
import { LocalDatePipe } from '../../shared/pipes/local-date.pipe';

interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  company_id: string;
  tenant_id: string;
  table_name: string;
  action: string;
  old_value: any;
  new_value: any;
  ip_address: string;
  user_agent: string;
  is_active: boolean;
  version_id: number;
}

interface SecurityEvent {
  id: string;
  event_type: string;
  message: string;
  ip_address: string;
  user_agent: string;
  timestamp: string;
  metadata?: {
    jti?: string;
    company_id?: string;
    correlation_id?: string;
    expires_in?: number;
  };
}

@Component({
  selector: 'app-forensic-dashboard',
  standalone: true,
  imports: [CommonModule, MatIconModule, LocalDatePipe],
  template: `
    <div class="p-12 space-y-10 animate-fade-in bg-white min-h-screen">

      <!-- Header + stats -->
      <div class="flex justify-between items-center bg-white">
        <div>
          <h2 class="text-4xl font-black text-slate-950 uppercase tracking-tighter italic">Auditoría Forense</h2>
          <p class="text-slate-500 text-[10px] font-mono uppercase tracking-widest mt-1">Vigilancia Industrial Muro de Hierro</p>
        </div>
        <div class="flex gap-4">
          <div class="px-6 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl flex flex-col items-center justify-center">
            <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Total Eventos</span>
            <span class="text-2xl font-black text-slate-800 dark:text-white">{{ logs().length }}</span>
          </div>
          <div class="px-6 py-4 bg-rose-50 border border-rose-100 rounded-2xl flex flex-col items-center justify-center relative overflow-hidden">
            @if (hasRecentBlock()) {
              <div class="absolute inset-0 bg-rose-500/10 animate-pulse"></div>
            }
            <span class="text-[10px] font-black text-rose-400 uppercase tracking-widest z-10">Bloqueos 402</span>
            <span class="text-2xl font-black text-rose-600 z-10">{{ blockedEventsCount() }}</span>
          </div>
          <div class="px-6 py-4 bg-red-50 border border-red-200 rounded-2xl flex flex-col items-center justify-center relative overflow-hidden">
            @if (securityEvents().length > 0) {
              <div class="absolute inset-0 bg-red-500/10 animate-pulse"></div>
            }
            <span class="text-[10px] font-black text-red-400 uppercase tracking-widest z-10">GOD MODE</span>
            <span class="text-2xl font-black text-red-600 z-10">{{ securityEvents().length }}</span>
          </div>
        </div>
      </div>

      <!-- Tab navigation -->
      <div class="flex gap-1 p-1 bg-slate-100 rounded-2xl w-fit">
        <button
          (click)="activeTab.set('audit')"
          class="px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all"
          [class.bg-white]="activeTab() === 'audit'"
          [class.text-slate-900]="activeTab() === 'audit'"
          [class.shadow-sm]="activeTab() === 'audit'"
          [class.text-slate-500]="activeTab() !== 'audit'"
        >
          Audit Log
        </button>
        <button
          (click)="switchToSecurity()"
          class="px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center gap-2"
          [class.bg-white]="activeTab() === 'security'"
          [class.text-slate-900]="activeTab() === 'security'"
          [class.shadow-sm]="activeTab() === 'security'"
          [class.text-slate-500]="activeTab() !== 'security'"
        >
          Alertas de Seguridad
          @if (securityEvents().length > 0) {
            <span class="px-1.5 py-0.5 bg-red-600 text-white text-[9px] font-black rounded-full">
              {{ securityEvents().length }}
            </span>
          }
        </button>
      </div>

      <!-- ─── TAB: Audit Log ─── -->
      @if (activeTab() === 'audit') {
        <div class="grid grid-cols-1 gap-4">
          @for (log of logs(); track log.id) {
            <div
              class="bg-white rounded-2xl p-6 border shadow-sm transition-all duration-300 flex items-start gap-6"
              [ngClass]="{
                'border-rose-200 shadow-rose-100 bg-rose-50/30': isBlockedEvent(log),
                'border-slate-200 hover:shadow-md': !isBlockedEvent(log)
              }"
            >
              <div
                class="w-12 h-12 rounded-xl flex items-center justify-center text-xl shrink-0"
                [ngClass]="{
                  'bg-rose-100 text-rose-600': isBlockedEvent(log),
                  'bg-emerald-50 text-emerald-600': log.action === 'INSERT',
                  'bg-amber-50 text-amber-600': log.action === 'UPDATE',
                  'bg-slate-50 text-slate-600': log.action === 'SELECT' || log.action === 'DELETE'
                }"
              >
                @if (isBlockedEvent(log)) {
                  <mat-icon>block</mat-icon>
                } @else if (log.action === 'INSERT') {
                  <mat-icon>add_circle</mat-icon>
                } @else if (log.action === 'UPDATE') {
                  <mat-icon>edit</mat-icon>
                } @else {
                  <mat-icon>history</mat-icon>
                }
              </div>

              <div class="flex-1 grid grid-cols-12 gap-4 items-center">
                <div class="col-span-3 flex flex-col">
                  <span class="text-xs font-black text-slate-400 uppercase tracking-widest">Identidad</span>
                  <span class="text-sm font-bold text-slate-800">{{ log.user_id || 'SYSTEM / RFID' }}</span>
                  <span class="text-[10px] font-mono text-slate-500 truncate" title="{{ log.company_id }}">Tenant: {{ log.company_id | slice:0:8 }}</span>
                </div>

                <div class="col-span-3 flex flex-col border-l border-slate-100 pl-4">
                  <span class="text-xs font-black text-slate-400 uppercase tracking-widest">Operación</span>
                  <span class="text-sm font-bold text-slate-800">{{ log.action }}</span>
                  <span class="text-[10px] font-mono text-slate-500">Tabla: {{ log.table_name }}</span>
                </div>

                <div class="col-span-4 flex flex-col border-l border-slate-100 pl-4">
                  <span class="text-xs font-black text-slate-400 uppercase tracking-widest">Contexto (IP / Agente)</span>
                  <span class="text-sm font-bold text-slate-800 truncate" title="{{ log.ip_address }}">{{ log.ip_address || 'Interno' }}</span>
                  <span class="text-[10px] font-mono text-slate-500 truncate" title="{{ log.user_agent }}">{{ log.user_agent || 'N/A' }}</span>
                </div>

                <div class="col-span-2 flex flex-col items-end justify-center">
                  <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Hace</span>
                  <span class="text-sm font-bold" [ngClass]="isBlockedEvent(log) ? 'text-rose-600' : 'text-slate-800'">
                    {{ getTimeAgo(log.timestamp) }}
                  </span>
                </div>
              </div>
            </div>
          }

          @if (logs().length === 0 && !loading()) {
            <div class="text-center p-12 text-slate-500">
              No se encontraron eventos de auditoría.
            </div>
          }
        </div>
      }

      <!-- ─── TAB: Alertas de Seguridad (GOD MODE) ─── -->
      @if (activeTab() === 'security') {
        <div class="space-y-4">
          @if (securityLoading()) {
            <div class="text-center p-12">
              <div class="inline-block w-6 h-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
              <p class="mt-3 text-slate-500 text-xs font-mono">Cargando eventos de seguridad…</p>
            </div>
          }

          @if (!securityLoading() && securityEvents().length === 0) {
            <div class="text-center p-12 text-slate-500">
              <p class="text-sm font-mono">No se encontraron eventos GOD_MODE en el audit trail.</p>
              <p class="text-xs text-slate-400 mt-1">Los eventos aparecen aquí cuando se activa una sesión de emergencia.</p>
            </div>
          }

          @for (ev of securityEvents(); track ev.id) {
            <div
              class="rounded-2xl p-6 border transition-all duration-300"
              [class.border-red-300]="isRecentAlert(ev)"
              [class.animate-pulse]="isRecentAlert(ev)"
              [class.bg-red-50]="isRecentAlert(ev)"
              [class.border-slate-200]="!isRecentAlert(ev)"
              [class.bg-white]="!isRecentAlert(ev)"
            >
              <div class="flex justify-between items-start">
                <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-red-500" [class.animate-ping]="isRecentAlert(ev)"></div>
                  <span class="font-black text-red-700 uppercase text-xs tracking-widest">
                    {{ ev.message || ev.event_type }}
                  </span>
                </div>
                <span class="text-xs font-mono text-slate-400 shrink-0 ml-4">{{ ev.timestamp | localDate:'short' }}</span>
              </div>
              <div class="mt-3 grid grid-cols-3 gap-4 text-xs font-mono text-slate-600">
                <div>
                  <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-0.5">IP</span>
                  <span>{{ ev.ip_address || '—' }}</span>
                </div>
                <div>
                  <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-0.5">JTI</span>
                  <span>{{ (ev.metadata?.jti | slice:0:8) || '—' }}…</span>
                </div>
                <div>
                  <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-0.5">Agente</span>
                  <span class="truncate block" title="{{ ev.user_agent }}">{{ ev.user_agent | slice:0:40 }}</span>
                </div>
              </div>
            </div>
          }

          <!-- Refresh manual -->
          @if (!securityLoading()) {
            <button
              (click)="loadSecurityLogs()"
              class="w-full py-3 border border-slate-200 rounded-xl text-xs font-black text-slate-500 uppercase tracking-widest hover:bg-slate-50 transition-colors"
            >
              Actualizar alertas
            </button>
          }
        </div>
      }
    </div>
  `
})
export class ForensicDashboardComponent implements OnInit, OnDestroy {
  private http = inject(HttpClient);

  logs           = signal<AuditLog[]>([]);
  loading        = signal<boolean>(true);
  securityEvents = signal<SecurityEvent[]>([]);
  securityLoading = signal<boolean>(false);
  activeTab      = signal<'audit' | 'security'>('audit');

  private pollSub?: Subscription;

  ngOnInit() {
    this.fetchLogs();
    this.pollSub = interval(300000).subscribe(() => this.fetchLogs());
  }

  ngOnDestroy() {
    this.pollSub?.unsubscribe();
  }

  fetchLogs(): void {
    this.http.get<{ status: string; data: AuditLog[] }>(`${environment.apiUrl}/api/v1/audit/`)
      .subscribe({
        next: (res) => {
          this.logs.set(res.data);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
  }

  switchToSecurity(): void {
    this.activeTab.set('security');
    if (this.securityEvents().length === 0) {
      this.loadSecurityLogs();
    }
  }

  async loadSecurityLogs(): Promise<void> {
    this.securityLoading.set(true);
    try {
      const res = await firstValueFrom(
        this.http.get<any>(`${environment.apiUrl}/api/v1/admin/security-logs?limit=50`)
      );
      this.securityEvents.set(res.data ?? []);
    } catch {
      // Endpoint requires god-mode or admin token; silently leave empty if unauthorized
    } finally {
      this.securityLoading.set(false);
    }
  }

  isRecentAlert(ev: SecurityEvent): boolean {
    return Date.now() - new Date(ev.timestamp).getTime() < 24 * 60 * 60 * 1000;
  }

  isBlockedEvent(log: AuditLog): boolean {
    return log.action === 'ACCESS_DENIED_402' ||
      (log.new_value && log.new_value.reason === 'Subscription PAST_DUE');
  }

  blockedEventsCount(): number {
    return this.logs().filter(l => this.isBlockedEvent(l)).length;
  }

  hasRecentBlock(): boolean {
    const now = Date.now();
    return this.logs().some(l => this.isBlockedEvent(l) && now - new Date(l.timestamp).getTime() < 60000);
  }

  getTimeAgo(timestamp: string): string {
    const diffMs = Date.now() - new Date(timestamp).getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'segundos';
    if (diffMins < 60) return `${diffMins} min`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hr`;
    return `${Math.floor(diffHours / 24)} días`;
  }
}
