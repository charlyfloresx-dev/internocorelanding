import {
  Component, OnInit, OnDestroy, inject, signal, computed, ChangeDetectionStrategy
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { Html5Qrcode } from 'html5-qrcode';
import { ResourceService } from '../../core/services/resource.service';
import { LaborService } from '../../core/services/labor.service';
import { BadgeClockInResponse } from '../../core/models/mes.types';

type MainTab = 'produccion' | 'personal';
type WOTab   = 'scan' | 'planned';

interface ScanFeedback {
  type: 'success' | 'transfer' | 'duplicate' | 'error';
  message: string;
  name?: string;
}

@Component({
  selector: 'app-resource-monitor',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatIconModule],
  template: `
  <div class="space-y-4 animate-fade-in-up">

    <!-- ── HEADER ─────────────────────────────────────────────────────── -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">

      <div>
        @if (svc.isLoading()) {
          <div class="h-7 w-40 bg-surface-text/10 animate-pulse rounded mb-2"></div>
          <div class="h-3 w-56 bg-surface-text/5 animate-pulse rounded"></div>
        } @else {
          <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">
            <span class="text-primary glow-text">{{ resourceCode() }}</span>
          </h2>
          <p class="text-[10px] text-surface-text-muted font-mono uppercase tracking-widest mt-1">
            {{ svc.shiftName() && svc.shiftName() !== '—' ? 'Turno: ' + svc.shiftName() : 'Sin turno activo' }}
          </p>
        }
      </div>

      <div class="flex items-center gap-2 flex-wrap">

        <!-- Main tab buttons -->
        <div class="flex rounded-xl overflow-hidden border border-surface-border bg-surface-card/40">
          <button
            (click)="setMainTab('produccion')"
            class="flex items-center gap-2 px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-all"
            [class.bg-primary/10]="mainTab() === 'produccion'"
            [class.text-primary]="mainTab() === 'produccion'"
            [class.text-surface-text-muted]="mainTab() !== 'produccion'"
          >
            <mat-icon class="text-sm !w-4 !h-4">factory</mat-icon>
            Producción
          </button>
          <button
            (click)="setMainTab('personal')"
            class="flex items-center gap-2 px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-all border-l border-surface-border relative"
            [class.bg-primary/10]="mainTab() === 'personal'"
            [class.text-primary]="mainTab() === 'personal'"
            [class.text-surface-text-muted]="mainTab() !== 'personal'"
          >
            <mat-icon class="text-sm !w-4 !h-4">groups</mat-icon>
            Personal
            @if (laborSvc.activeCount() > 0) {
              <span class="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-emerald-500 text-[8px] font-black text-white flex items-center justify-center shadow">
                {{ laborSvc.activeCount() }}
              </span>
            }
          </button>
        </div>

        <!-- Andon status -->
        <button
          class="px-3 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all border"
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
          class="px-3 py-2 bg-industrial-gray border border-white/10 text-gray-400 rounded-lg
                 text-[10px] font-bold uppercase tracking-widest hover:text-white transition-all"
        >
          ← Recursos
        </button>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════
         TAB: PRODUCCIÓN
    ══════════════════════════════════════════════════════════════════════ -->
    @if (mainTab() === 'produccion') {
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">

        <!-- Left panel: WO Activa / Planeación + Breaks -->
        <div class="lg:col-span-1 space-y-6">
          <div class="industrial-card overflow-hidden glow-border">

            <!-- Inner tabs -->
            <div class="flex border-b border-surface-border">
              <button
                (click)="woTab.set('scan')"
                class="flex-1 py-3 text-[9px] font-black uppercase tracking-widest transition-all"
                [class.text-primary]="woTab() === 'scan'"
                [class.bg-primary/5]="woTab() === 'scan'"
                [class.text-surface-text-muted]="woTab() !== 'scan'"
              >Escaneo</button>
              <button
                (click)="woTab.set('planned')"
                class="flex-1 py-3 text-[9px] font-black uppercase tracking-widest transition-all border-l border-surface-border"
                [class.text-primary]="woTab() === 'planned'"
                [class.bg-primary/5]="woTab() === 'planned'"
                [class.text-surface-text-muted]="woTab() !== 'planned'"
              >Planeación</button>
            </div>

            <div class="p-6">
              @if (woTab() === 'scan') {
                @if (svc.isLoadingGraphic()) {
                  <div class="space-y-3">
                    <div class="h-4 w-24 bg-surface-text/10 animate-pulse rounded"></div>
                    <div class="h-6 w-32 bg-surface-text/10 animate-pulse rounded"></div>
                    <div class="h-3 w-full bg-surface-text/5 animate-pulse rounded mt-4"></div>
                  </div>
                } @else if (svc.activeWO()) {
                  <div class="space-y-4">
                    @if (materialPending()) {
                      <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-500/10 border border-amber-500/30 animate-pulse-slow">
                        <mat-icon class="text-sm text-amber-400 flex-shrink-0">warning</mat-icon>
                        <div>
                          <p class="text-[9px] text-amber-400 font-black uppercase tracking-widest">Material sin surtir</p>
                          <p class="text-[8px] text-amber-300/70 leading-tight">Almacén pendiente de entregar componentes</p>
                        </div>
                      </div>
                    }
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
            <div class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mb-4">Horarios de Descanso</div>
            @if (svc.breaks().length === 0) {
              <p class="text-[10px] text-surface-text-muted uppercase">Sin descansos configurados</p>
            } @else {
              <div class="space-y-3">
                @for (b of svc.breaks(); track b.code) {
                  <div class="flex items-center gap-3 p-2 rounded-lg bg-surface-text/5 border border-surface-border">
                    <mat-icon class="text-amber-400 text-sm">{{ b.break_type === 'MEAL' ? 'restaurant' : 'coffee' }}</mat-icon>
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

        <!-- Right 3 cols: Chart + Cumulative + Support + Actions -->
        <div class="lg:col-span-3 space-y-6">

          <!-- Hourly production chart -->
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
                  <div class="flex-1 bg-surface-text/10 animate-pulse rounded-t-sm" [style.height.px]="60 + (h * 18)"></div>
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
                      <div class="w-full bg-primary shadow-[inset_0_0_10px_rgba(255,255,255,0.2)]" [style.height.px]="slot.actual * 1.5"></div>
                      <div class="w-full bg-amber-500/80" [style.height.px]="slot.missing * 1.5"></div>
                      <div class="w-full bg-ic-blue/80" [style.height.px]="slot.excess * 1.5"></div>
                    </div>
                    <div class="absolute w-full h-0.5 bg-white/20 border-t border-dashed border-white/40 z-20" [style.bottom.px]="(slot.goal * 1.5) + 32"></div>
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

            <!-- Support + Actions -->
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
    }

    <!-- ══════════════════════════════════════════════════════════════════
         TAB: PERSONAL
    ══════════════════════════════════════════════════════════════════════ -->
    @if (mainTab() === 'personal') {
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Col 1-2: Scanner + Density chart -->
        <div class="lg:col-span-2 space-y-4">

          <!-- Scanner zone -->
          <div class="industrial-card p-5 relative overflow-hidden"
               [class.ring-2]="scanFeedback()"
               [class.ring-emerald-500]="scanFeedback()?.type === 'success'"
               [class.ring-blue-500]="scanFeedback()?.type === 'transfer'"
               [class.ring-amber-500]="scanFeedback()?.type === 'duplicate'"
               [class.ring-red-500]="scanFeedback()?.type === 'error'">
            <div class="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-violet-500 to-primary"></div>

            @if (!scanFeedback()) {
              <!-- Idle -->
              <div class="flex items-center gap-5 py-2">
                <div class="relative w-14 h-14 rounded-xl bg-surface-text/5 border border-surface-border flex items-center justify-center flex-shrink-0">
                  <mat-icon class="text-2xl text-surface-text-muted">credit_card</mat-icon>
                  @if (!debounceActive()) {
                    <span class="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-500 animate-ping"></span>
                    <span class="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-500"></span>
                  }
                </div>
                <div class="flex-1">
                  <p class="text-sm font-black text-surface-text">
                    {{ debounceActive() ? 'Procesando...' : 'Listo para escanear' }}
                  </p>
                  <p class="text-[10px] text-surface-text-muted mt-0.5">
                    Acerque tarjeta RFID, QR o código de barras al lector
                  </p>
                </div>
                <!-- Camera toggle button -->
                <button
                  (click)="toggleCamera()"
                  class="flex items-center gap-2 px-3 py-2 rounded-xl border text-[10px] font-black uppercase tracking-widest transition-all flex-shrink-0"
                  [class.bg-primary/10]="!cameraActive()"
                  [class.border-primary/30]="!cameraActive()"
                  [class.text-primary]="!cameraActive()"
                  [class.bg-red-500/10]="cameraActive()"
                  [class.border-red-500/30]="cameraActive()"
                  [class.text-red-400]="cameraActive()"
                >
                  <mat-icon class="!text-sm !w-4 !h-4">{{ cameraActive() ? 'videocam_off' : 'qr_code_scanner' }}</mat-icon>
                  {{ cameraActive() ? 'Cerrar' : 'Cámara' }}
                </button>
              </div>
            } @else {
              <!-- Feedback -->
              <div class="flex items-center gap-5 py-2 animate-fade-in">
                <div class="w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0"
                     [class.bg-emerald-500/15]="scanFeedback()!.type === 'success'"
                     [class.bg-blue-500/15]="scanFeedback()!.type === 'transfer'"
                     [class.bg-amber-500/15]="scanFeedback()!.type === 'duplicate'"
                     [class.bg-red-500/15]="scanFeedback()!.type === 'error'">
                  <mat-icon class="text-2xl"
                            [class.text-emerald-400]="scanFeedback()!.type === 'success'"
                            [class.text-blue-400]="scanFeedback()!.type === 'transfer'"
                            [class.text-amber-400]="scanFeedback()!.type === 'duplicate'"
                            [class.text-red-400]="scanFeedback()!.type === 'error'">
                    {{ scanFeedback()!.type === 'success' ? 'check_circle' :
                       scanFeedback()!.type === 'transfer' ? 'swap_horiz' :
                       scanFeedback()!.type === 'duplicate' ? 'replay' : 'cancel' }}
                  </mat-icon>
                </div>
                <div class="flex-1 min-w-0">
                  @if (scanFeedback()!.name) {
                    <p class="text-base font-black text-surface-text truncate">{{ scanFeedback()!.name }}</p>
                  }
                  <p class="text-xs font-bold mt-0.5"
                     [class.text-emerald-400]="scanFeedback()!.type === 'success'"
                     [class.text-blue-400]="scanFeedback()!.type === 'transfer'"
                     [class.text-amber-400]="scanFeedback()!.type === 'duplicate'"
                     [class.text-red-400]="scanFeedback()!.type === 'error'">
                    {{ scanFeedback()!.message }}
                  </p>
                </div>
                @if (debounceActive()) {
                  <div class="w-24 h-1 bg-surface-border rounded-full overflow-hidden flex-shrink-0">
                    <div class="h-full bg-surface-text-muted rounded-full animate-[shrink_1.5s_linear_forwards]"></div>
                  </div>
                }
              </div>
            }

            <!-- Camera viewer — always in DOM so html5-qrcode can mount without timing issues.
                 Height collapses to 0 when not active (width stays 100% for correct measuring). -->
            <div class="mt-4 relative overflow-hidden transition-all duration-300"
                 [style.maxHeight]="cameraActive() ? '300px' : '0'"
                 [style.marginTop]="cameraActive() ? '1rem' : '0'">
              <div
                id="reader-monitor"
                class="w-full rounded-2xl overflow-hidden bg-black"
                style="aspect-ratio:1/1"
              ></div>
              <!-- Scan line overlay -->
              @if (cameraActive()) {
                <div class="absolute inset-0 pointer-events-none border-2 border-primary rounded-2xl overflow-hidden">
                  <div class="absolute top-0 left-0 w-full h-0.5 bg-primary shadow-[0_0_15px_rgba(0,229,255,0.8)] animate-scan-line"></div>
                </div>
              }
            </div>
          </div>

          <!-- Hourly density chart -->
          <div class="industrial-card p-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest flex items-center gap-2">
                <mat-icon class="text-sm text-violet-400">groups</mat-icon>
                Densidad de Personal por Hora
              </h3>
              <button (click)="refreshPersonnel()" class="p-1 rounded hover:bg-surface-text/5 transition-colors">
                <mat-icon class="text-sm text-surface-text-muted">refresh</mat-icon>
              </button>
            </div>

            @if (laborSvc.headcountHistory()) {
              @let series = laborSvc.headcountHistory()!.series;
              @let mx = maxHeadcount();
              <div class="flex items-end gap-1 h-28">
                @for (pt of series; track pt.hour) {
                  <div class="flex-1 flex flex-col items-center gap-1 group cursor-default"
                       [title]="pt.label + ' — ' + pt.active + ' activos, ' + pt.on_permit + ' permiso'">
                    <div class="w-full rounded-t overflow-hidden flex flex-col-reverse" style="height:80px">
                      @if (pt.active > 0 && mx > 0) {
                        <div class="w-full bg-emerald-500 transition-all"
                             [style.height.%]="(pt.active / mx) * 100"></div>
                      }
                      @if (pt.on_permit > 0 && mx > 0) {
                        <div class="w-full bg-amber-400/70 transition-all"
                             [style.height.%]="(pt.on_permit / mx) * 100"></div>
                      }
                      @if (pt.total === 0) {
                        <div class="w-full h-full bg-surface-text/5"></div>
                      }
                    </div>
                    <span class="text-[9px] text-surface-text-muted font-mono">{{ pt.hour }}h</span>
                  </div>
                }
              </div>
              <div class="flex gap-4 mt-2">
                <span class="flex items-center gap-1.5 text-[9px] text-surface-text-muted">
                  <span class="w-2 h-2 rounded-sm bg-emerald-500 inline-block"></span>Activos
                </span>
                <span class="flex items-center gap-1.5 text-[9px] text-surface-text-muted">
                  <span class="w-2 h-2 rounded-sm bg-amber-400/70 inline-block"></span>En Permiso
                </span>
              </div>
            } @else {
              <div class="h-28 flex items-center justify-center text-surface-text-muted text-xs">
                Sin historial para hoy
              </div>
            }
          </div>
        </div>

        <!-- Col 3: Headcount panel + Collaborators list -->
        <div class="flex flex-col gap-4">

          <!-- KPI summary -->
          @if (laborSvc.headcount()) {
            @let hc = laborSvc.headcount()!.headcount;
            <div class="grid grid-cols-2 gap-3">
              <div class="industrial-card p-4 text-center bg-emerald-500/5 border-emerald-500/20">
                <div class="text-4xl font-black text-emerald-400">{{ hc.active }}</div>
                <div class="text-[9px] text-emerald-600 font-black uppercase tracking-widest mt-1">Activos</div>
              </div>
              <div class="industrial-card p-4 text-center">
                <div class="text-4xl font-black text-surface-text">{{ hc.total_rostered }}</div>
                <div class="text-[9px] text-surface-text-muted font-black uppercase tracking-widest mt-1">Total</div>
              </div>
              @if (hc.on_permit > 0) {
                <div class="industrial-card p-3 text-center bg-amber-500/5 border-amber-500/20">
                  <div class="text-2xl font-black text-amber-400">{{ hc.on_permit }}</div>
                  <div class="text-[9px] text-amber-600 font-black uppercase tracking-widest mt-0.5">Permiso</div>
                </div>
              }
              @if (hc.transferred_in > 0) {
                <div class="industrial-card p-3 text-center bg-blue-500/5 border-blue-500/20">
                  <div class="text-2xl font-black text-blue-400">{{ hc.transferred_in }}</div>
                  <div class="text-[9px] text-blue-600 font-black uppercase tracking-widest mt-0.5">Traslados</div>
                </div>
              }
            </div>
          } @else {
            <div class="industrial-card p-6 text-center text-surface-text-muted text-xs">
              {{ laborSvc.isLoading() ? 'Cargando...' : 'Sin datos de headcount' }}
            </div>
          }

          <!-- Collaborators list -->
          <div class="industrial-card flex-1 overflow-hidden flex flex-col">
            <div class="px-4 pt-4 pb-2 border-b border-surface-border text-[9px] text-surface-text-muted font-black uppercase tracking-widest">
              En Línea Ahora
            </div>
            <div class="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar" style="max-height:380px">
              @if (laborSvc.headcount()) {
                @for (c of laborSvc.headcount()!.collaborators; track c.id) {
                  <div class="flex items-center gap-3 p-3 rounded-xl bg-surface-text/5 border border-surface-border hover:border-primary/30 transition-all">
                    <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                         [class.bg-emerald-500/15]="c.status === 'ACTIVE'"
                         [class.bg-amber-500/15]="c.status === 'ON_PERMIT'"
                         [class.bg-blue-500/15]="c.status === 'TRANSFERRED_IN'">
                      <mat-icon class="text-sm"
                                [class.text-emerald-400]="c.status === 'ACTIVE'"
                                [class.text-amber-400]="c.status === 'ON_PERMIT'"
                                [class.text-blue-400]="c.status === 'TRANSFERRED_IN'">
                        {{ c.status === 'ACTIVE' ? 'person' : c.status === 'ON_PERMIT' ? 'coffee' : 'swap_horiz' }}
                      </mat-icon>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-[11px] font-bold text-surface-text truncate">{{ c.name }}</p>
                      <div class="flex items-center gap-2 mt-0.5">
                        <span class="text-[9px] font-mono text-surface-text-muted">{{ c.clock_in }}</span>
                        @if (c.is_deviation) {
                          <span class="px-1 py-0.5 rounded text-[8px] font-black uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20">dev</span>
                        }
                      </div>
                    </div>
                  </div>
                }
                @if (laborSvc.headcount()!.collaborators.length === 0) {
                  <div class="text-center py-10 text-surface-text-muted">
                    <mat-icon class="text-3xl mb-2">group_off</mat-icon>
                    <p class="text-xs font-bold uppercase">Sin personal registrado</p>
                  </div>
                }
              }
            </div>
          </div>
        </div>
      </div>
    }

  </div>
  `,
  styles: [`
    :host { display: block; }
    @keyframes pulse-slow { 0%,100%{opacity:1} 50%{opacity:.7} }
    .animate-pulse-slow { animation: pulse-slow 2.5s ease-in-out infinite; }
    @keyframes shrink { from { width:100% } to { width:0% } }
    @keyframes scan-line { 0%{top:0} 50%{top:calc(100% - 2px)} 100%{top:0} }
    .animate-scan-line { animation: scan-line 2s linear infinite; }
    .custom-scrollbar::-webkit-scrollbar { width: 3px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
  `]
})
export class ResourceMonitorComponent implements OnInit, OnDestroy {

