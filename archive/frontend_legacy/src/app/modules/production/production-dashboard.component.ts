import { Component, inject, OnInit, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductionDataService } from '@services/production-data.service';

@Component({
  selector: 'app-production-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      
      <!-- Header -->
      <div class="flex justify-between items-center mb-8">
        <div>
          <h1 class="text-3xl font-bold text-white tracking-tight">Production Dashboard</h1>
          <p class="text-slate-400">Real-time monitoring of Line 1</p>
        </div>
        <div class="flex gap-3">
          <span class="px-3 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 text-xs font-bold uppercase tracking-wider flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> Live
          </span>
        </div>
      </div>

      <!-- KPI Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        @for (kpi of data.kpis(); track kpi.label) {
          <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg hover:border-slate-700 transition-all group">
            <div class="flex justify-between items-start mb-2">
              <span class="text-slate-400 text-xs font-bold uppercase tracking-wider">{{ kpi.label }}</span>
              <i [class]="kpi.icon + ' ' + kpi.iconColor + ' text-lg opacity-80 group-hover:scale-110 transition-transform'"></i>
            </div>
            <div class="text-2xl font-bold text-white mb-1">{{ kpi.value }}</div>
            <div class="text-xs font-medium" [ngClass]="kpi.trendColor">
              {{ kpi.trend }}
            </div>
          </div>
        }
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- Hourly Production Chart (Mock Visual) -->
        <div class="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <h3 class="text-white font-bold mb-6 flex items-center gap-2">
            <i class="fa-solid fa-chart-column text-sky-500"></i> Hourly Output
          </h3>
          
          <div class="h-64 flex items-end justify-between gap-2 px-2">
            @for (stat of data.hourlyProduction(); track stat.hour) {
              <div class="flex-1 flex flex-col items-center gap-2 group">
                <div class="w-full bg-slate-800 rounded-t-lg relative overflow-hidden transition-all hover:bg-slate-700" 
                     [style.height.%]="(stat.actual / 120) * 100">
                  <div class="absolute bottom-0 left-0 w-full bg-sky-500/20 h-full group-hover:bg-sky-500/30 transition-colors"></div>
                  <div class="absolute bottom-0 left-0 w-full bg-sky-500" [style.height.%]="(stat.actual / stat.goal) * 100"></div>
                </div>
                <span class="text-[10px] text-slate-500 font-mono">{{ stat.hour }}</span>
              </div>
            }
          </div>
        </div>

        <!-- Recent Downtime Log -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <h3 class="text-white font-bold mb-6 flex items-center gap-2">
            <i class="fa-solid fa-triangle-exclamation text-red-500"></i> Recent Issues
          </h3>
          
          <div class="space-y-4">
            @for (log of data.downtimeLogs(); track log.id) {
              <div class="flex items-center gap-4 p-3 rounded-lg bg-slate-800/50 border border-slate-800 hover:border-slate-700 transition-colors">
                <div class="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
                  <i class="fa-solid fa-wrench"></i>
                </div>
                <div class="flex-1 min-w-0">
                  <h4 class="text-sm font-bold text-white truncate">{{ log.issueName }}</h4>
                  <p class="text-xs text-slate-400">{{ log.startTime | date:'shortTime' }} &bull; {{ log.durationMinutes }} min</p>
                </div>
                <span class="px-2 py-1 rounded text-[10px] font-bold uppercase bg-slate-700 text-slate-300">
                  {{ log.status }}
                </span>
              </div>
            }
            @if (data.downtimeLogs().length === 0) {
              <div class="text-center py-8 text-slate-500">
                <i class="fa-solid fa-check-circle text-2xl mb-2 text-green-500/50"></i>
                <p class="text-sm">No recent downtime events.</p>
              </div>
            }
          </div>
        </div>

      </div>
    </div>
  `
})
export class ProductionDashboardComponent implements OnInit {
  public data = inject(ProductionDataService);

  constructor() {
    // Optional: React to loading state
    effect(() => {
      // console.log('Dashboard Loading:', this.data.loading());
    });
  }

  ngOnInit() {
    this.data.loadDashboard();
  }
}