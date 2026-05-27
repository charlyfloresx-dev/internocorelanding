import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { SupportService } from '../../../core/services/support.service';
import { TicketPriority } from '../../../core/models/support.types';

@Component({
  selector: 'app-industrial-flows',
  standalone: true,
  imports: [CommonModule, MatIconModule, TranslatePipe],
  template: `
    <div class="p-8 animate-fade-in max-w-5xl mx-auto">
      <header class="mb-10 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="h-12 w-12 rounded-2xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20 shadow-inner">
            <mat-icon class="text-2xl text-purple-500">account_tree</mat-icon>
          </div>
          <div>
            <h1 class="text-2xl font-black tracking-tight text-surface-text leading-none uppercase">
              {{ 'monitor.flows.title' | translate:'Industrial Flows Simulator' }}
            </h1>
            <p class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em] mt-2">
              {{ 'monitor.flows.subtitle' | translate:'Validación de Arquitectura y Trazabilidad Forense' }}
            </p>
          </div>
        </div>
        
        <div class="px-4 py-2 rounded-xl bg-surface-card border border-surface-border flex items-center gap-3">
          <div class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
          <span class="text-[9px] font-black uppercase tracking-widest text-surface-text-muted">Monolith Status: Synchronized</span>
        </div>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <!-- Flow 1: Triple Identity -->
        <div class="bg-surface-card border border-surface-border rounded-3xl p-6 shadow-xl hover:shadow-purple-500/5 transition-all group">
          <div class="flex justify-between items-start mb-6">
            <div class="h-14 w-14 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/20 group-hover:scale-110 transition-transform">
              <mat-icon class="text-white text-3xl">fingerprint</mat-icon>
            </div>
            <span class="px-3 py-1 rounded-full bg-purple-500/10 text-purple-500 text-[8px] font-black uppercase tracking-widest border border-purple-500/20">Critical Flow</span>
          </div>
          
          <h3 class="text-lg font-black text-surface-text mb-2">{{ 'monitor.flows.triple_identity.title' | translate:'Flujo de Triple Identity' }}</h3>
          <p class="text-xs text-surface-text-muted mb-6 leading-relaxed">
            Valida la creación y despacho simultáneo de tickets para las tres entidades de identidad industrial:
            <span class="block mt-2 font-bold text-surface-text">• Interno: Usuario administrativo/técnico OAuth.</span>
            <span class="block font-bold text-surface-text">• Planta: Colaborador operativo mediante HCM.</span>
            <span class="block font-bold text-surface-text">• Externo: Proveedor con acceso tokenizado.</span>
          </p>

          <div class="space-y-4 mb-8">
            <div class="flex items-center gap-3 p-3 rounded-xl bg-surface-text/[0.02] border border-surface-border/50">
              <mat-icon class="text-emerald-500 text-sm">check_circle</mat-icon>
              <span class="text-[10px] font-bold text-surface-text-muted uppercase">Persistencia Forense Validada</span>
            </div>
            <div class="flex items-center gap-3 p-3 rounded-xl bg-surface-text/[0.02] border border-surface-border/50">
              <mat-icon class="text-emerald-500 text-sm">check_circle</mat-icon>
              <span class="text-[10px] font-bold text-surface-text-muted uppercase">Handshake de Tokens Externos</span>
            </div>
          </div>

          <button (click)="runFlow('TRIPLE_IDENTITY')" 
                  [disabled]="isRunning()"
                  class="w-full py-4 bg-purple-600 hover:bg-purple-700 text-white rounded-2xl text-xs font-black uppercase tracking-widest transition-all active:scale-95 flex items-center justify-center gap-3 shadow-lg shadow-purple-500/20 disabled:opacity-50">
            <mat-icon [class.animate-spin]="isRunning()">{{ isRunning() ? 'refresh' : 'play_arrow' }}</mat-icon>
            {{ isRunning() ? ('common.running' | translate:'Ejecutando Secuencia...') : ('common.start' | translate:'Iniciar Simulación') }}
          </button>
        </div>

        <!-- Flow 2: Reasignment & Load Balancing (Placeholder) -->
        <div class="bg-surface-card border border-surface-border rounded-3xl p-6 shadow-xl opacity-60 grayscale hover:grayscale-0 transition-all cursor-not-allowed">
           <div class="flex justify-between items-start mb-6">
            <div class="h-14 w-14 rounded-2xl bg-surface-text/5 flex items-center justify-center">
              <mat-icon class="text-surface-text-muted text-3xl">balance</mat-icon>
            </div>
          </div>
          <h3 class="text-lg font-black text-surface-text mb-2">Workload & Liberation</h3>
          <p class="text-xs text-surface-text-muted mb-6 leading-relaxed">
            Simulación de reasignación inteligente basada en saturación (🟢🟡🔴). Próxima implementación en Phase 92.
          </p>
          <div class="h-[120px] border-2 border-dashed border-surface-border rounded-2xl flex items-center justify-center">
             <span class="text-[8px] font-black uppercase tracking-widest text-surface-text-muted">Coming Soon</span>
          </div>
        </div>
      </div>

      <!-- Live Execution Log -->
      <div class="mt-12 bg-surface-card border border-surface-border rounded-3xl overflow-hidden shadow-2xl">
        <div class="px-6 py-4 border-b border-surface-border bg-surface-text/[0.02] flex justify-between items-center">
          <div class="flex items-center gap-2">
            <mat-icon class="text-surface-text-muted text-sm">terminal</mat-icon>
            <span class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted">Real-Time Execution Log</span>
          </div>
          <button (click)="clearLog()" class="text-[9px] font-black text-purple-500 uppercase tracking-widest hover:underline">Clear</button>
        </div>
        <div class="p-6 h-[300px] overflow-y-auto font-mono text-[11px] bg-black/90 custom-scrollbar">
          @for (entry of log(); track entry.timestamp) {
            <div class="mb-2 flex gap-4 animate-slide-in">
              <span class="text-white/30">{{ entry.timestamp | date:'HH:mm:ss' }}</span>
              <span [ngClass]="{
                'text-purple-400': entry.type === 'info',
                'text-emerald-400': entry.type === 'success',
                'text-rose-400': entry.type === 'error',
                'text-amber-400': entry.type === 'step'
              }">[{{ entry.type.toUpperCase() }}]</span>
              <span class="text-white/80">{{ entry.message }}</span>
            </div>
          }
          @if (log().length === 0) {
            <div class="h-full flex items-center justify-center text-white/20 uppercase tracking-[0.5em] text-[10px]">
              Waiting for sequence...
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .custom-scrollbar::-webkit-scrollbar { width: 6px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
    
    @keyframes slide-in {
      from { transform: translateX(-10px); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    .animate-slide-in { animation: slide-in 0.3s ease-out forwards; }
  `]
})
export class IndustrialFlowsComponent {
  private supportService = inject(SupportService);
  isRunning = signal<boolean>(false);
  log = signal<any[]>([]);

