import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { toSignal, takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { interval } from 'rxjs';
import { map } from 'rxjs/operators';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { GodModeStore } from '../../core/stores/god-mode.store';

@Component({
  selector: 'app-system-control',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-12 space-y-10 animate-fade-in bg-white min-h-screen">

      <!-- Header -->
      <div>
        <h2 class="text-4xl font-black text-slate-950 uppercase tracking-tighter italic">Control del Sistema</h2>
        <p class="text-slate-500 text-[10px] font-mono uppercase tracking-widest mt-1">Consola de Acceso Break-Glass · Solo personal de infraestructura</p>
      </div>

      <!-- ─── BANNER: Sesión activa ─── -->
      @if (store.isActive()) {
        <div class="rounded-2xl border-2 border-red-500 bg-red-600 text-white relative overflow-hidden">
          <div class="absolute inset-0 bg-red-400/20 animate-pulse pointer-events-none"></div>
          <div class="relative z-10 px-8 py-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="space-y-1">
              <div class="flex items-center gap-3">
                <div class="w-3 h-3 rounded-full bg-white animate-ping"></div>
                <span class="text-lg font-black uppercase tracking-widest">SESIÓN DE EMERGENCIA ACTIVA</span>
                <span class="text-2xl font-mono font-black tabular-nums ml-2">{{ formattedCountdown() }}</span>
              </div>
              <p class="text-red-100 text-xs font-mono">JTI: {{ store.jti() }}</p>
              <p class="text-red-200 text-xs">Acceso completo a todas las empresas. Cada acción está siendo auditada permanentemente.</p>
            </div>
            <button
              (click)="closeSession()"
              class="shrink-0 px-6 py-3 bg-white text-red-700 font-black text-xs uppercase tracking-widest rounded-xl hover:bg-red-50 transition-colors"
            >
              Cerrar Sesión de Emergencia
            </button>
          </div>
        </div>
      }

      <!-- ─── PANEL: Consola de emergencia (solo cuando inactivo) ─── -->
      @if (!store.isActive()) {
        <div class="rounded-2xl border border-slate-200 shadow-sm overflow-hidden max-w-2xl">

          <!-- Cabecera del panel -->
          <div class="px-8 py-5 bg-slate-950 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span class="text-white font-black text-sm uppercase tracking-widest">Consola de Emergencia</span>
              <span class="px-2 py-0.5 bg-red-600 text-white text-[9px] font-black uppercase tracking-widest rounded">Crítico</span>
            </div>
            <span class="text-slate-500 text-[10px] font-mono">BREAK-GLASS ACCESS</span>
          </div>

          <!-- Cuerpo del panel -->
          <div class="p-8 bg-white space-y-6">

            <!-- Advertencia -->
            <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-1">
              <p class="text-amber-800 text-xs font-bold">Esta acción eleva tus privilegios globalmente sobre todas las empresas del sistema.</p>
              <p class="text-amber-700 text-xs">Cada uso queda registrado permanentemente en el audit trail de seguridad con tu IP y agente de usuario.</p>
            </div>

            <!-- Panel bloqueado -->
            @if (store.isLocked()) {
              <div class="bg-red-50 border border-red-300 rounded-xl p-6 text-center space-y-2">
                <p class="text-red-700 font-black text-sm uppercase tracking-widest">Panel bloqueado — 3 intentos fallidos</p>
                <p class="text-red-500 text-xs font-mono">Recarga la página para reiniciar el contador local.<br>El rate limit del backend aplica por IP durante 1 hora.</p>
              </div>
            }

            <!-- Formulario (visible cuando NO bloqueado) -->
            @if (!store.isLocked()) {

              <!-- Input de clave maestra -->
              <div class="space-y-2">
                <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest block">Clave Maestra</label>
                <div class="flex gap-2">
                  <input
                    [type]="showKey() ? 'text' : 'password'"
                    [value]="masterKeyInput()"
                    (input)="masterKeyInput.set($any($event.target).value)"
                    placeholder="Ingresa CORE_ADMIN_MASTER_KEY"
                    autocomplete="off"
                    [disabled]="isLoading()"
                    class="flex-1 px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent disabled:opacity-50"
                  />
                  <button
                    type="button"
                    (click)="showKey.set(!showKey())"
                    class="px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors text-lg"
                    title="Mostrar / ocultar clave"
                  >
                    {{ showKey() ? '🙈' : '👁' }}
                  </button>
                </div>

                @if (store.attempts() > 0) {
                  <p class="text-red-500 text-xs font-mono">
                    ⚠ {{ store.attempts() }}/3 intentos fallidos — clave incorrecta
                  </p>
                }
              </div>

              <!-- Avisos -->
              <div class="grid grid-cols-2 gap-3">
                <div class="flex items-start gap-2 text-xs text-slate-500 font-mono">
                  <span class="text-amber-500 mt-0.5">⚠</span>
                  <span>3 intentos máximos por sesión de navegador</span>
                </div>
                <div class="flex items-start gap-2 text-xs text-slate-500 font-mono">
                  <span class="text-amber-500 mt-0.5">⚠</span>
                  <span>Sesión dura exactamente 5 minutos</span>
                </div>
              </div>

              <!-- Estado: confirmación doble -->
              @if (isConfirming()) {
                <div class="bg-red-50 border-2 border-red-400 rounded-xl p-5 space-y-3">
                  <p class="text-red-700 font-black text-sm">¿Confirmas la elevación de privilegios globales?</p>
                  <p class="text-red-600 text-xs">Esta acción es irreversible. El registro incluye IP, agente de usuario y JTI únicos.</p>
                  <div class="flex gap-3">
                    <button
                      (click)="confirmActivation()"
                      [disabled]="isLoading()"
                      class="flex-1 py-3 bg-red-600 text-white font-black text-xs uppercase tracking-widest rounded-xl hover:bg-red-700 disabled:opacity-50 transition-colors"
                    >
                      @if (isLoading()) { Activando… } @else { Confirmar Activación }
                    </button>
                    <button
                      (click)="isConfirming.set(false)"
                      [disabled]="isLoading()"
                      class="flex-1 py-3 bg-slate-100 text-slate-700 font-black text-xs uppercase tracking-widest rounded-xl hover:bg-slate-200 disabled:opacity-50 transition-colors"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              } @else {
                <button
                  (click)="requestConfirmation()"
                  [disabled]="!masterKeyInput().trim() || isLoading()"
                  class="w-full py-4 bg-slate-950 text-white font-black text-xs uppercase tracking-widest rounded-xl hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Activar Sesión de Emergencia
                </button>
              }

            }
          </div>
        </div>
      }

    </div>
  `
})
export class SystemControlComponent {
  protected store = inject(GodModeStore);
  private http    = inject(HttpClient);

  masterKeyInput = signal('');
  showKey        = signal(false);
  isConfirming   = signal(false);
  isLoading      = signal(false);

  // Tick each second to refresh secondsRemaining computed from the store
  private readonly tick = toSignal(
    interval(1000).pipe(
      map(() => this.store.secondsRemaining()),
      takeUntilDestroyed()
    ),
    { initialValue: 0 }
  );

  formattedCountdown = computed(() => {
    const secs = Number(this.tick() ?? 0);
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  });

  requestConfirmation(): void {
    if (this.store.isLocked() || !this.masterKeyInput().trim()) return;
    this.isConfirming.set(true);
  }

  async confirmActivation(): Promise<void> {
    if (this.store.isLocked()) return;
    this.isLoading.set(true);

    try {
      const response = await firstValueFrom(
        this.http.post<any>(
          `${environment.apiUrl}/api/v1/admin/elevate`,
          {},
          { headers: { 'X-Admin-Master-Key': this.masterKeyInput() } }
        )
      );
      this.store.activate(
        response.data.access_token,
        response.data.metadata.jti,
        response.data.expires_in
      );
      this.masterKeyInput.set('');
      this.isConfirming.set(false);
    } catch {
      this.store.recordFailedAttempt();
      this.isConfirming.set(false);
    } finally {
      this.isLoading.set(false);
    }
  }

  closeSession(): void {
    const jti = this.store.jti();
    this.store.clear();  // limpia memoria inmediatamente

    // Revocación server-side — fire-and-forget (el token de todas formas expirará)
    if (jti) {
      this.http.delete(`${environment.apiUrl}/api/v1/admin/elevate/${jti}`).subscribe({
        error: () => { /* token ya expiró o Redis no disponible — aceptable */ }
      });
    }
  }
}
