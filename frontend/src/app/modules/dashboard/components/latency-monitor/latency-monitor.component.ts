// temp_future/src/app/modules/dashboard/components/latency-monitor/latency-monitor.component.ts
import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardService } from '../../../../core/services/dashboard.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-latency-monitor',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="bg-slate-900/40 border border-white/5 p-6 rounded-3xl backdrop-blur-md relative overflow-hidden h-full flex flex-col">
      <!-- Glow Effect -->
      <div class="absolute -top-24 -left-24 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl"></div>
      
      <div class="flex justify-between items-start mb-6 relative z-10">
        <div>
          <h4 class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-1">Telemetría de Red</h4>
          <p class="text-[9px] text-neon-cyan font-bold uppercase tracking-widest">Infraestructura ECR / App Runner</p>
        </div>
        <div class="px-2 py-1 rounded bg-black/40 border border-white/5 flex items-center gap-2">
           <div class="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_5px_#00e5ff]"></div>
           <span class="text-[9px] text-white font-black tabular-nums">{{ dashboard.averageLatency() }}ms</span>
        </div>
      </div>

      <!-- Neon Oscilloscope -->
      <div class="flex-1 relative flex items-end gap-1 px-2 border-b border-l border-white/5 pb-2">
        <!-- Grid lines -->
        <div class="absolute inset-0 pointer-events-none flex flex-col justify-between opacity-5">
          <div class="border-t border-white w-full"></div>
          <div class="border-t border-white w-full"></div>
          <div class="border-t border-white w-full"></div>
        </div>

        @for (point of dashboard.latencyHistory(); track $index) {
          <div class="flex-1 min-w-[4px] bg-gradient-to-t from-cyan-500/10 to-cyan-400 group relative transition-all duration-300"
               [style.height.%]="getHeight(point.value)">
            <!-- Dot -->
            <div class="absolute -top-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-white rounded-full shadow-[0_0_8px_#fff] opacity-0 group-hover:opacity-100 transition-opacity"></div>
            
            <!-- Tooltip -->
            <div class="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-ic-dark border border-white/10 rounded text-[8px] text-white font-bold opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20">
              {{ point.value }}ms
            </div>
          </div>
        } @empty {
          <div class="absolute inset-0 flex items-center justify-center opacity-10">
            <mat-icon class="text-4xl animate-pulse">radar</mat-icon>
          </div>
        }
      </div>

      <!-- ECR Health Status -->
      <div class="mt-6 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400">
            <mat-icon class="!text-lg">cloud_done</mat-icon>
          </div>
          <div>
            <p class="text-[8px] text-slate-500 font-black uppercase">AWS Region</p>
            <p class="text-[10px] text-white font-black tracking-tighter uppercase">us-east-1</p>
          </div>
        </div>
        
        <div class="text-right">
           <p class="text-[8px] text-slate-500 font-black uppercase mb-1">App Runner Health</p>
           <div class="px-2 py-0.5 rounded-full bg-neon-green/10 border border-neon-green/20">
             <span class="text-[8px] text-neon-green font-black uppercase tracking-widest">Healthy / Stable</span>
           </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    @keyframes bar-grow {
      from { transform: scaleY(0); }
      to { transform: scaleY(1); }
    }
    .animate-bar-grow {
      transform-origin: bottom;
      animation: bar-grow 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
  `]
})
export class LatencyMonitorComponent {
  dashboard = inject(DashboardService);

  getHeight(value: number): number {
    // scale 0-1000ms to 0-100%
    const height = (value / 500) * 100; // 500ms as baseline for "max" visual height
    return Math.min(Math.max(height, 5), 100);
  }
}
