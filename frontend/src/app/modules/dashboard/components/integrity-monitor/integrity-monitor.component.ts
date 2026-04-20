// temp_future/src/app/modules/dashboard/components/integrity-monitor/integrity-monitor.component.ts
import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardService } from '../../../../core/services/dashboard.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-integrity-monitor',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      
      <!-- Data Health Sphere -->
      <div class="p-6 rounded-3xl border backdrop-blur-md relative overflow-hidden flex flex-col items-center justify-center text-center transition-all
                  bg-slate-50 border-slate-200 dark:bg-slate-900/40 dark:border-white/5">
        <div class="absolute top-0 right-0 p-4 opacity-10 text-slate-400 dark:text-white">
          <mat-icon class="text-6xl">security</mat-icon>
        </div>
        
        <div class="relative w-24 h-24 mb-4">
           <!-- SVG Circle Loader -->
           <svg class="w-full h-full -rotate-90">
             <circle cx="48" cy="48" r="40" fill="transparent" stroke="currentColor" stroke-width="4" class="text-slate-200 dark:text-white/5" />
             <circle cx="48" cy="48" r="40" fill="transparent" stroke="currentColor" stroke-width="6" 
               class="transition-all duration-1000 ease-out"
               [ngClass]="healthColor()"
               stroke-dasharray="251.2"
               [style.stroke-dashoffset]="dashOffset()" />
           </svg>
           <div class="absolute inset-0 flex flex-col items-center justify-center">
             <span class="text-2xl font-black tabular-nums text-slate-900 dark:text-white">{{ metrics().healthPercentage | number:'1.0-0' }}%</span>
             <span class="text-[7px] font-black uppercase tracking-tighter text-slate-500 dark:text-slate-400">Audit Integrity</span>
           </div>
        </div>
        <p class="text-[10px] font-black uppercase tracking-widest italic mb-1 text-slate-900 dark:text-white">Estado de Integridad</p>
        <p class="text-[8px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-500">Protocolo Forense v4.2 Activo</p>
      </div>

      <!-- Quick Stats -->
      <div class="p-6 rounded-3xl border backdrop-blur-md flex flex-col justify-between group overflow-hidden transition-all
                  bg-slate-50 border-slate-200 dark:bg-slate-900/40 dark:border-white/5">
        <div class="flex justify-between items-start mb-4">
          <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">Carga Transaccional (24h)</h4>
          <mat-icon class="text-primary opacity-30 group-hover:opacity-100 transition-opacity">analytics</mat-icon>
        </div>
        <div class="flex items-end gap-3">
          <span class="text-4xl font-black italic tracking-tighter text-slate-900 dark:text-white">{{ metrics().totalValidations }}</span>
          <div class="mb-1">
             <p class="text-[10px] text-emerald-500 font-black">+12.5%</p>
             <p class="text-[8px] font-bold uppercase text-slate-500 dark:text-slate-400">vs ayer</p>
          </div>
        </div>
        <div class="mt-4 flex gap-1 h-1.5 rounded-full overflow-hidden bg-slate-200 dark:bg-white/5">
          <div class="animate-grow-width bg-primary duration-1000" [style.width.%]="65"></div>
          <div class="animate-grow-width bg-emerald-500 duration-1000 delay-200" [style.width.%]="20"></div>
          <div class="animate-grow-width bg-amber-500 duration-1000 delay-500" [style.width.%]="15"></div>
        </div>
      </div>

      <!-- Forensics Breakdown -->
      <div class="p-6 rounded-3xl border backdrop-blur-md flex flex-col justify-between transition-all
                  bg-slate-50 border-slate-200 dark:bg-slate-900/40 dark:border-white/5">
        <h4 class="text-[10px] font-black uppercase tracking-[0.2em] mb-4 text-center md:text-left text-slate-500 dark:text-slate-400">Resultado de Auditoría</h4>
        
        <div class="space-y-3">
          <div class="flex justify-between items-center p-2 rounded-xl border bg-emerald-500/5 border-emerald-500/10">
            <span class="text-[9px] text-emerald-600 dark:text-emerald-400 font-black uppercase tracking-widest">Validado (SSOT)</span>
            <span class="text-xs font-black tabular-nums text-slate-900 dark:text-white">{{ metrics().successful }}</span>
          </div>
          <div class="flex justify-between items-center p-2 rounded-xl border transition-all" 
               [ngClass]="metrics().discrepancies > 0 ? 'bg-red-500/10 border-red-500/20 animate-pulse' : 'bg-slate-100 border-slate-200 dark:bg-white/5 dark:border-white/5'">
            <span class="text-[9px] font-black uppercase tracking-widest"
                  [ngClass]="metrics().discrepancies > 0 ? 'text-red-500' : 'text-slate-500'">Discrepancias</span>
            <span class="text-xs font-black tabular-nums"
                  [ngClass]="metrics().discrepancies > 0 ? 'text-red-500' : 'text-slate-900 dark:text-white'">{{ metrics().discrepancies }}</span>
          </div>
        </div>
      </div>

    </div>
  `
})
export class IntegrityMonitorComponent {
  dashboard = inject(DashboardService);
  metrics = this.dashboard.integrityMetrics;

  dashOffset = computed(() => {
    const percentage = this.metrics().healthPercentage;
    const circumference = 2 * Math.PI * 40; // r=40
    return circumference - (percentage / 100) * circumference;
  });

  healthColor = computed(() => {
    const h = this.metrics().healthPercentage;
    if (h > 95) return 'text-neon-green shadow-[0_0_15px_#00ff9d]';
    if (h > 80) return 'text-amber-500';
    return 'text-red-500';
  });
}
