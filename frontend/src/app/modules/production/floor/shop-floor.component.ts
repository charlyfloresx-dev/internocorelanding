import {
  Component, inject, OnInit, OnDestroy, signal, computed, ChangeDetectionStrategy
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { LaborService } from '../../../core/services/labor.service';
import { ResourceService } from '../../../core/services/resource.service';
import { BadgeClockInResponse, CollaboratorOnFloor, HourlyLaborPoint } from '../../../core/models/mes.types';

interface ScanFeedback {
  type: 'success' | 'transfer' | 'duplicate' | 'error';
  message: string;
  collaboratorName?: string;
  timestamp?: string;
}

interface OfflineQueueEntry {
  request: { resource_code: string; production_run_id: string; badge_raw_value: string; client_timestamp: string };
  retries: number;
}

@Component({
  selector: 'app-shop-floor',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="min-h-screen bg-slate-950 text-white flex flex-col">

      <!-- ── Top bar ─────────────────────────────────────────────── -->
      <header class="flex items-center justify-between px-6 py-3 bg-slate-900 border-b border-slate-800">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-violet-600/20 flex items-center justify-center">
            <i class="fa-solid fa-microchip text-violet-400 text-sm"></i>
          </div>
          <div>
            <h1 class="text-sm font-bold text-white leading-tight">{{ resourceName() }}</h1>
            <p class="text-[10px] text-slate-500 uppercase tracking-wider">Piso de Producción</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <!-- Online/Offline indicator -->
          <span class="flex items-center gap-1.5 text-xs font-bold"
                [class.text-green-400]="isOnline()"
                [class.text-amber-400]="!isOnline()">
            <span class="w-2 h-2 rounded-full"
                  [class.bg-green-500]="isOnline()"
                  [class.bg-amber-500]="!isOnline()"
                  [class.animate-pulse]="true"></span>
            {{ isOnline() ? 'Online' : 'Offline (' + offlineQueue().length + ')' }}
          </span>
          <!-- Clock -->
          <span class="font-mono text-sm text-slate-300">{{ clockDisplay() }}</span>
          <!-- Refresh button -->
          <button (click)="refreshData()"
                  class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center transition-colors">
            <i class="fa-solid fa-rotate-right text-xs text-slate-400"></i>
          </button>
        </div>
      </header>

      <!-- ── Body ────────────────────────────────────────────────── -->
      <main class="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-0 overflow-hidden">

        <!-- Left: Scanner zone + hourly chart -->
        <div class="lg:col-span-2 flex flex-col gap-0 border-r border-slate-800">

          <!-- Scanner zone -->
          <div class="flex-none p-6 border-b border-slate-800">
            <div class="relative rounded-2xl overflow-hidden"
                 [class.ring-2]="scanFeedback()"
                 [class.ring-green-500]="scanFeedback()?.type === 'success'"
                 [class.ring-blue-500]="scanFeedback()?.type === 'transfer'"
                 [class.ring-amber-500]="scanFeedback()?.type === 'duplicate'"
                 [class.ring-red-500]="scanFeedback()?.type === 'error'">

              <!-- Scanner ready area -->
              <div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col items-center gap-4 min-h-[160px] justify-center"
                   [class.bg-green-900\/20]="scanFeedback()?.type === 'success'"
                   [class.bg-blue-900\/20]="scanFeedback()?.type === 'transfer'"
                   [class.bg-red-900\/20]="scanFeedback()?.type === 'error'">

                @if (!scanFeedback()) {
                  <!-- Idle state -->
                  <div class="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center relative">
                    <i class="fa-solid fa-id-card text-2xl text-slate-600"></i>
                    @if (!debounceActive()) {
                      <span class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-green-500 animate-ping"></span>
                      <span class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-green-500"></span>
                    }
                  </div>
                  <div class="text-center">
                    <p class="text-white font-bold text-lg">{{ debounceActive() ? 'Procesando...' : 'Listo para escanear' }}</p>
                    <p class="text-slate-500 text-sm">Acerque tarjeta RFID, QR o código de barras</p>
                  </div>

                } @else {
                  <!-- Scan result -->
                  <div class="flex flex-col items-center gap-3 w-full animate-fade-in">
                    <div class="w-16 h-16 rounded-2xl flex items-center justify-center"
                         [class.bg-green-500\/20]="scanFeedback()!.type === 'success'"
                         [class.bg-blue-500\/20]="scanFeedback()!.type === 'transfer'"
                         [class.bg-amber-500\/20]="scanFeedback()!.type === 'duplicate'"
                         [class.bg-red-500\/20]="scanFeedback()!.type === 'error'">
                      <i class="text-2xl"
                         [class.fa-solid]="true"
                         [class.fa-check]="scanFeedback()!.type === 'success'"
                         [class.fa-shuffle]="scanFeedback()!.type === 'transfer'"
                         [class.fa-rotate-right]="scanFeedback()!.type === 'duplicate'"
                         [class.fa-xmark]="scanFeedback()!.type === 'error'"
                         [class.text-green-400]="scanFeedback()!.type === 'success'"
                         [class.text-blue-400]="scanFeedback()!.type === 'transfer'"
                         [class.text-amber-400]="scanFeedback()!.type === 'duplicate'"
                         [class.text-red-400]="scanFeedback()!.type === 'error'"></i>
                    </div>
                    <div class="text-center">
                      @if (scanFeedback()!.collaboratorName) {
                        <p class="text-xl font-bold text-white">{{ scanFeedback()!.collaboratorName }}</p>
                      }
                      <p class="text-sm font-medium"
                         [class.text-green-400]="scanFeedback()!.type === 'success'"
                         [class.text-blue-400]="scanFeedback()!.type === 'transfer'"
                         [class.text-amber-400]="scanFeedback()!.type === 'duplicate'"
                         [class.text-red-400]="scanFeedback()!.type === 'error'">
                        {{ scanFeedback()!.message }}
                      </p>
                    </div>
                    <!-- Debounce progress bar -->
                    @if (debounceActive()) {
                      <div class="w-full h-1 bg-slate-700 rounded-full overflow-hidden mt-2">
                        <div class="h-full bg-slate-500 rounded-full animate-[shrink_1.5s_linear_forwards]"></div>
                      </div>
                    }
                  </div>
                }
              </div>
            </div>
          </div>

          <!-- Hourly density chart -->
          <div class="flex-1 p-6">
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 h-full relative overflow-hidden">
              <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 to-sky-500"></div>
              <h3 class="text-white font-bold mb-4 flex items-center gap-2 text-sm">
                <i class="fa-solid fa-users text-violet-400"></i>
                Densidad de Personal por Hora
              </h3>

              @if (laborSvc.headcountHistory()) {
                @let series = laborSvc.headcountHistory()!.series;
                @let maxVal = maxHeadcount();
                <div class="flex items-end gap-1.5 h-36">
                  @for (point of series; track point.hour) {
                    <div class="flex-1 flex flex-col items-center gap-1 group cursor-default"
                         [title]="point.label + ': ' + point.active + ' activos, ' + point.on_permit + ' permiso'">
                      <div class="w-full flex flex-col justify-end rounded-t-lg overflow-hidden" [style.height.px]="100">
                        <!-- On permit (amber, top) -->
                        @if (point.on_permit > 0 && maxVal > 0) {
                          <div class="w-full bg-amber-500/60 transition-all"
                               [style.height.%]="(point.on_permit / maxVal) * 100"></div>
                        }
                        <!-- Active (green, bottom) -->
                        @if (point.active > 0 && maxVal > 0) {
                          <div class="w-full bg-emerald-500 transition-all"
                               [style.height.%]="(point.active / maxVal) * 100"></div>
                        }
                        @if (point.total === 0) {
                          <div class="w-full bg-slate-800 h-full"></div>
                        }
                      </div>
                      <span class="text-[9px] text-slate-600 font-mono">{{ point.hour }}h</span>
                    </div>
                  }
                </div>
                <!-- Legend -->
                <div class="flex gap-4 mt-3">
                  <span class="flex items-center gap-1.5 text-[10px] text-slate-400">
                    <span class="w-2.5 h-2.5 rounded-sm bg-emerald-500"></span> Activos
                  </span>
                  <span class="flex items-center gap-1.5 text-[10px] text-slate-400">
                    <span class="w-2.5 h-2.5 rounded-sm bg-amber-500/60"></span> En Permiso
                  </span>
                </div>
              } @else {
                <div class="h-36 flex items-center justify-center text-slate-600 text-sm">
                  Sin datos de historial para hoy
                </div>
              }
            </div>
          </div>
        </div>

        <!-- Right: Headcount panel -->
        <div class="flex flex-col gap-0">

          <!-- Headcount summary -->
          <div class="p-6 border-b border-slate-800">
            <h2 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">
              Personal en Línea
            </h2>

            @if (laborSvc.headcount()) {
              @let hc = laborSvc.headcount()!.headcount;
              <div class="grid grid-cols-2 gap-3 mb-4">
                <!-- Active -->
                <div class="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center">
                  <div class="text-3xl font-black text-emerald-400">{{ hc.active }}</div>
                  <div class="text-[10px] text-emerald-600 font-bold uppercase tracking-wider mt-1">Activos</div>
                </div>
                <!-- Total rostered -->
                <div class="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center">
                  <div class="text-3xl font-black text-white">{{ hc.total_rostered }}</div>
                  <div class="text-[10px] text-slate-500 font-bold uppercase tracking-wider mt-1">Total</div>
                </div>
                <!-- On permit -->
                @if (hc.on_permit > 0) {
                  <div class="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 text-center">
                    <div class="text-2xl font-black text-amber-400">{{ hc.on_permit }}</div>
                    <div class="text-[10px] text-amber-600 font-bold uppercase tracking-wider mt-0.5">Permiso</div>
                  </div>
                }
                <!-- Transferred in -->
                @if (hc.transferred_in > 0) {
                  <div class="bg-blue-500/10 border border-blue-500/20 rounded-xl p-3 text-center">
                    <div class="text-2xl font-black text-blue-400">{{ hc.transferred_in }}</div>
                    <div class="text-[10px] text-blue-600 font-bold uppercase tracking-wider mt-0.5">Trasladados</div>
                  </div>
                }
              </div>
            } @else if (laborSvc.isLoading()) {
              <div class="text-center py-8 text-slate-600 text-sm">Cargando...</div>
            } @else {
              <div class="text-center py-8 text-slate-700 text-sm">Sin datos</div>
            }
          </div>

          <!-- Collaborators list -->
          <div class="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar">
            @if (laborSvc.headcount()) {
              @for (collab of laborSvc.headcount()!.collaborators; track collab.id) {
                <div class="flex items-center gap-3 p-3 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors">
                  <!-- Status dot -->
                  <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-black"
                       [class.bg-emerald-500\/15]="collab.status === 'ACTIVE'"
                       [class.text-emerald-400]="collab.status === 'ACTIVE'"
                       [class.bg-amber-500\/15]="collab.status === 'ON_PERMIT'"
                       [class.text-amber-400]="collab.status === 'ON_PERMIT'"
                       [class.bg-blue-500\/15]="collab.status === 'TRANSFERRED_IN'"
                       [class.text-blue-400]="collab.status === 'TRANSFERRED_IN'">
                    <i class="fa-solid"
                       [class.fa-person-digging]="collab.status === 'ACTIVE'"
                       [class.fa-mug-hot]="collab.status === 'ON_PERMIT'"
                       [class.fa-right-left]="collab.status === 'TRANSFERRED_IN'"></i>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-bold text-white truncate leading-tight">{{ collab.name }}</p>
                    <div class="flex items-center gap-2 mt-0.5">
                      <span class="text-[10px] font-mono text-slate-500">{{ collab.clock_in }}</span>
                      @if (collab.is_deviation) {
                        <span class="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 text-[9px] font-bold uppercase tracking-wider border border-amber-500/20">
                          Desviación
                        </span>
                      }
                    </div>
                  </div>
                </div>
              }
              @if (laborSvc.headcount()!.collaborators.length === 0) {
                <div class="text-center py-12 text-slate-700">
                  <i class="fa-solid fa-users text-3xl mb-3 block"></i>
                  <p class="text-sm">Sin personal registrado</p>
                </div>
              }
            }
          </div>
        </div>
      </main>
    </div>
  `,
  styles: [`
    .custom-scrollbar::-webkit-scrollbar { width: 3px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }

    @keyframes shrink {
      from { width: 100%; }
      to   { width: 0%; }
    }
  `]
})
export class ShopFloorComponent implements OnInit, OnDestroy {
  // Services
  readonly laborSvc = inject(LaborService);
  private readonly route = inject(ActivatedRoute);
  private readonly resourceSvc = inject(ResourceService);

  // State signals
  resourceId = signal('');
  resourceName = signal('Recurso');
  productionRunId = signal('');
  resourceCode = signal('');

  debounceActive = signal(false);
  scanFeedback = signal<ScanFeedback | null>(null);
  isOnline = signal(navigator.onLine);
  offlineQueue = signal<OfflineQueueEntry[]>([]);
  clockDisplay = signal('');

  maxHeadcount = computed(() => {
    const series = this.laborSvc.headcountHistory()?.series ?? [];
    return Math.max(...series.map(s => s.total), 1);
  });

  // Internal
  private scanBuffer = '';
  private refreshInterval?: ReturnType<typeof setInterval>;
  private clockInterval?: ReturnType<typeof setInterval>;
  private feedbackTimeout?: ReturnType<typeof setTimeout>;
  private readonly DEBOUNCE_MS = 1500;
  private readonly MIN_BADGE_LENGTH = 3;
  private readonly keydownHandler = this.onKeydown.bind(this);
  private readonly onlineHandler = () => { this.isOnline.set(true); this.flushOfflineQueue(); };
  private readonly offlineHandler = () => this.isOnline.set(false);

  ngOnInit(): void {
    // Resolve route param
    const id = this.route.snapshot.paramMap.get('resourceId') ?? '';
    this.resourceId.set(id);

    // Keyboard HID listener (global focus — captures scanner without manual click)
    document.addEventListener('keydown', this.keydownHandler);

    // Online/offline listeners
    window.addEventListener('online', this.onlineHandler);
    window.addEventListener('offline', this.offlineHandler);

    // Live clock
    this.updateClock();
    this.clockInterval = setInterval(() => this.updateClock(), 1000);

    // Auto-refresh headcount every 30s
    this.refreshData();
    this.refreshInterval = setInterval(() => this.refreshData(), 30_000);

    // Load resource meta
    this.resourceSvc.loadResource(id).catch(() => {});
  }

  ngOnDestroy(): void {
    document.removeEventListener('keydown', this.keydownHandler);
    window.removeEventListener('online', this.onlineHandler);
    window.removeEventListener('offline', this.offlineHandler);
    clearInterval(this.refreshInterval);
    clearInterval(this.clockInterval);
    clearTimeout(this.feedbackTimeout);
  }

  // ── Scanner keyboard HID listener ─────────────────────────────────────────

  onKeydown(event: KeyboardEvent): void {
    // Block if debounce is active (prevents infinite loops from RFID tag on antenna)
    if (this.debounceActive()) return;

    if (event.key === 'Enter') {
      if (this.scanBuffer.length >= this.MIN_BADGE_LENGTH) {
        event.preventDefault();
        const value = this.scanBuffer;
        this.scanBuffer = '';
        void this.processScan(value);
      } else {
        this.scanBuffer = '';
      }
    } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      this.scanBuffer += event.key;
    }
  }

  private async processScan(badgeValue: string): Promise<void> {
    // Activate debounce immediately (1.5s lock — prevents double-reads from RFID antenna)
    this.debounceActive.set(true);
    setTimeout(() => this.debounceActive.set(false), this.DEBOUNCE_MS);

    if (!this.productionRunId()) {
      this.showFeedback({ type: 'error', message: 'Sin orden activa asignada al recurso' });
      return;
    }

    const req = {
      resource_code: this.resourceCode(),
      production_run_id: this.productionRunId(),
      badge_raw_value: badgeValue,
      client_timestamp: new Date().toISOString(),
    };

    if (!this.isOnline()) {
      this.offlineQueue.update(q => [...q, { request: req, retries: 0 }]);
      this.showFeedback({ type: 'error', message: 'Sin conexión — evento encolado' });
      return;
    }

    try {
      const res = await this.laborSvc.clockInByBadge(req);
      this.handleScanResponse(res);
      void this.laborSvc.loadHeadcount(this.resourceId());
    } catch (err: any) {
      const msg = err?.error?.detail ?? err?.message ?? 'Error de comunicación';
      this.showFeedback({ type: 'error', message: msg });
    }
  }

  private handleScanResponse(res: BadgeClockInResponse): void {
    const name = res.collaborator?.full_name ?? '';
    switch (res.action) {
      case 'CLOCK_IN':
        this.showFeedback({ type: 'success', message: 'Entrada registrada', collaboratorName: name });
        break;
      case 'TRANSFER':
        this.showFeedback({ type: 'transfer', message: 'Traslado automático', collaboratorName: name });
        break;
      case 'ALREADY_CLOCKED_IN':
        this.showFeedback({ type: 'duplicate', message: 'Ya registrado en este recurso', collaboratorName: name });
        break;
    }
  }

  private showFeedback(fb: ScanFeedback): void {
    clearTimeout(this.feedbackTimeout);
    this.scanFeedback.set({ ...fb, timestamp: new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' }) });
    // Auto-clear after 4s
    this.feedbackTimeout = setTimeout(() => this.scanFeedback.set(null), 4000);
  }

  // ── Offline queue flush ───────────────────────────────────────────────────

  private async flushOfflineQueue(): Promise<void> {
    const queue = [...this.offlineQueue()];
    if (!queue.length) return;
    this.offlineQueue.set([]);

    for (const entry of queue) {
      try {
        await this.laborSvc.clockInByBadge(entry.request);
      } catch {
        // Re-enqueue if still failing
        if (entry.retries < 3) {
          this.offlineQueue.update(q => [...q, { ...entry, retries: entry.retries + 1 }]);
        }
      }
    }
    void this.laborSvc.loadHeadcount(this.resourceId());
  }

  // ── Data loading ──────────────────────────────────────────────────────────

  refreshData(): void {
    const id = this.resourceId();
    if (!id) return;
    void this.laborSvc.loadHeadcount(id);
    void this.laborSvc.loadHeadcountHistory(id);
    this.syncResourceMeta();
  }

  private syncResourceMeta(): void {
    const res = this.resourceSvc.resource();
    if (res) {
      this.resourceName.set(res.name ?? res.code);
      this.resourceCode.set(res.code);
    }
  }

  private updateClock(): void {
    this.clockDisplay.set(new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
  }
}