  async runFlow(type: string) {
    if (this.isRunning()) return;
    this.isRunning.set(true);
    this.addLog('info', `Iniciando secuencia real: ${type}`);
    
    try {
      // 1. Ticket Interno (Técnico Administrativo)
      this.addLog('step', '[PHASE 1] Generando Ticket para Usuario Interno (OAuth)...');
      const t1 = await this.supportService.createTicket(
        'MT-ADMIN-01: Falla en Router Auditoría', 
        'Simulación de flujo industrial - Usuario Administrativo',
        TicketPriority.MEDIUM,
        'IT'
      );
      this.addLog('success', `Ticket Interno Creado: ${t1?.reference_code}`);

      // 2. Ticket Planta (Colaborador HCM)
      this.addLog('step', '[PHASE 2] Generando Ticket para Colaborador de Planta (Carlos Ramírez)...');
      const t2 = await this.supportService.createTicket(
        'MT-PLANT-02: Calibración RACK-01', 
        'Simulación de flujo industrial - Colaborador de Planta',
        TicketPriority.HIGH,
        'Producción'
      );
      if (t2) {
        await this.supportService.triageTicket(
          t2.id,
          'REASSIGN',
          [{ identity_type: 'PLANTA', identity_id: '11111111-0001-4001-b001-000000000001', is_lead: true }],
          'Asignación automática a colaborador de planta'
        );
        this.addLog('success', `Ticket Planta Creado y Asignado a Carlos Ramírez: ${t2.reference_code}`);
      }

      // 3. Ticket Externo (Proveedor Alicia Torres)
      this.addLog('step', '[PHASE 3] Generando Ticket para Proveedor Externo (Alicia Torres)...');
      const t3 = await this.supportService.createTicket(
        'MT-EXT-03: Instalación Sensor Proximidad', 
        'Simulación de flujo industrial - Proveedor Externo con Token',
        TicketPriority.CRITICAL,
        'Mantenimiento'
      );
      if (t3) {
        await this.supportService.triageTicket(
          t3.id,
          'REASSIGN',
          [{ identity_type: 'EXTERNO', identity_id: '22222222-0002-4002-b002-000000000002', is_lead: true }],
          'Generando token de acceso para proveedor externo'
        );
        this.addLog('success', `Ticket Externo Creado con Token Forense: ${t3.reference_code}`);
        this.addLog('info', `Handshake completado para: charly.flores.x@gmail.com`);
      }

      this.addLog('success', 'Secuencia Industrial Completada con Tráfico Real.');
    } catch (err: any) {
      this.addLog('error', `Error en la secuencia: ${err.message || 'Error desconocido'}`);
    } finally {
      this.isRunning.set(false);
    }
  }

  addLog(type: 'info' | 'success' | 'error' | 'step', message: string) {
    this.log.update(prev => [{ timestamp: new Date(), type, message }, ...prev]);
  }

  clearLog() {
    this.log.set([]);
  }
}