  // Services
  readonly svc      = inject(ResourceService);
  readonly laborSvc = inject(LaborService);
  private route     = inject(ActivatedRoute);
  private router    = inject(Router);

  // Tab state
  readonly mainTab = signal<MainTab>('produccion');
  readonly woTab   = signal<WOTab>('scan');

  // Resource identity
  readonly resourceCode = signal<string>('—');

  // Computed from ResourceService
  readonly hasActiveWO    = computed(() => !!this.svc.activeWO());
  readonly supportMembers = computed(() => this.svc.resource()?.support_members ?? []);
  readonly materialPending = computed(() => this.svc.activeWO()?.material_status === 'PENDING_ISSUE');
  readonly maxHeadcount   = computed(() => {
    const s = this.laborSvc.headcountHistory()?.series ?? [];
    return Math.max(...s.map(p => p.total), 1);
  });

  // Scanner state
  readonly debounceActive = signal(false);
  readonly scanFeedback   = signal<ScanFeedback | null>(null);
  readonly cameraActive   = signal(false);

  // Internal
  private scanBuffer = '';
  private personnelInterval?: ReturnType<typeof setInterval>;
  private feedbackTimeout?: ReturnType<typeof setTimeout>;
  private qrCode: Html5Qrcode | null = null;
  private readonly DEBOUNCE_MS  = 1500;
  private readonly MIN_LEN      = 3;
  private readonly keydownFn    = this.onKeydown.bind(this);

