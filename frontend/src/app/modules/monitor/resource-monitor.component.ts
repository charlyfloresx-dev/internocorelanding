import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { ResourceService } from '../../core/services/resource.service';

@Component({
  selector: 'app-resource-monitor',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="space-y-6 animate-fade-in-up">

      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          @if (svc.isLoading()) {
            <div class="h-7 w-40 bg-surface-text/10 animate-pulse rounded mb-2"></div>
            <div class="h-3 w-64 bg-surface-text/5 animate-pulse rounded"></div>
          } @else {
            <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">
              <span class="text-primary glow-text">{{ resourceCode() }}</span>
            </h2>
            <p class="text-[10px] text-surface-text-muted font-mono uppercase tracking-widest mt-1">
              Línea de Producción: {{ resourceCode() }}
              @if (svc.shiftName() && svc.shiftName() !== '—') {
                | Turno: {{ svc.shiftName() }}
              }
            </p>
          }
        </div>
        <div class="flex items-center gap-3">
          <button
            class="px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all border"
            [class.bg-emerald-500/10]="hasActiveWO()"
            [class.border-emerald-500/30]="hasActiveWO()"
            [class.text-emerald-400]="hasActiveWO()"
            [class.bg-surface-text/5]="!hasActiveWO()"
            [class.border-surface-border]="!hasActiveWO()"
            [class.text-surface-text-muted]="!hasActiveWO()"
          >
            {{ hasActiveWO() ? 'Andon Activo' : 'Sin Andon' }}
          </button>
          <button
            (click)="goBack()"
            class="px-4 py-2 bg-industrial-gray border border-white/10 text-gray-400 rounded-lg
                   text-[10px] font-bold uppercase tracking-widest hover:text-white transition-all"
          >
            ← Recursos
          </button>
        </div>
      </div>

      <!-- Main Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">

        <!-- Left Panel -->
        <div class="lg:col-span-1 space-y-6">
          <div class="industrial-card overflow-hidden glow-border">

            <!-- Tabs -->
            <div class="flex border-b border-surface-border">
              <button
                (click)="activeTab.set('scan')"
                class="flex-1 py-3 text-[9px] font-black uppercase tracking-widest transition-all"
                [class.text-primary]="activeTab() === 'scan'"
                [class.bg-primary/5]="activeTab() === 'scan'"
                [class.text-surface-text-muted]="activeTab() !== 'scan'"
              >Escaneo</button>
              <button
                (click)="activeTab.set('planned')"
                class="flex-1 py-3 text-[9px] font-black uppercase tracking-widest transition-all border-l border-surface-border"
                [class.text-primary]="activeTab() === 'planned'"
                [class.bg-primary/5]="activeTab() === 'planned'"
                [class.text-surface-text-muted]="activeTab() !== 'planned'"
              >Planeación</button>
            </div>

            <div class="p-6">
              @if (activeTab() === 'scan') {
                @if (svc.isLoadingGraphic()) {
                  <div class="space-y-3">
                    <div class="h-4 w-24 bg-surface-text/10 animate-pulse rounded"></div>
                    <div class="h-6 w-32 bg-surface-text/10 animate-pulse rounded"></div>
                    <div class="h-3 w-full bg-surface-text/5 animate-pulse rounded mt-4"></div>
                  </div>
                } @else if (svc.activeWO()) {
                  <div class="space-y-4">
                    <div class="flex flex-col">
                      <span class="text-[9px] text-surface-text-muted uppercase font-bold">ID Operación</span>
                      <span class="text-surface-text font-mono font-bold">{{ svc.activeWO()!.order_number }}</span>
                    </div>
                    <div class="flex flex-col">
                      <span class="text-[9px] text-surface-text-muted uppercase font-bold">Part Number</span>
                      <span class="text-surface-text font-mono font-bold text-xs">{{ svc.activeWO()!.item_code }}</span>
                    </div>
                    <div class="pt-4 border-t border-surface-border">
                      <div class="flex justify-between items-end mb-2">
                        <span class="text-[9px] text-surface-text-muted uppercase font-bold">Actual / Plan</span>
                        <span class="text-primary font-black text-2xl glow-text">
                          {{ svc.activeWO()!.manufactured_quantity }}
                          <span class="text-surface-text-muted text-xs">/ {{ svc.activeWO()!.order_quantity }}</span>
                        </span>
                      </div>
                      <div class="progress-bar-industrial">
                        <div class="progress-fill-cyan" [style.width.%]="svc.progressPct()"></div>
                      </div>
                    </div>
                  </div>
                } @else {
                  <div class="text-center py-6">
                    <mat-icon class="text-surface-text-muted text-3xl mb-2">pause_circle</mat-icon>
                    <p class="text-[10px] text-surface-text-muted uppercase font-bold">Sin orden activa</p>
                  </div>
                }
              } @else {
                <div class="space-y-4">
                  <div class="flex items-center justify-between mb-2">
                    <div class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest">Órdenes del Turno</div>
                    @if (svc.shiftName() && svc.shiftName() !== '—') {
                      <span class="text-[8px] text-primary font-bold uppercase">{{ svc.shiftName() }}</span>
                    }
                  </div>
                  @if (svc.plannedWOs().length === 0) {
                    <p class="text-[10px] text-surface-text-muted text-center py-4 uppercase">Sin órdenes planeadas</p>
                  } @else {
                    <div class="space-y-3 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                      @for (wo of svc.plannedWOs(); track wo.work_order_id) {
                        <div class="p-3 rounded-lg bg-surface-text/5 border border-surface-border hover:border-primary/30 transition-all group">
                          <div class="flex justify-between items-start mb-1">
                            <div class="flex flex-col">
                              <span class="text-[10px] text-surface-text font-bold group-hover:text-primary transition-colors">{{ wo.order_number }}</span>
                              <span class="text-[8px] text-surface-text-muted font-mono truncate max-w-[120px]">{{ wo.item_code }}</span>
                            </div>
                            <span class="text-[8px] px-1.5 py-0.5 rounded uppercase font-bold"
                                  [class.bg-emerald-500/20]="wo.status === 'IN_PROGRESS'"
                                  [class.text-emerald-400]="wo.status === 'IN_PROGRESS'"
                                  [class.bg-surface-text/10]="wo.status !== 'IN_PROGRESS'"
                                  [class.text-surface-text-muted]="wo.status !== 'IN_PROGRESS'">
                              {{ wo.status === 'IN_PROGRESS' ? 'En Proceso' : 'Pendiente' }}
                            </span>
                          </div>
                          <div class="mt-3 flex flex-col">
                            <span class="text-[8px] text-surface-text-muted uppercase font-bold">Cantidad</span>
                            <span class="text-[11px] text-surface-text font-black">{{ wo.planned_quantity }}</span>
                          </div>
                        </div>
                      }
                    </div>
                  }
                </div>
              }
            </div>
          </div>

          <!-- Breaks -->
          <div class="industrial-card p-6">
            <div class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mb-4">
              Horarios de Descanso
            </div>
            @if (svc.isLoadingGraphic()) {
              <div class="space-y-2">
                <div class="h-10 bg-surface-text/5 animate-pulse rounded-lg"></div>
                <div class="h-10 bg-surface-text/5 animate-pulse rounded-lg"></div>
              </div>
            } @else if (svc.breaks().length === 0) {
              <p class="text-[10px] text-surface-text-muted uppercase">Sin descansos configurados</p>
            } @else {
              <div class="space-y-3">
                @for (b of svc.breaks(); track b.code) {
                  <div class="flex items-center gap-3 p-2 rounded-lg bg-surface-text/5 border border-surface-border">
                    <mat-icon class="text-amber-400 text-sm">
                      {{ b.break_type === 'MEAL' ? 'restaurant' : 'coffee' }}
                    </mat-icon>
                    <div class="flex flex-col">
                      <span class="text-[9px] text-surface-text-muted uppercase font-bold">{{ b.label }}</span>
                      <span class="text-[10px] text-surface-text font-bold">{{ b.start_time }} - {{ b.end_time }}</span>
                    </div>
                  </div>
                }
              </div>
            }
          </div>
        </div>

        <!-- Right 3 cols -->
        <div class="lg:col-span-3 space-y-6">

          <!-- Chart -->
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

            @if (svc.isLoadingGraphic()) {
              <div class="h-[300px] flex items-end justify-between gap-4 px-4">
                @for (h of [1,2,3,4,5,6,7,8]; track h) {
                  <div class="flex-1 bg-surface-text/10 animate-pulse rounded-t-sm"
                       [style.height.px]="60 + (h * 18)"></div>
                }
              </div>
            } @else if (svc.hourlySlots().length === 0) {
              <div class="h-[300px] flex flex-col items-center justify-center gap-3 text-surface-text-muted">
                <mat-icon class="text-4xl">bar_chart</mat-icon>
                <p class="text-xs uppercase font-bold tracking-widest">Sin datos de producción para hoy</p>
              </div>
            } @else {
              <div class="h-[300px] flex items-end justify-between gap-4 px-4 relative">
                <div class="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-5 py-4">
                  @for (_ of [1,2,3,4,5]; track _) {
                    <div class="h-px bg-white w-full"></div>
                  }
                </div>
                @for (slot of svc.hourlySlots(); track slot.time) {
                  <div class="flex-1 flex flex-col items-center gap-3 group relative h-full justify-end">
                    <div class="w-full max-w-[40px] flex flex-col-reverse rounded-t-sm overflow-hidden transition-all duration-500 group-hover:brightness-125">
                      <div class="w-full bg-primary shadow-[inset_0_0_10px_rgba(255,255,255,0.2)]"
                           [style.height.px]="slot.actual * 1.5"></div>
                      <div class="w-full bg-amber-500/80" [style.height.px]="slot.missing * 1.5"></div>
                      <div class="w-full bg-ic-blue/80" [style.height.px]="slot.excess * 1.5"></div>
                    </div>
                    <div class="absolute w-full h-0.5 bg-white/20 border-t border-dashed border-white/40 z-20"
                         [style.bottom.px]="(slot.goal * 1.5) + 32"></div>
                    <span class="text-[9px] text-surface-text-muted font-bold uppercase tracking-widest">{{ slot.time }}</span>
                    <div class="absolute -top-12 left-1/2 -translate-x-1/2 bg-surface-card p-2 rounded border border-surface-border opacity-0 group-hover:opacity-100 transition-opacity z-30 pointer-events-none min-w-[80px] shadow-xl">
                      <div class="text-[8px] text-surface-text-muted uppercase font-bold mb-1">{{ slot.time }}</div>
                      <div class="flex justify-between gap-4">
                        <span class="text-[8px] text-primary font-bold">ACT: {{ slot.actual }}</span>
                        <span class="text-[8px] text-surface-text font-bold">META: {{ slot.goal }}</span>
                      </div>
                    </div>
                  </div>
                }
              </div>
            }
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

            <!-- Cumulative table -->
            <div class="industrial-card p-6">
              <h3 class="text-xs font-bold text-surface-text-muted uppercase tracking-widest mb-6">Meta Acumulada</h3>
              @if (svc.cumulativeTable().length === 0) {
                <p class="text-[10px] text-surface-text-muted uppercase text-center py-4">Sin datos</p>
              } @else {
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
                      @for (row of svc.cumulativeTable(); track row.time) {
                        <tr class="border-b border-surface-border hover:bg-surface-text/5 transition-colors">
                          <td class="py-3 font-mono">{{ row.time }}</td>
                          <td class="py-3 font-bold text-surface-text">{{ row.goal_cumulative }}</td>
                          <td class="py-3 font-bold"
                              [class.text-primary]="row.actual_cumulative >= row.goal_cumulative"
                              [class.text-red-400]="row.actual_cumulative < row.goal_cumulative">
                            {{ row.actual_cumulative }}
                          </td>
                          <td class="py-3">
                            <mat-icon class="text-[12px] h-3 w-3"
                                      [class.text-emerald-400]="row.actual_cumulative >= row.goal_cumulative"
                                      [class.text-red-400]="row.actual_cumulative < row.goal_cumulative">
                              {{ row.actual_cumulative >= row.goal_cumulative ? 'trending_up' : 'trending_down' }}
                            </mat-icon>
                          </td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              }
            </div>

            <!-- Support team + action rail -->
            <div class="space-y-6">
              <div class="industrial-card p-6">
                <h3 class="text-xs font-bold text-surface-text-muted uppercase tracking-widest mb-6">Equipo de Soporte</h3>
                @if (supportMembers().length === 0) {
                  <p class="text-[10px] text-surface-text-muted uppercase text-center py-2">Sin equipo asignado</p>
                } @else {
                  <div class="space-y-4">
                    @for (m of supportMembers(); track m.collaborator_id) {
                      <div class="flex items-center justify-between p-3 rounded-xl bg-surface-text/5 border border-surface-border">
                        <div class="flex items-center gap-3">
                          <div class="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-xs">
                            {{ m.role.slice(0,2).toUpperCase() }}
                          </div>
                          <div class="flex flex-col">
                            <span class="text-[10px] text-surface-text font-bold">{{ m.collaborator_id | slice:0:8 }}…</span>
                            <span class="text-[8px] text-surface-text-muted uppercase font-bold">{{ m.role }}</span>
                          </div>
                        </div>
                        <button class="text-primary hover:bg-primary/10 p-1.5 rounded-lg transition-all">
                          <mat-icon class="text-sm">chat</mat-icon>
                        </button>
                      </div>
                    }
                  </div>
                }
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
  styles: [':host { display: block; }']
})
export class ResourceMonitorComponent implements OnInit, OnDestroy {
  readonly svc   = inject(ResourceService);
  private route  = inject(ActivatedRoute);
  private router = inject(Router);

  readonly activeTab    = signal<'scan' | 'planned'>('scan');
  readonly resourceCode = signal<string>('—');

  readonly hasActiveWO = computed(() => !!this.svc.activeWO());
  readonly supportMembers = computed(() => this.svc.resource()?.support_members ?? []);

  ngOnInit(): void {
    const code = this.route.snapshot.paramMap.get('code');
    if (!code) {
      this.router.navigate(['/monitor/resources']);
      return;
    }
    this.resourceCode.set(code);
    this.svc.loadAll(code);
  }

  ngOnDestroy(): void {
    this.svc.reset();
  }

  goBack(): void {
    this.router.navigate(['/monitor/resources']);
  }
}
