import { Component, inject, signal, computed, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

type SessionStatus = 'NOT_INITIALIZED' | 'QR_READY' | 'AUTHENTICATING' | 'CONNECTED' | 'DISCONNECTED' | 'FAILED';

interface SessionState {
  status: SessionStatus;
  qrCode?: string;
  errorMessage?: string;
}

@Component({
  selector: 'app-whatsapp-gateway',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6 space-y-5">

      <!-- Status Badge -->
      <div class="flex items-center justify-between">
        <span class="text-[9px] font-mono uppercase tracking-widest text-slate-400">Local Gateway · Headless Chromium</span>
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-[10px] font-black uppercase tracking-widest" [ngClass]="statusBadgeClass()">
          <div class="w-1.5 h-1.5 rounded-full" [ngClass]="statusDotClass()"></div>
          <span>{{ statusLabel() }}</span>
        </div>
      </div>

      <!-- ─── PANEL: CONNECTED ─── -->
      @if (session().status === 'CONNECTED') {
        <div class="rounded-2xl border-2 border-emerald-500 bg-emerald-50 p-8 flex items-center gap-6">
          <div class="w-14 h-14 rounded-2xl bg-emerald-500 flex items-center justify-center shrink-0">
            <svg class="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17.498 14.382c-.301-.15-1.767-.867-2.04-.966-.273-.101-.473-.15-.673.15-.197.295-.771.964-.944 1.162-.175.195-.349.21-.646.075-.3-.15-1.263-.465-2.403-1.485-.888-.795-1.484-1.77-1.66-2.07-.174-.3-.019-.465.13-.615.136-.135.301-.345.451-.523.146-.181.194-.301.297-.496.1-.21.049-.375-.025-.524-.075-.15-.672-1.62-.922-2.206-.24-.584-.487-.51-.672-.51-.172-.015-.371-.015-.571-.015-.2 0-.523.074-.797.359-.273.3-1.045 1.02-1.045 2.475s1.07 2.865 1.219 3.075c.149.195 2.105 3.195 5.1 4.485.714.3 1.27.48 1.704.629.714.227 1.365.195 1.88.121.574-.091 1.767-.721 2.016-1.426.255-.705.255-1.29.18-1.425-.074-.135-.27-.21-.57-.345z"/>
              <path d="M20.52 3.449C18.24 1.245 15.24 0 12.045 0 5.463 0 .104 5.334.101 11.893c0 2.096.549 4.14 1.595 5.945L0 24l6.335-1.652c1.746.943 3.71 1.444 5.71 1.447h.006c6.585 0 11.946-5.336 11.949-11.896 0-3.176-1.24-6.165-3.48-8.4zm-8.475 18.312h-.005c-1.775 0-3.514-.477-5.031-1.378l-.361-.214-3.741.975.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.884 9.884z"/>
            </svg>
          </div>
          <div class="flex-1">
            <p class="text-emerald-800 font-black text-lg">Sesión activa y conectada</p>
            <p class="text-emerald-600 text-xs font-mono mt-1">El canal de WhatsApp está listo para enviar notificaciones a los grupos registrados.</p>
          </div>
          <button
            (click)="reinitialize()"
            [disabled]="isLoading()"
            class="px-5 py-2.5 border border-emerald-400 text-emerald-700 text-xs font-black uppercase tracking-widest rounded-xl hover:bg-emerald-100 disabled:opacity-40 transition-colors shrink-0"
          >
            Reiniciar sesión
          </button>
        </div>
      }

      <!-- ─── PANEL: NOT_INITIALIZED / DISCONNECTED / FAILED ─── -->
      @if (['NOT_INITIALIZED', 'DISCONNECTED', 'FAILED'].includes(session().status)) {
        <div class="rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="px-8 py-5 bg-slate-950 flex items-center justify-between">
            <span class="text-white font-black text-sm uppercase tracking-widest">Iniciar sesión WhatsApp</span>
            <span class="text-slate-500 text-[10px] font-mono">LOCAL GATEWAY</span>
          </div>
          <div class="p-8 bg-white space-y-5">
            @if (session().status === 'FAILED') {
              <div class="bg-red-50 border border-red-200 rounded-xl p-4">
                <p class="text-red-700 text-xs font-bold">Error: {{ session().errorMessage || 'Falla desconocida al inicializar la sesión.' }}</p>
              </div>
            }
            @if (session().status === 'DISCONNECTED') {
              <div class="bg-amber-50 border border-amber-200 rounded-xl p-4">
                <p class="text-amber-800 text-xs font-bold">Sesión desconectada. Escanea el QR nuevamente para reconectarte.</p>
              </div>
            }
            <p class="text-slate-600 text-sm">Haz clic en el botón para iniciar el cliente Puppeteer y generar el código QR de vinculación con tu teléfono.</p>
            <button
              (click)="startInitialization()"
              [disabled]="isLoading()"
              class="w-full py-4 bg-slate-950 text-white font-black text-xs uppercase tracking-widest rounded-xl hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              @if (isLoading()) { Iniciando Puppeteer… } @else { Iniciar y generar QR }
            </button>
          </div>
        </div>
      }

      <!-- ─── PANEL: QR_READY ─── -->
      @if (session().status === 'QR_READY') {
        <div class="rounded-2xl border-2 border-amber-400 bg-amber-50 overflow-hidden">
          <div class="px-8 py-5 bg-amber-500 flex items-center gap-3">
            <div class="w-2 h-2 rounded-full bg-white animate-ping"></div>
            <span class="text-white font-black text-sm uppercase tracking-widest">Escanea el código QR con WhatsApp</span>
          </div>
          <div class="p-8 space-y-4">
            <p class="text-amber-800 text-xs font-mono">Abre WhatsApp → Ajustes → Dispositivos vinculados → Vincular dispositivo</p>
            @if (session().qrCode) {
              <div class="flex justify-center">
                <div class="p-4 bg-white rounded-2xl shadow-lg inline-block">
                  <img [src]="session().qrCode" alt="WhatsApp QR Code" class="w-56 h-56 rounded-lg" />
                </div>
              </div>
            } @else {
              <div class="flex justify-center items-center h-64">
                <div class="text-center space-y-3">
                  <div class="w-10 h-10 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
                  <p class="text-amber-700 text-xs font-mono">Generando QR…</p>
                </div>
              </div>
            }
            <p class="text-amber-600 text-[10px] font-mono text-center">El QR se actualiza automáticamente cada 30 segundos</p>
          </div>
        </div>
      }

      <!-- ─── PANEL: AUTHENTICATING ─── -->
      @if (session().status === 'AUTHENTICATING') {
        <div class="rounded-2xl border-2 border-blue-400 bg-blue-50 p-8 flex items-center gap-6">
          <div class="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin shrink-0"></div>
          <div>
            <p class="text-blue-800 font-black text-base">Autenticando con WhatsApp Web…</p>
            <p class="text-blue-600 text-xs font-mono mt-1">El código QR fue escaneado. Esperando confirmación del servidor de WhatsApp.</p>
          </div>
        </div>
      }

      <!-- ─── SECCIÓN: Grupos registrados ─── -->
      @if (session().status === 'CONNECTED') {
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-black text-slate-800 uppercase tracking-widest">Grupos configurados</h3>
            <span class="text-[10px] font-mono text-slate-400">Enrutamiento de notificaciones por área</span>
          </div>
          <div class="rounded-2xl border border-slate-200 p-8 text-center">
            <p class="text-slate-400 text-xs font-mono">Los grupos se configuran desde Admin → Gestión de Grupos.</p>
          </div>
        </div>
      }

      <!-- ─── Controles de estado ─── -->
      <div class="flex items-center justify-between pt-4 border-t border-slate-100">
        <button
          (click)="refreshStatus()"
          [disabled]="isLoading()"
          class="flex items-center gap-2 px-4 py-2 text-xs font-mono text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors disabled:opacity-40"
        >
          <svg class="w-4 h-4" [class.animate-spin]="isLoading()" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Actualizar estado
        </button>
        <span class="text-[10px] font-mono text-slate-300">Puerto interno: 3011 · Gateway: interno-whatsapp-gateway-dev</span>
      </div>

      @if (errorMessage()) {
        <div class="rounded-xl bg-red-50 border border-red-200 px-5 py-4">
          <p class="text-red-700 text-xs font-mono">{{ errorMessage() }}</p>
        </div>
      }

    </div>
  `
})
export class WhatsAppGatewayComponent implements OnDestroy {
  private http = inject(HttpClient);

  session   = signal<SessionState>({ status: 'NOT_INITIALIZED' });
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);

  private pollInterval: ReturnType<typeof setInterval> | null = null;

  statusLabel = computed(() => {
    const map: Record<SessionStatus, string> = {
      NOT_INITIALIZED: 'Sin inicializar',
      QR_READY:        'QR listo',
      AUTHENTICATING:  'Autenticando',
      CONNECTED:       'Conectado',
      DISCONNECTED:    'Desconectado',
      FAILED:          'Error',
    };
    return map[this.session().status] ?? 'Desconocido';
  });

  statusBadgeClass = computed(() => {
    const s = this.session().status;
    if (s === 'CONNECTED')     return 'border-emerald-300 bg-emerald-50 text-emerald-700';
    if (s === 'QR_READY')      return 'border-amber-300 bg-amber-50 text-amber-700';
    if (s === 'AUTHENTICATING') return 'border-blue-300 bg-blue-50 text-blue-700';
    if (s === 'FAILED' || s === 'DISCONNECTED') return 'border-red-300 bg-red-50 text-red-700';
    return 'border-slate-200 bg-slate-50 text-slate-500';
  });

  statusDotClass = computed(() => {
    const s = this.session().status;
    if (s === 'CONNECTED')     return 'bg-emerald-500 animate-pulse';
    if (s === 'QR_READY')      return 'bg-amber-500 animate-ping';
    if (s === 'AUTHENTICATING') return 'bg-blue-500 animate-spin';
    if (s === 'FAILED' || s === 'DISCONNECTED') return 'bg-red-500';
    return 'bg-slate-400';
  });

  constructor() {
    this.refreshStatus();
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  async startInitialization(): Promise<void> {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    try {
      await firstValueFrom(
        this.http.post<any>(`${environment.apiUrl}/api/v1/whatsapp/session/initialize`, {})
      );
      await this.refreshStatus();
      this.startPolling();
    } catch (err: any) {
      this.errorMessage.set(err?.error?.detail ?? 'No se pudo conectar con el gateway. Verifica que el contenedor esté corriendo.');
    } finally {
      this.isLoading.set(false);
    }
  }

  async reinitialize(): Promise<void> {
    await this.startInitialization();
  }

  async refreshStatus(): Promise<void> {
    this.isLoading.set(true);
    try {
      const res = await firstValueFrom(
        this.http.get<any>(`${environment.apiUrl}/api/v1/whatsapp/session/status`)
      );
      const data = res?.data ?? res;
      this.session.set({
        status: data.status ?? 'NOT_INITIALIZED',
        errorMessage: data.errorMessage,
      });

      if (data.status === 'QR_READY') {
        await this.fetchQr();
        this.startPolling();
      } else if (data.status === 'CONNECTED' || data.status === 'FAILED') {
        this.stopPolling();
      }
    } catch {
      // Gateway unreachable — show NOT_INITIALIZED UI, no error banner
      this.session.set({ status: 'NOT_INITIALIZED' });
    } finally {
      this.isLoading.set(false);
    }
  }

  private async fetchQr(): Promise<void> {
    try {
      const res = await firstValueFrom(
        this.http.get<any>(`${environment.apiUrl}/api/v1/whatsapp/session/qr`)
      );
      const data = res?.data ?? res;
      this.session.update(s => ({ ...s, qrCode: data.qrCode }));
    } catch { /* ignore */ }
  }

  private startPolling(): void {
    if (this.pollInterval) return;
    this.pollInterval = setInterval(async () => {
      await this.refreshStatus();
    }, 5000);
  }

  private stopPolling(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }
}