  ngOnInit(): void {
    const code = this.route.snapshot.paramMap.get('code');
    if (!code) { this.router.navigate(['/monitor/resources']); return; }
    this.resourceCode.set(code);
    this.svc.loadAll(code);
    document.addEventListener('keydown', this.keydownFn);
  }

  ngOnDestroy(): void {
    document.removeEventListener('keydown', this.keydownFn);
    clearInterval(this.personnelInterval);
    clearTimeout(this.feedbackTimeout);
    void this.stopCamera();
    this.svc.reset();
  }

  // ── Tab switching ────────────────────────────────────────────────────

  setMainTab(tab: MainTab): void {
    this.mainTab.set(tab);
    if (tab === 'personal') this.loadPersonnel();
  }

  // ── Personnel data ───────────────────────────────────────────────────

  refreshPersonnel(): void { this.loadPersonnel(); }

  private loadPersonnel(): void {
    const id = this.svc.resource()?.id;
    if (!id) return;
    void this.laborSvc.loadHeadcount(id);
    void this.laborSvc.loadHeadcountHistory(id);
    clearInterval(this.personnelInterval);
    this.personnelInterval = setInterval(() => {
      if (this.mainTab() === 'personal') {
        const rid = this.svc.resource()?.id;
        if (rid) void this.laborSvc.loadHeadcount(rid);
      }
    }, 30_000);
  }

