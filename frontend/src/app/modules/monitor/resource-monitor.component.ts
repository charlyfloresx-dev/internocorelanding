import {Component, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatIconModule} from '@angular/material/icon';

@Component({
  selector: 'app-resource-monitor',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="space-y-6 animate-fade-in-up">
      <!-- Header Section -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic"><span class="text-primary glow-text">CELDA-58D</span></h2>
          <p class="text-[10px] text-surface-text-muted font-mono uppercase tracking-widest mt-1">Línea de Producción: CELDA-58D | Turno: Matutino</p>
        </div>
        <div class="flex items-center gap-3">
          <button class="px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg text-[10px] font-bold uppercase tracking-widest hover:bg-emerald-500/20 transition-all">
            Andon Activo
          </button>
          <button class="px-4 py-2 bg-industrial-gray border border-white/10 text-gray-400 rounded-lg text-[10px] font-bold uppercase tracking-widest hover:text-white transition-all">
            Cambio de Modelo
          </button>
        </div>
      </div>

      <!-- Main Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        <!-- Left Panel: Production Info -->
        <div class="lg:col-span-1 space-y-6">
          <div class="industrial-card overflow-hidden glow-border">
            <!-- Tabs Header -->
            <div class="flex border-b border-surface-border">
              <button 
                (click)="activeTab.set('scan')"
                class="flex-1 py-3 text-[9px] font-black uppercase tracking-widest transition-all"
                [class.text-primary]="activeTab() === 'scan'"
                [class.bg-primary/5]="activeTab() === 'scan'"
                [class.text-surface-text-muted]="activeTab() !== 'scan'"
              >
                Escaneo
              </button>
              <button 
                (click)="activeTab.set('planned')"
                class="flex-1 py-3 text-[9px] font-black uppercase tracking-widest transition-all border-l border-surface-border"
                [class.text-primary]="activeTab() === 'planned'"
                [class.bg-primary/5]="activeTab() === 'planned'"
                [class.text-surface-text-muted]="activeTab() !== 'planned'"
              >
                Planeación
              </button>
            </div>

            <div class="p-6">
              @if (activeTab() === 'scan') {
                <div class="space-y-4">
                  <div class="flex flex-col">
                    <span class="text-[9px] text-surface-text-muted uppercase font-bold">ID Operación</span>
                    <span class="text-surface-text font-mono font-bold">428881</span>
                  </div>
                  <div class="flex flex-col">
                    <span class="text-[9px] text-surface-text-muted uppercase font-bold">Part Number</span>
                    <span class="text-surface-text font-mono font-bold text-xs">RRC9002-4801F</span>
                  </div>
                  <div class="pt-4 border-t border-surface-border">
                    <div class="flex justify-between items-end mb-2">
                      <span class="text-[9px] text-surface-text-muted uppercase font-bold">Actual / Plan</span>
                      <span class="text-primary font-black text-2xl glow-text">560 <span class="text-surface-text-muted text-xs">/ 2160</span></span>
                    </div>
                    <div class="progress-bar-industrial"><div class="progress-fill-cyan w-[26%]"></div></div>
                  </div>
                </div>
              } @else {
                <div class="space-y-4">
                  <div class="flex items-center justify-between mb-2">
                    <div class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest">Órdenes del Turno</div>
                    <span class="text-[8px] text-primary font-bold uppercase">Turno: Matutino</span>
                  </div>
                  <div class="space-y-3 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                    @for (order of plannedOrders(); track order.id) {
                      <div class="p-3 rounded-lg bg-surface-text/5 border border-surface-border hover:border-primary/30 transition-all group">
                        <div class="flex justify-between items-start mb-1">
                          <div class="flex flex-col">
                            <span class="text-[10px] text-surface-text font-bold group-hover:text-primary transition-colors">{{ order.id }}</span>
                            <span class="text-[8px] text-surface-text-muted font-mono truncate max-w-[120px]">{{ order.part }}</span>
                          </div>
                          <span class="text-[8px] px-1.5 py-0.5 rounded uppercase font-bold" 
                                [class.bg-emerald-500/20]="order.status === 'En Proceso'"
                                [class.text-emerald-400]="order.status === 'En Proceso'"
                                [class.bg-surface-text/10]="order.status === 'Pendiente'"
                                [class.text-surface-text-muted]="order.status === 'Pendiente'">
                            {{ order.status }}
                          </span>
                        </div>
                        <div class="mt-3 flex justify-between items-end">
                          <div class="flex flex-col">
                            <span class="text-[8px] text-surface-text-muted uppercase font-bold">Cantidad</span>
                            <span class="text-[11px] text-surface-text font-black">{{ order.qty }}</span>
                          </div>
                          <button class="w-6 h-6 rounded bg-primary/10 flex items-center justify-center text-primary opacity-0 group-hover:opacity-100 transition-all">
                            <mat-icon class="text-sm">visibility</mat-icon>
                          </button>
                        </div>
                      </div>
                    }
                  </div>
                </div>
              }
            </div>
          </div>

          <div class="industrial-card p-6">
            <div class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mb-4">Horarios de Descanso</div>
            <div class="space-y-3">
              <div class="flex items-center gap-3 p-2 rounded-lg bg-surface-text/5 border border-surface-border">
                <mat-icon class="text-amber-400 text-sm">coffee</mat-icon>
                <div class="flex flex-col">
                  <span class="text-[9px] text-surface-text-muted uppercase font-bold">Primer Descanso</span>
                  <span class="text-[10px] text-surface-text font-bold">08:35 AM - 09:05 AM</span>
                </div>
              </div>
              <div class="flex items-center gap-3 p-2 rounded-lg bg-surface-text/5 border border-surface-border">
                <mat-icon class="text-amber-400 text-sm">restaurant</mat-icon>
                <div class="flex flex-col">
                  <span class="text-[9px] text-surface-text-muted uppercase font-bold">Comida</span>
                  <span class="text-[10px] text-surface-text font-bold">12:35 PM - 01:05 PM</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Center Panel: Main Chart -->
        <div class="lg:col-span-3 space-y-6">
          <div class="industrial-card p-6">
            <div class="flex items-center justify-between mb-8">
              <h3 class="text-xs font-bold text-surface-text-muted uppercase tracking-widest">Unidades Producidas por Hora</h3>
              <div class="flex items-center gap-4">
                <div class="flex items-center gap-1.5">
                  <div class="w-2 h-2 rounded-full bg-primary shadow-[0_0_5px_rgba(0,229,255,0.5)]"></div>
                  <span class="text-[8px] text-surface-text-muted uppercase font-bold">Actual</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <div class="w-2 h-2 rounded-full bg-amber-500"></div>
                  <span class="text-[8px] text-surface-text-muted uppercase font-bold">Faltante</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <div class="w-2 h-2 rounded-full bg-ic-blue shadow-[0_0_5px_rgba(0,163,255,0.5)]"></div>
                  <span class="text-[8px] text-surface-text-muted uppercase font-bold">Excedente</span>
                </div>
              </div>
            </div>

            <!-- Modern Stacked Bar Chart Simulation -->
            <div class="h-[300px] flex items-end justify-between gap-4 px-4 relative">
              <!-- Grid Lines -->
              <div class="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-5 py-4">
                <div class="h-px bg-white w-full"></div>
                <div class="h-px bg-white w-full"></div>
                <div class="h-px bg-white w-full"></div>
                <div class="h-px bg-white w-full"></div>
                <div class="h-px bg-white w-full"></div>
              </div>

              <!-- Bars -->
              @for (hour of productionData(); track hour.time) {
                <div class="flex-1 flex flex-col items-center gap-3 group relative h-full justify-end">
                  <!-- Stacked Bar Container -->
                  <div class="w-full max-w-[40px] flex flex-col-reverse rounded-t-sm overflow-hidden transition-all duration-500 group-hover:brightness-125">
                    <!-- Actual (Green/Cyan) -->
                    <div 
                      class="w-full bg-primary shadow-[inset_0_0_10px_rgba(255,255,255,0.2)]"
                      [style.height.px]="hour.actual * 1.5"
                    ></div>
                    <!-- Faltante (Amber) -->
                    <div 
                      class="w-full bg-amber-500/80"
                      [style.height.px]="hour.missing * 1.5"
                    ></div>
                    <!-- Excedente (Blue) -->
                    <div 
                      class="w-full bg-ic-blue/80"
                      [style.height.px]="hour.excess * 1.5"
                    ></div>
                  </div>
                  
                  <!-- Goal Line Marker -->
                  <div 
                    class="absolute w-full h-0.5 bg-white/20 border-t border-dashed border-white/40 z-20"
                    [style.bottom.px]="(hour.goal * 1.5) + 32"
                  ></div>

                  <span class="text-[9px] text-surface-text-muted font-bold uppercase tracking-widest">{{ hour.time }}</span>
                  
                  <!-- Tooltip -->
                  <div class="absolute -top-12 left-1/2 -translate-x-1/2 bg-surface-card p-2 rounded border border-surface-border opacity-0 group-hover:opacity-100 transition-opacity z-30 pointer-events-none min-w-[80px] shadow-xl">
                    <div class="text-[8px] text-surface-text-muted uppercase font-bold mb-1">{{ hour.time }}</div>
                    <div class="flex justify-between gap-4">
                      <span class="text-[8px] text-primary font-bold">ACT: {{ hour.actual }}</span>
                      <span class="text-[8px] text-surface-text font-bold">META: {{ hour.goal }}</span>
                    </div>
                  </div>
                </div>
              }
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Meta Acumulada Table -->
            <div class="industrial-card p-6">
              <h3 class="text-xs font-bold text-surface-text-muted uppercase tracking-widest mb-6">Meta Acumulada</h3>
              <div class="overflow-x-auto">
                <table class="w-full text-left">
                  <thead>
                    <tr class="text-[9px] text-surface-text-muted uppercase font-bold border-b border-surface-border">
                      <th class="pb-3">Hora</th>
                      <th class="pb-3">Meta</th>
                      <th class="pb-3">Real</th>
                      <th class="pb-3">Estatus</th>
                    </tr>
                  </thead>
                  <tbody class="text-[10px] text-surface-text-muted">
                    @for (row of tableData(); track row.time) {
                      <tr class="border-b border-surface-border hover:bg-surface-text/5 transition-colors">
                        <td class="py-3 font-mono">{{ row.time }}</td>
                        <td class="py-3 font-bold text-surface-text">{{ row.meta }}</td>
                        <td class="py-3 font-bold" [class.text-primary]="row.real >= row.meta" [class.text-red-400]="row.real < row.meta">{{ row.real }}</td>
                        <td class="py-3">
                          <mat-icon class="text-[12px] h-3 w-3" [class.text-emerald-400]="row.real >= row.meta" [class.text-red-400]="row.real < row.meta">
                            {{ row.real >= row.meta ? 'trending_up' : 'trending_down' }}
                          </mat-icon>
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Support Team & Action Rail -->
            <div class="space-y-6">
              <div class="industrial-card p-6">
                <h3 class="text-xs font-bold text-surface-text-muted uppercase tracking-widest mb-6">Equipo de Soporte</h3>
                <div class="space-y-4">
                  <div class="flex items-center justify-between p-3 rounded-xl bg-surface-text/5 border border-surface-border">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-xs">JR</div>
                      <div class="flex flex-col">
                        <span class="text-[10px] text-surface-text font-bold">Juan Ruiz</span>
                        <span class="text-[8px] text-surface-text-muted uppercase font-bold">HANT - Supervisor</span>
                      </div>
                    </div>
                    <button class="text-primary hover:bg-primary/10 p-1.5 rounded-lg transition-all"><mat-icon class="text-sm">chat</mat-icon></button>
                  </div>
                  <div class="flex items-center justify-between p-3 rounded-xl bg-surface-text/5 border border-surface-border">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-ic-blue/20 flex items-center justify-center text-ic-blue font-bold text-xs">OS</div>
                      <div class="flex flex-col">
                        <span class="text-[10px] text-surface-text font-bold">Oscar Sampayo</span>
                        <span class="text-[8px] text-surface-text-muted uppercase font-bold">HANT - Calidad</span>
                      </div>
                    </div>
                    <button class="text-primary hover:bg-primary/10 p-1.5 rounded-lg transition-all"><mat-icon class="text-sm">chat</mat-icon></button>
                  </div>
                </div>
              </div>

              <div class="industrial-card p-6 bg-gradient-to-br from-surface-card to-primary/5">
                <h3 class="text-xs font-bold text-surface-text-muted uppercase tracking-widest mb-6">Rail de Acciones</h3>
                <div class="grid grid-cols-2 gap-3">
                  <button class="flex flex-col items-center gap-2 p-4 rounded-xl bg-surface-text/5 border border-surface-border hover:border-primary/30 transition-all group">
                    <mat-icon class="text-primary group-hover:scale-110 transition-transform">report_problem</mat-icon>
                    <span class="text-[8px] text-surface-text-muted font-bold uppercase">Incidencia</span>
                  </button>
                  <button class="flex flex-col items-center gap-2 p-4 rounded-xl bg-surface-text/5 border border-surface-border hover:border-primary/30 transition-all group">
                    <mat-icon class="text-primary group-hover:scale-110 transition-transform">history</mat-icon>
                    <span class="text-[8px] text-surface-text-muted font-bold uppercase">Historial</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
  `]
})
export class ResourceMonitorComponent {
  activeTab = signal<'scan' | 'planned'>('scan');

  productionData = signal([
    { time: '06:00', actual: 170, missing: 70, excess: 0, goal: 240 },
    { time: '07:00', actual: 136, missing: 104, excess: 0, goal: 240 },
    { time: '08:00', actual: 96, missing: 44, excess: 101, goal: 140 },
    { time: '09:00', actual: 128, missing: 112, excess: 0, goal: 240 },
    { time: '10:00', actual: 30, missing: 210, excess: 0, goal: 240 },
    { time: '11:00', actual: 0, missing: 0, excess: 0, goal: 0 },
    { time: '12:00', actual: 0, missing: 0, excess: 0, goal: 0 },
    { time: '13:00', actual: 0, missing: 0, excess: 0, goal: 0 },
  ]);

  tableData = signal([
    { time: '07:00', meta: 7, real: 6 },
    { time: '08:00', meta: 11, real: 11 },
    { time: '09:00', meta: 18, real: 17 },
    { time: '10:00', meta: 25, real: 25 },
    { time: '11:00', meta: 32, real: 32 },
    { time: '12:00', meta: 36, real: 35 },
  ]);

  plannedOrders = signal([
    { id: 'PO-9921', part: 'RRC9002-4801F', qty: 2160, status: 'En Proceso' },
    { id: 'PO-9922', part: 'RRC9002-4802F', qty: 1500, status: 'Pendiente' },
    { id: 'PO-9923', part: 'RRC9002-4803F', qty: 1200, status: 'Pendiente' },
    { id: 'PO-9924', part: 'RRC9002-4804F', qty: 800, status: 'Pendiente' },
  ]);
}
