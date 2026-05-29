import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ResourceService } from '../../../core/services/resource.service';
import { ShiftService } from '../../../core/services/shift.service';
import { SideDrawerService } from '../../../core/services/side-drawer.service';
import { NotificationService } from '../../../core/services/notification.service';
import { WorkOrderFormComponent } from '../../../shared/components/work-order-form.component';
import { ResourceRead, ShiftRead } from '../../../core/models/mes.types';

interface WorkOrderOption {
  id: string;
  order_number: string;
  item_code: string;
  order_quantity: number;
  manufactured_quantity: number;
  status: string;
}

interface ProductionRunRead {
  id: string;
  work_order_id: string;
  resource_id: string;
  shift_id: string;
  date: string;
  planned_quantity: number;
  actual_quantity: number;
  order_number?: string;
  item_code?: string;
  resource_code?: string;
  resource_name?: string;
  shift_name?: string;
}

interface PlanningRow {
  resource: ResourceRead;
  runs: ProductionRunRead[];
}

@Component({
  selector: 'app-daily-planning',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="p-8 space-y-8 animate-fade-in">

      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <h1 class="text-4xl font-black text-surface-text uppercase tracking-tighter italic leading-none">
            Planificación Diaria
          </h1>
          <p class="text-surface-text-muted font-mono text-[10px] uppercase tracking-[0.3em]">
            Asignación de órdenes de trabajo a recursos por turno
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Date picker -->
          <div class="flex items-center gap-2 px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl">
            <mat-icon class="text-sm text-primary">calendar_today</mat-icon>
            <input type="date" [(ngModel)]="selectedDate" (change)="loadPlan()"
              class="bg-transparent text-xs font-mono text-surface-text outline-none cursor-pointer" />
          </div>

          <button (click)="goToday()"
            class="px-4 py-3 bg-surface-bg border border-surface-border hover:bg-primary/10 text-surface-text-muted hover:text-primary rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all">
            Hoy
          </button>

          <button (click)="loadPlan()"
            class="p-3 bg-surface-bg border border-surface-border hover:bg-primary/10 rounded-2xl transition-all">
            <mat-icon class="text-sm text-surface-text-muted">refresh</mat-icon>
          </button>

          <button (click)="openNewWorkOrder()"
            class="flex items-center gap-2 px-5 py-3 bg-surface-bg border border-surface-border hover:bg-violet-500/10 hover:border-violet-500/30 text-violet-400 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all">
            <mat-icon class="text-sm">assignment_add</mat-icon>
            Nueva OT
          </button>
        </div>
      </div>

      <!-- Summary bar -->
      <div class="grid grid-cols-4 gap-4">
        @for (stat of stats(); track stat.label) {
          <div class="p-4 bg-surface-card border border-surface-border rounded-2xl flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center {{ stat.color }}">
              <mat-icon class="text-lg">{{ stat.icon }}</mat-icon>
            </div>
            <div>
              <div class="text-2xl font-black text-surface-text leading-none">{{ stat.value }}</div>
              <div class="text-[9px] text-surface-text-muted uppercase tracking-widest">{{ stat.label }}</div>
            </div>
          </div>
        }
      </div>

      <!-- Planning board -->
      @if (loading()) {
        <div class="flex items-center justify-center py-24">
          <div class="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
        </div>
      } @else {
        <div class="space-y-4">
          @for (row of planningRows(); track row.resource.id) {
            <div class="industrial-card overflow-hidden">
              <!-- Resource header -->
              <div class="flex items-center justify-between px-6 py-4 border-b border-surface-border bg-surface-bg/50">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center">
                    <mat-icon class="text-sm text-primary">{{ resourceIcon(row.resource.resource_type) }}</mat-icon>
                  </div>
                  <div>
                    <span class="text-xs font-black text-primary tracking-widest font-mono">{{ row.resource.code }}</span>
                    <span class="text-xs text-surface-text ml-3">{{ row.resource.name }}</span>
                  </div>
                  @if (row.resource.capacity) {
                    <span class="text-[9px] text-surface-text-muted font-mono">· {{ row.resource.capacity }} pzas/hr</span>
                  }
                </div>
                <button (click)="openAssignRun(row.resource)"
                  [disabled]="!hasWorkOrders()"
                  class="flex items-center gap-1.5 px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-xl text-[9px] font-black uppercase tracking-widest transition-all disabled:opacity-40 disabled:pointer-events-none">
                  <mat-icon class="text-xs">add</mat-icon>
                  Asignar OT
                </button>
              </div>

              <!-- Runs for this resource -->
              <div class="px-6 py-4">
                @if (row.runs.length === 0) {
                  <div class="flex items-center gap-2 text-surface-text-muted py-2">
                    <mat-icon class="text-sm opacity-40">event_busy</mat-icon>
                    <span class="text-[10px] italic">Sin planificación para este día</span>
                  </div>
                } @else {
                  <div class="flex flex-wrap gap-3">
                    @for (run of row.runs; track run.id) {
                      <div class="flex items-start gap-3 p-4 bg-surface-bg border border-surface-border rounded-xl group min-w-[240px] max-w-xs">
                        <div class="flex-1 min-w-0">
                          <div class="flex items-center gap-2 mb-1">
                            <span class="text-xs font-black text-primary font-mono">{{ run.order_number }}</span>
                            <span class="text-[9px] text-surface-text-muted font-mono uppercase">{{ run.shift_name }}</span>
                          </div>
                          <div class="text-[10px] text-surface-text">{{ run.item_code }}</div>
                          <div class="flex items-center gap-2 mt-2">
                            <div class="flex-1 h-1.5 bg-surface-border rounded-full overflow-hidden">
                              <div class="h-full bg-emerald-400 rounded-full transition-all"
                                [style.width.%]="runProgress(run)"></div>
                            </div>
                            <span class="text-[9px] text-surface-text-muted font-mono">
                              {{ run.actual_quantity }}/{{ run.planned_quantity }}
                            </span>
                          </div>
                        </div>
                        <button (click)="deleteRun(run)"
                          class="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-rose-500/10 text-rose-400 rounded-lg flex-shrink-0"
                          title="Quitar planificación">
                          <mat-icon class="text-xs">close</mat-icon>
                        </button>
                      </div>
                    }
                  </div>
                }
              </div>
            </div>
          } @empty {
            <div class="py-24 text-center space-y-4">
              <mat-icon class="text-5xl text-surface-text-muted/20">event_note</mat-icon>
              <p class="text-surface-text-muted text-sm italic">No hay recursos configurados. Ve a Configuración → Recursos.</p>
            </div>
          }
        </div>
      }

      <!-- Assign Run Modal (inline) -->
      @if (assignModal.open()) {
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6" (click)="assignModal.open.set(false)">
          <div class="w-full max-w-md bg-surface-bg border border-surface-border rounded-3xl p-8 shadow-2xl space-y-6" (click)="$event.stopPropagation()">
            <h3 class="text-xl font-black text-surface-text uppercase italic tracking-tighter">
              Asignar OT — {{ assignModal.resource?.code }}
            </h3>

            <div class="space-y-4">
              <!-- Work Order select -->
              <div class="space-y-2">
                <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Orden de Trabajo *</label>
                <select [(ngModel)]="assignModal.workOrderId"
                  class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs cursor-pointer outline-none focus:border-primary transition-all">
                  <option value="">— Seleccionar OT —</option>
                  @for (wo of workOrders(); track wo.id) {
                    <option [value]="wo.id">{{ wo.order_number }} · {{ wo.item_code }} ({{ wo.order_quantity - wo.manufactured_quantity }} pend.)</option>
                  }
                </select>
              </div>

              <!-- Shift select -->
              <div class="space-y-2">
                <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Turno *</label>
                <select [(ngModel)]="assignModal.shiftId"
                  class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs cursor-pointer outline-none focus:border-primary transition-all">
                  <option value="">— Seleccionar turno —</option>
                  @for (s of companyShifts(); track s.id) {
                    <option [value]="s.id">{{ s.name }} ({{ s.start_time }}–{{ s.end_time }})</option>
                  }
                </select>
              </div>

              <!-- Planned quantity -->
              <div class="space-y-2">
                <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Cantidad planificada *</label>
                <input type="number" [(ngModel)]="assignModal.plannedQty" min="1" placeholder="480"
                  class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono outline-none focus:border-primary transition-all" />
              </div>
            </div>

            <div class="flex gap-3">
              <button (click)="confirmAssign()"
                [disabled]="!assignModal.workOrderId || !assignModal.shiftId || !assignModal.plannedQty || assigning()"
                class="flex-1 py-4 bg-primary text-slate-950 rounded-2xl text-[10px] font-black uppercase tracking-widest disabled:opacity-50 disabled:pointer-events-none transition-all hover:scale-[1.02]">
                {{ assigning() ? 'Asignando...' : 'Confirmar Asignación' }}
              </button>
              <button (click)="assignModal.open.set(false)"
                class="px-6 border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-surface-border transition-all">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      }

    </div>
  `,
  styles: [`
    :host { display: block; }
    .animate-fade-in { animation: fadeIn 0.4s cubic-bezier(0.22,1,0.36,1) forwards; }
    @keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
  `]
})
export class DailyPlanningComponent implements OnInit {
  private http       = inject(HttpClient);
  private resourceSvc = inject(ResourceService);
  private shiftSvc   = inject(ShiftService);
  private drawer     = inject(SideDrawerService);
  private notif      = inject(NotificationService);

  private base = `${environment.productionUrl}/mes`;

  selectedDate = new Date().toISOString().split('T')[0];
  loading   = signal(false);
  assigning = signal(false);

  resources  = signal<ResourceRead[]>([]);
  runs       = signal<ProductionRunRead[]>([]);
  workOrders = signal<WorkOrderOption[]>([]);

  companyShifts = computed(() =>
    this.shiftSvc.shifts().filter(s => s.is_active && !s.resource_id)
  );

  planningRows = computed((): PlanningRow[] =>
    this.resources().map(r => ({
      resource: r,
      runs: this.runs().filter(run => run.resource_id === r.id),
    }))
  );

  stats = computed(() => [
    { label: 'Recursos', value: this.resources().length, icon: 'grid_view', color: 'bg-primary/10 text-primary' },
    { label: 'OTs Asignadas', value: this.runs().length, icon: 'assignment', color: 'bg-violet-500/10 text-violet-400' },
    { label: 'Total planificado', value: this.runs().reduce((s, r) => s + r.planned_quantity, 0), icon: 'stacked_bar_chart', color: 'bg-emerald-500/10 text-emerald-400' },
    { label: 'Producido', value: this.runs().reduce((s, r) => s + r.actual_quantity, 0), icon: 'check_circle', color: 'bg-amber-500/10 text-amber-400' },
  ]);

  assignModal = {
    open:        signal(false),
    resource:    null as ResourceRead | null,
    workOrderId: '',
    shiftId:     '',
    plannedQty:  480,
  };

  ngOnInit() {
    this.loadAll();
    this.drawer.refresh$.subscribe(() => this.loadAll());
  }

  async loadAll() {
    await Promise.all([
      this.resourceSvc.listResources().then(list => this.resources.set(list)),
      this.shiftSvc.loadShifts(),
      this.loadPlan(),
      this.loadWorkOrders(),
    ]);
  }

  async loadPlan() {
    this.loading.set(true);
    try {
      const resp: any = await lastValueFrom(
        this.http.get(`${this.base}/planning/runs?target_date=${this.selectedDate}`)
      );
      const data = resp?.data ?? resp;
      this.runs.set(Array.isArray(data) ? data : []);
    } catch {
      this.runs.set([]);
    } finally {
      this.loading.set(false);
    }
  }

  async loadWorkOrders() {
    try {
      const resp: any = await lastValueFrom(
        this.http.get(`${this.base}/orders/`)
      );
      const data = resp?.data ?? resp;
      this.workOrders.set(Array.isArray(data) ? data.filter((wo: any) => wo.status !== 'COMPLETED') : []);
    } catch {
      this.workOrders.set([]);
    }
  }

  hasWorkOrders(): boolean {
    return this.workOrders().length > 0;
  }

  goToday() {
    this.selectedDate = new Date().toISOString().split('T')[0];
    this.loadPlan();
  }

  resourceIcon(type?: string | null): string {
    const map: Record<string, string> = { CELL: 'grid_view', MACHINE: 'precision_manufacturing', LINE: 'linear_scale', AREA: 'warehouse' };
    return map[type ?? ''] ?? 'settings';
  }

  runProgress(run: ProductionRunRead): number {
    if (!run.planned_quantity) return 0;
    return Math.min(100, Math.round((run.actual_quantity / run.planned_quantity) * 100));
  }

  openAssignRun(resource: ResourceRead) {
    this.assignModal.resource    = resource;
    this.assignModal.workOrderId = '';
    this.assignModal.shiftId     = '';
    this.assignModal.plannedQty  = resource.capacity ? Number(resource.capacity) * 8 : 480;
    this.assignModal.open.set(true);
  }

  async confirmAssign() {
    const m = this.assignModal;
    if (!m.resource || !m.workOrderId || !m.shiftId || !m.plannedQty) return;

    this.assigning.set(true);
    try {
      await lastValueFrom(this.http.post(`${this.base}/planning/runs`, {
        work_order_id:    m.workOrderId,
        resource_id:      m.resource.id,
        shift_id:         m.shiftId,
        production_date:  this.selectedDate,
        planned_quantity: Number(m.plannedQty),
      }));
      this.notif.success('Asignación registrada', `${m.resource.code} — ${this.selectedDate}`);
      m.open.set(false);
      await this.loadPlan();
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'No se pudo asignar la OT');
    } finally {
      this.assigning.set(false);
    }
  }

  async deleteRun(run: ProductionRunRead) {
    if (!confirm(`¿Quitar la OT ${run.order_number} de ${run.resource_code}?`)) return;
    try {
      await lastValueFrom(this.http.delete(`${this.base}/planning/runs/${run.id}`));
      this.runs.update(list => list.filter(r => r.id !== run.id));
      this.notif.success('Eliminado', `${run.order_number} removido del plan`);
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'No se pudo eliminar');
    }
  }

  openNewWorkOrder() {
    this.drawer.open(WorkOrderFormComponent, {
      title: 'Nueva Orden de Trabajo',
      subtitle: 'MES · Fabricación',
      icon: 'assignment_add',
      width: 'w-[480px]',
    });
  }
}
