// temp_future/src/app/modules/dashboard/components/usage-monitor/usage-monitor.component.ts
import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardService } from '../../../../core/services/dashboard.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-usage-monitor',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      
      <!-- Operation Quota & Throughput -->
      <div class="p-6 rounded-3xl border backdrop-blur-md transition-all
                  bg-slate-50 border-slate-200 dark:bg-slate-900/40 dark:border-white/5">
        <div class="flex justify-between items-start mb-6">
          <div>
            <h4 class="text-[10px] font-black uppercase tracking-[0.2em] mb-1 text-slate-500 dark:text-slate-400">Cuota de Operaciones</h4>
            <p class="text-[9px] text-emerald-600 dark:text-emerald-400 font-bold uppercase tracking-widest italic">Plan Enterprise / Multi-tenant</p>
          </div>
          <mat-icon class="text-emerald-500 opacity-20">speed</mat-icon>
        </div>

        <div class="space-y-6">
          <!-- Transacciones -->
          <div>
            <div class="flex justify-between text-[10px] font-black uppercase mb-2">
              <span class="text-slate-900 dark:text-white">Transacciones Ledger</span>
              <span class="text-emerald-600 dark:text-emerald-400 font-black tabular-nums">{{ metrics().requestCount }} / 500</span>
            </div>
            <div class="h-2 rounded-full overflow-hidden border shadow-inner bg-slate-200 dark:bg-white/5 border-slate-200 dark:border-white/5">
              <div class="h-full bg-gradient-to-r from-emerald-500/40 to-emerald-500 transition-all duration-1000"
                   [style.width.%]="metrics().operationQuota"></div>
            </div>
          </div>

          <!-- Payload Data -->
          <div>
            <div class="flex justify-between text-[10px] font-black uppercase mb-2">
              <span class="text-slate-900 dark:text-white">Ancho de Banda (JSON)</span>
              <span class="text-primary dark:text-primary font-black tabular-nums">{{ metrics().totalPayloadSize }} KB</span>
            </div>
            <div class="h-2 rounded-full overflow-hidden border shadow-inner bg-slate-200 dark:bg-white/5 border-slate-200 dark:border-white/5">
               <div class="h-full bg-gradient-to-r from-primary/40 to-primary transition-all duration-1000"
                    [style.width.%]="Math.min(100, metrics().totalPayloadSize / 10)"></div>
            </div>
          </div>
        </div>

        <div class="mt-8 pt-6 border-t flex justify-between items-center text-[10px] font-black border-slate-200 dark:border-white/5">
          <p class="text-slate-500 uppercase tracking-widest">Estado del Plan</p>
          <div class="flex items-center gap-2">
            <span class="text-slate-900 dark:text-white">ESTABLE</span>
            <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          </div>
        </div>
      </div>

      <!-- Activity Heatmap -->
      <div class="p-6 rounded-3xl border backdrop-blur-md flex flex-col transition-all
                  bg-slate-50 border-slate-200 dark:bg-slate-900/40 dark:border-white/5">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h4 class="text-[10px] font-black uppercase tracking-[0.2em] mb-1 text-slate-500 dark:text-slate-400">Puntos de Calor</h4>
            <p class="text-[9px] text-amber-600 dark:text-amber-500 font-bold uppercase tracking-widest">Actividad Transaccional / 24h</p>
          </div>
          <mat-icon class="text-amber-500 opacity-20">grid_on</mat-icon>
        </div>

        <div class="flex-1 flex flex-col gap-1 p-2 rounded-xl overflow-hidden bg-slate-200/50 dark:bg-black/20">
           @for (day of metrics().activityHeatmap; track $index) {
             <div class="flex gap-1 h-full">
                @for (hour of day; track $index) {
                  <div class="flex-1 min-w-[4px] rounded-sm transition-colors duration-500 group relative shadow-sm border border-transparent dark:border-white/5"
                       [style.background-color]="getHeatColor(hour)">
                    <!-- Tooltip -->
                    <div class="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 border rounded text-[7px] font-bold opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20 pointer-events-none
                                bg-slate-900 border-white/10 text-white
                                dark:bg-slate-800 dark:border-white/10">
                      {{ hour }} Op
                    </div>
                  </div>
                }
             </div>
           }
        </div>
        
        <div class="mt-4 flex justify-between text-[8px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-500">
           <span>00:00</span>
           <span>Picos de Actividad</span>
           <span>23:59</span>
        </div>
      </div>

    </div>
  `
})
export class UsageMonitorComponent {
  dashboard = inject(DashboardService);
  metrics = this.dashboard.usageMetrics;
  Math = Math;

  getHeatColor(value: number): string {
    if (value === 0) return 'rgba(255,255,255,0.03)';
    if (value < 5)   return 'rgba(0, 255, 157, 0.2)'; // Neon Green Low
    if (value < 10)  return 'rgb(0, 255, 157)';      // Neon Green Med
    return 'rgb(245, 158, 11)';                       // Amber High
  }
}
