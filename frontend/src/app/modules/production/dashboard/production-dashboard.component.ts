import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductionService } from '../../../core/services/production.service';
import { LocalDatePipe } from '../../../shared/pipes/local-date.pipe';

@Component({
  selector: 'app-production-dashboard',
  standalone: true,
  imports: [CommonModule, LocalDatePipe],
  template: `
    <div class="p-6 space-y-6 animate-fade-in">
      
      <!-- Header -->
      <div class="flex justify-between items-center mb-8">
        <div>
          <h1 class="text-3xl font-bold text-white tracking-tight">Panel de Producción</h1>
          <p class="text-slate-400">Monitoreo de Planta en Tiempo Real</p>
        </div>
        <div class="flex gap-3">
          <span class="px-3 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 text-xs font-bold uppercase tracking-wider flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> Sistema Online
          </span>
        </div>
      </div>

      <!-- KPI Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        @for (kpi of production.kpis(); track kpi.label) {
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg hover:border-slate-700 transition-all group relative overflow-hidden">
            <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
               <i [class]="kpi.icon + ' text-5xl ' + kpi.iconColor"></i>
            </div>
            
            <div class="flex flex-col">
              <span class="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">{{ kpi.label }}</span>
              <div class="text-3xl font-bold text-white mb-2">{{ kpi.value }}</div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium px-2 py-0.5 rounded bg-slate-800" [ngClass]="kpi.trendColor">
                  {{ kpi.trend }}
                </span>
              </div>
            </div>
          </div>
        }
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- Hourly Production Chart -->
        <div class="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
           <!-- Glassmorphism effect -->
          <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 to-sky-500"></div>
          
          <h3 class="text-white font-bold mb-8 flex items-center gap-2">
            <i class="fa-solid fa-chart-column text-sky-500"></i> Rendimiento por Hora
          </h3>
          
          <div class="h-64 flex items-end justify-between gap-3 px-2">
            @for (stat of production.hourlyProduction(); track stat.hour) {
              <div class="flex-1 flex flex-col items-center gap-3 group">
                <div class="w-full bg-slate-800 rounded-t-xl relative overflow-hidden transition-all hover:bg-slate-750 min-h-[4px]" 
                     [style.height.%]="(stat.actual / 200) * 100">
                  <div class="absolute bottom-0 left-0 w-full bg-sky-500 opacity-20 h-full group-hover:opacity-30 transition-opacity"></div>
                  <div class="absolute bottom-0 left-0 w-full bg-gradient-to-t from-sky-600 to-sky-400 shadow-[0_0_15px_rgba(56,189,248,0.5)]" 
                       [style.height.%]="(stat.actual / stat.goal) * 100"></div>
                </div>
                <span class="text-[10px] text-slate-500 font-mono font-bold">{{ stat.hour }}</span>
              </div>
            }
          </div>
        </div>

        <!-- Recent Downtime Log -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-orange-500"></div>
          
          <h3 class="text-white font-bold mb-8 flex items-center gap-2">
            <i class="fa-solid fa-triangle-exclamation text-red-500"></i> Eventos de Paro
          </h3>
          
          <div class="space-y-4 max-h-[16rem] overflow-y-auto pr-2 custom-scrollbar">
            @for (log of production.recentDowntime(); track log.id) {
              <div class="flex items-center gap-4 p-4 rounded-xl bg-slate-800/40 border border-slate-800 hover:border-slate-700 transition-all">
                <div class="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center text-red-500 shadow-inner">
                  <i class="fa-solid fa-clock-rotate-left"></i>
                </div>
                <div class="flex-1 min-w-0">
                  <h4 class="text-sm font-bold text-white truncate">{{ log.issue_name }}</h4>
                  <p class="text-xs text-slate-500">{{ log.start_time | localDate:'HH:mm' }} &bull; {{ log.duration_minutes }} min</p>
                </div>
                <span class="px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-widest bg-slate-950 text-slate-400 border border-slate-800">
                  {{ log.status }}
                </span>
              </div>
            }
            @if (production.recentDowntime().length === 0) {
              <div class="text-center py-12 flex flex-col items-center justify-center text-slate-600">
                <div class="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
                  <i class="fa-solid fa-check text-2xl text-green-500/30"></i>
                </div>
                <p class="text-sm font-bold">Sin paros reportados</p>
                <p class="text-xs uppercase tracking-tighter">Turno estable</p>
              </div>
            }
          </div>
        </div>

      </div>
    </div>
  `,
  styles: [`
    .custom-scrollbar::-webkit-scrollbar { width: 4px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
  `]
})
export class ProductionDashboardComponent implements OnInit {
  public production = inject(ProductionService);

  ngOnInit() {
    this.production.loadDashboard();
  }
}