  // ── HID Scanner listener ─────────────────────────────────────────────

  onKeydown(event: KeyboardEvent): void {
    if (this.mainTab() !== 'personal') return;
    if (this.debounceActive()) return;

    if (event.key === 'Enter') {
      if (this.scanBuffer.length >= this.MIN_LEN) {
        event.preventDefault();
        const val = this.scanBuffer;
        this.scanBuffer = '';
        void this.processScan(val);
      } else {
        this.scanBuffer = '';
      }
    } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      this.scanBuffer += event.key;
    }
  }

  private async processScan(badgeValue: string): Promise<void> {
    const cleanValue = badgeValue.trim();
    if (cleanValue.length < this.MIN_LEN) return;

    this.debounceActive.set(true);
    setTimeout(() => this.debounceActive.set(false), this.DEBOUNCE_MS);

    try {
      const res = await this.laborSvc.clockInByBadge({
        resource_code: this.resourceCode(),
        badge_raw_value: cleanValue,
        client_timestamp: new Date().toISOString(),
      });
      this.applyFeedback(res);
      const id = this.svc.resource()?.id;
      if (id) void this.laborSvc.loadHeadcount(id);
    } catch (err: any) {
      const msg = err?.error?.detail ?? 'Error de comunicación';
      this.showFeedback({ type: 'error', message: msg });
    }
  }

  private applyFeedback(res: BadgeClockInResponse): void {
    const name = res.collaborator?.full_name;
    switch (res.action) {
      case 'CLOCK_IN':           this.showFeedback({ type: 'success',   message: 'Entrada registrada', name }); break;
      case 'TRANSFER':           this.showFeedback({ type: 'transfer',  message: 'Traslado automático', name }); break;
      case 'ALREADY_CLOCKED_IN': this.showFeedback({ type: 'duplicate', message: 'Ya registrado aquí', name }); break;
    }
  }

  private showFeedback(fb: ScanFeedback): void {
    clearTimeout(this.feedbackTimeout);
    this.scanFeedback.set(fb);
    this.feedbackTimeout = setTimeout(() => this.scanFeedback.set(null), 4000);
  }

  // ── Camera QR scanner (same pattern as login) ────────────────────────

  async toggleCamera(): Promise<void> {
    if (this.cameraActive()) {
      await this.stopCamera();
    } else {
      await this.startCamera();
    }
  }

  private async startCamera(): Promise<void> {
    // reader-monitor is always in the DOM (not inside @if) so no render delay needed
    this.cameraActive.set(true);
    try {
      this.qrCode = new Html5Qrcode('reader-monitor');
      await this.qrCode.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 220, height: 220 } },
        (decodedText: string) => {
          void this.processScan(decodedText);
          void this.stopCamera();
        },
        () => { /* scan errors silenciosos */ }
      );
    } catch (err) {
      console.error('[Monitor] Camera start failed:', err);
      this.cameraActive.set(false);
    }
  }

  private async stopCamera(): Promise<void> {
    if (this.qrCode) {
      try {
        if (this.qrCode.isScanning) await this.qrCode.stop();
        this.qrCode.clear();
      } catch { /* ignore stop errors */ }
      this.qrCode = null;
    }
    this.cameraActive.set(false);
  }

  // ── Navigation ───────────────────────────────────────────────────────

  goBack(): void { this.router.navigate(['/monitor/resources']); }
}
