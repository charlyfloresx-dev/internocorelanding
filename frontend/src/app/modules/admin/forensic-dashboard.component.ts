import {Component, inject, signal, OnInit, OnDestroy} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatIconModule} from '@angular/material/icon';
import {HttpClient} from '@angular/common/http';
import {environment} from '../../../environments/environment';
import {interval, Subscription} from 'rxjs';

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

@Component({
  selector: 'app-forensic-dashboard',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="p-12 space-y-10 animate-fade-in bg-white min-h-screen">
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
        </div>
      </div>

      <!-- Logs Grid -->
      <div class="grid grid-cols-1 gap-4">
        @for (log of logs(); track log.id) {
          <div 
            class="bg-white rounded-2xl p-6 border shadow-sm transition-all duration-300 flex items-start gap-6"
            [ngClass]="{
              'border-rose-200 shadow-rose-100 bg-rose-50/30': isBlockedEvent(log),
              'border-slate-200 hover:shadow-md': !isBlockedEvent(log)
            }"
          >
            <!-- Icon indicator based on action type -->
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

            <!-- Content -->
            <div class="flex-1 grid grid-cols-12 gap-4 items-center">
              
              <!-- Subject -->
              <div class="col-span-3 flex flex-col">
                <span class="text-xs font-black text-slate-400 uppercase tracking-widest">Identidad</span>
                <span class="text-sm font-bold text-slate-800">{{ log.user_id || 'SYSTEM / RFID' }}</span>
                <span class="text-[10px] font-mono text-slate-500 truncate" title="{{ log.company_id }}">Tenant: {{ log.company_id | slice:0:8 }}</span>
              </div>

              <!-- Action -->
              <div class="col-span-3 flex flex-col border-l border-slate-100 pl-4">
                <span class="text-xs font-black text-slate-400 uppercase tracking-widest">Operación</span>
                <span class="text-sm font-bold text-slate-800">{{ log.action }}</span>
                <span class="text-[10px] font-mono text-slate-500">Tabla: {{ log.table_name }}</span>
              </div>

              <!-- Context -->
              <div class="col-span-4 flex flex-col border-l border-slate-100 pl-4">
                <span class="text-xs font-black text-slate-400 uppercase tracking-widest">Contexto (IP / Agente)</span>
                <span class="text-sm font-bold text-slate-800 truncate" title="{{ log.ip_address }}">{{ log.ip_address || 'Interno' }}</span>
                <span class="text-[10px] font-mono text-slate-500 truncate" title="{{ log.user_agent }}">{{ log.user_agent || 'N/A' }}</span>
              </div>

              <!-- Timestamp -->
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
    </div>
  `
})
export class ForensicDashboardComponent implements OnInit, OnDestroy {
  private http = inject(HttpClient);
  
  logs = signal<AuditLog[]>([]);
  loading = signal<boolean>(true);
  
  private pollSub?: Subscription;

  ngOnInit() {
    this.fetchLogs();
    // Poll every 5 minutes for dashboard updates
    this.pollSub = interval(300000).subscribe(() => {
      this.fetchLogs();
    });
  }

  ngOnDestroy() {
    if (this.pollSub) {
      this.pollSub.unsubscribe();
    }
  }

  fetchLogs() {
    this.http.get<{status: string, data: AuditLog[]}>(`${environment.apiUrl}/api/v1/audit/`)
      .subscribe({
        next: (res) => {
          this.logs.set(res.data);
          this.loading.set(false);
        },
        error: (err) => {
          console.error("Error fetching audit logs", err);
          this.loading.set(false);
        }
      });
  }

  isBlockedEvent(log: AuditLog): boolean {
    // Assuming blocked events are logged with a specific action or metadata in new_value
    return log.action === 'ACCESS_DENIED_402' || 
           (log.new_value && log.new_value.reason === 'Subscription PAST_DUE');
  }

  blockedEventsCount(): number {
    return this.logs().filter(l => this.isBlockedEvent(l)).length;
  }

  hasRecentBlock(): boolean {
    // Check if there's a block in the last 60 seconds
    const now = new Date();
    return this.logs().some(l => {
      if (!this.isBlockedEvent(l)) return false;
      const logTime = new Date(l.timestamp);
      const diffMs = now.getTime() - logTime.getTime();
      return diffMs < 60000;
    });
  }

  getTimeAgo(timestamp: string): string {
    const now = new Date();
    const logTime = new Date(timestamp);
    const diffMs = now.getTime() - logTime.getTime();
    
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'segundos';
    if (diffMins < 60) return `${diffMins} min`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hr`;
    
    return `${Math.floor(diffHours / 24)} días`;
  }
}
