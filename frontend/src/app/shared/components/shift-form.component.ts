import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { ShiftService } from '../../core/services/shift.service';
import { ResourceService } from '../../core/services/resource.service';
import { NotificationService } from '../../core/services/notification.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { ResourceRead, ShiftBreakCreate, BreakSlot } from '../../core/models/mes.types';

/** Break-type icon map */
const BREAK_ICON: Record<string, string> = {
  BREAK: 'coffee',
  MEAL:  'restaurant',
  MAINTENANCE: 'build',
};

@Component({
  selector: 'app-shift-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">

      <!-- Header -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-amber-500/10 rounded-2xl flex items-center justify-center text-amber-400 border border-amber-500/20">
            <mat-icon class="text-2xl">schedule</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              {{ isEdit ? 'Editar Turno' : 'Nuevo Turno' }}
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              {{ form.value.resource_id ? 'TURNO ESPECÍFICO DE RECURSO' : 'TURNO DE EMPRESA' }}
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-5">

        <!-- Shift fields -->
        <form [formGroup]="form" class="space-y-5">

          <!-- Código + Nombre -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Código *</label>
              <input type="text" formControlName="code"
                placeholder="MAT"
                [readonly]="isEdit"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase"
                [class.opacity-60]="isEdit" />
            </div>
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Nombre *</label>
              <input type="text" formControlName="name"
                placeholder="Turno Matutino"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-bold outline-none focus:border-primary transition-all" />
            </div>
          </div>

          <!-- Horarios -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Inicio *</label>
              <input type="time" formControlName="start_time"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono outline-none focus:border-primary transition-all" />
            </div>
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Fin *</label>
              <input type="time" formControlName="end_time"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono outline-none focus:border-primary transition-all" />
            </div>
          </div>

          <!-- Opciones -->
          <div class="grid grid-cols-2 gap-4">
            <div class="flex items-center gap-3 p-4 bg-surface-card rounded-xl border border-surface-border">
              <input type="checkbox" formControlName="is_overnight" id="overnight" class="w-4 h-4 rounded accent-amber-500 cursor-pointer" />
              <label for="overnight" class="text-xs font-bold text-surface-text cursor-pointer">Cruza medianoche</label>
            </div>
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">
                Min. descanso <span class="text-surface-text-muted/60">(total)</span>
              </label>
              <input type="number" formControlName="break_minutes" min="0" max="480"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono outline-none focus:border-primary transition-all" />
            </div>
          </div>

          <!-- Recurso específico -->
          <div class="space-y-2">
            <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">
              Recurso específico
              <span class="ml-2 text-[8px] normal-case font-normal text-surface-text-muted/60">
                (vacío = aplica a toda la empresa)
              </span>
            </label>
            @if (resourcesLoading()) {
              <div class="h-12 bg-surface-card rounded-xl animate-pulse"></div>
            } @else {
              <select formControlName="resource_id"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs outline-none focus:border-primary transition-all cursor-pointer">
                <option value="">— Empresa completa —</option>
                @for (r of resources(); track r.id) {
                  <option [value]="r.id">{{ r.code }} — {{ r.name }}</option>
                }
              </select>
              @if (form.value.resource_id) {
                <p class="text-[9px] text-amber-400 font-bold flex items-center gap-1">
                  <mat-icon class="text-xs">info</mat-icon>
                  Este turno sobreescribe el horario de breaks del recurso seleccionado
                </p>
              }
            }
          </div>

          @if (isEdit) {
            <div class="flex items-center gap-3 p-4 bg-surface-card rounded-xl border border-surface-border">
              <input type="checkbox" formControlName="is_active" id="shiftActive" class="w-4 h-4 rounded accent-primary cursor-pointer" />
              <label for="shiftActive" class="text-xs font-bold text-surface-text cursor-pointer">Turno activo</label>
            </div>
          }

        </form>

        <!-- ── Breaks section (only when editing) ────────────────────────── -->
        @if (isEdit && editShiftId) {
          <div class="border-t border-surface-border pt-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-[10px] font-black text-surface-text uppercase tracking-widest flex items-center gap-2">
                <mat-icon class="text-sm text-amber-400">coffee</mat-icon>
                Breaks del turno
              </h3>
              <button (click)="showAddBreak.set(!showAddBreak())"
                class="text-[9px] font-black text-primary uppercase tracking-widest flex items-center gap-1 hover:opacity-70 transition-opacity">
                <mat-icon class="text-xs">{{ showAddBreak() ? 'remove' : 'add' }}</mat-icon>
                Agregar
              </button>
            </div>

            <!-- Existing breaks -->
            <div class="space-y-2 mb-4">
              @for (brk of currentBreaks(); track brk.code) {
                <div class="flex items-center gap-3 p-3 bg-surface-card rounded-xl border border-surface-border group">
                  <mat-icon class="text-sm text-amber-400">{{ breakIcon(brk.break_type) }}</mat-icon>
                  <div class="flex-1 min-w-0">
                    <div class="text-xs font-bold text-surface-text">{{ brk.label }}</div>
                    <div class="text-[9px] text-surface-text-muted font-mono">
                      {{ brk.start_time }} – {{ brk.end_time }} · {{ brk.duration_minutes }} min
                    </div>
                  </div>
                  <button (click)="deleteBreak(brk)"
                    class="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-rose-500/10 text-rose-400 rounded-lg">
                    <mat-icon class="text-xs">delete</mat-icon>
                  </button>
                </div>
              } @empty {
                <p class="text-[10px] text-surface-text-muted text-center py-4 italic">Sin breaks configurados</p>
              }
            </div>

            <!-- Add break form -->
            @if (showAddBreak()) {
              <div class="p-4 bg-surface-card rounded-2xl border border-primary/20 space-y-4">
                <h4 class="text-[9px] font-black text-primary uppercase tracking-widest">Nuevo Break</h4>
                <div class="grid grid-cols-2 gap-3">
                  <div class="space-y-1">
                    <label class="text-[8px] text-surface-text-muted uppercase font-bold">Código</label>
                    <input [(ngModel)]="newBreak.code" type="text" maxlength="15" placeholder="DSC1"
                      class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs font-mono outline-none focus:border-primary transition-all" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[8px] text-surface-text-muted uppercase font-bold">Etiqueta</label>
                    <input [(ngModel)]="newBreak.label" type="text" placeholder="Primer Descanso"
                      class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs outline-none focus:border-primary transition-all" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[8px] text-surface-text-muted uppercase font-bold">Inicio</label>
                    <input [(ngModel)]="newBreak.start_time" type="time"
                      class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs font-mono outline-none focus:border-primary transition-all" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[8px] text-surface-text-muted uppercase font-bold">Fin</label>
                    <input [(ngModel)]="newBreak.end_time" type="time"
                      class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs font-mono outline-none focus:border-primary transition-all" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[8px] text-surface-text-muted uppercase font-bold">Minutos</label>
                    <input [(ngModel)]="newBreak.duration_minutes" type="number" min="1" max="240" placeholder="30"
                      class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs font-mono outline-none focus:border-primary transition-all" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[8px] text-surface-text-muted uppercase font-bold">Tipo</label>
                    <select [(ngModel)]="newBreak.break_type"
                      class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs cursor-pointer outline-none focus:border-primary transition-all">
                      <option value="BREAK">Descanso</option>
                      <option value="MEAL">Comida</option>
                      <option value="MAINTENANCE">Mantenimiento</option>
                    </select>
                  </div>
                </div>
                <button (click)="addBreak()" [disabled]="addingBreak()"
                  class="w-full py-2.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 disabled:opacity-50">
                  <mat-icon class="text-xs">{{ addingBreak() ? 'sync' : 'add' }}</mat-icon>
                  Agregar Break
                </button>
              </div>
            }
          </div>
        }

      </div>

      <!-- Footer -->
      <div class="pt-8 mt-auto border-t border-surface-border">
        <div class="flex flex-col gap-3">
          <button (click)="save()" [disabled]="form.invalid || saving()"
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic disabled:opacity-50 disabled:pointer-events-none">
            <mat-icon>{{ saving() ? 'sync' : 'verified' }}</mat-icon>
            {{ saving() ? 'Guardando...' : (isEdit ? 'Actualizar Turno' : 'Registrar Turno') }}
          </button>
          <button type="button" (click)="drawer.close()"
            class="w-full py-4 border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-surface-border transition-all">
            Cerrar
          </button>
        </div>
      </div>

    </div>
  `,
  styles: [`:host { display: block; }`]
})
export class ShiftFormComponent implements OnInit {
  private shiftSvc    = inject(ShiftService);
  private resourceSvc = inject(ResourceService);
  private notif       = inject(NotificationService);
  drawer              = inject(SideDrawerService);
  private fb          = inject(FormBuilder);

  isEdit      = false;
  editShiftId: string | null = null;
  saving      = signal(false);
  resources   = signal<ResourceRead[]>([]);
  resourcesLoading = signal(false);
  currentBreaks = signal<BreakSlot[]>([]);
  showAddBreak  = signal(false);
  addingBreak   = signal(false);

  newBreak: ShiftBreakCreate = {
    code: '', label: '', break_type: 'BREAK',
    start_time: '09:00', end_time: '09:30', duration_minutes: 30,
  };

  form: FormGroup = this.fb.group({
    code:          ['', [Validators.required, Validators.maxLength(20)]],
    name:          ['', [Validators.required, Validators.maxLength(100)]],
    start_time:    ['06:00', Validators.required],
    end_time:      ['14:00', Validators.required],
    is_overnight:  [false],
    break_minutes: [60, [Validators.min(0), Validators.max(480)]],
    resource_id:   [''],
    is_active:     [true],
  });

  set data(val: any) {
    if (!val) return;
    const item = val.item;
    if (item) {
      this.isEdit = true;
      this.editShiftId = item.id;
      this.currentBreaks.set(item.breaks ?? []);
      this.form.patchValue({
        code:          item.code,
        name:          item.name,
        start_time:    item.start_time,
        end_time:      item.end_time,
        is_overnight:  item.is_overnight,
        break_minutes: item.break_minutes,
        resource_id:   item.resource_id ?? '',
        is_active:     item.is_active,
      });
    }
    // Pre-select resource if opened from resource context
    if (val.resourceId) {
      this.form.patchValue({ resource_id: val.resourceId });
    }
  }

  async ngOnInit() {
    this.resourcesLoading.set(true);
    this.resources.set(await this.resourceSvc.listResources() as ResourceRead[]);
    this.resourcesLoading.set(false);
  }

  breakIcon(type?: string): string {
    return BREAK_ICON[type ?? 'BREAK'] ?? 'coffee';
  }

  async save() {
    if (this.form.invalid) return;
    this.saving.set(true);
    const v = this.form.value;
    const body: any = {
      name:          v.name,
      start_time:    v.start_time,
      end_time:      v.end_time,
      is_overnight:  v.is_overnight,
      break_minutes: v.break_minutes,
    };
    if (!this.isEdit) body.code = v.code;

    try {
      if (this.isEdit && this.editShiftId) {
        await this.shiftSvc.updateShift(this.editShiftId, {
          ...body,
          is_active: v.is_active,
        });
        this.notif.success('Éxito', 'Turno actualizado');
      } else {
        const payload = {
          ...body,
          is_overnight: v.is_overnight,
          break_minutes: v.break_minutes,
          ...(v.resource_id ? { resource_id: v.resource_id } : {}),
        };
        await this.shiftSvc.createShift(payload);
        this.notif.success('Éxito', 'Turno creado');
      }
      this.drawer.notifyRefresh();
      this.drawer.close();
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'No se pudo guardar el turno');
    } finally {
      this.saving.set(false);
    }
  }

  async addBreak() {
    if (!this.editShiftId || !this.newBreak.code || !this.newBreak.label) return;
    this.addingBreak.set(true);
    try {
      const created = await this.shiftSvc.createBreak(this.editShiftId, this.newBreak);
      this.currentBreaks.update(list => [...list, created]);
      this.newBreak = { code: '', label: '', break_type: 'BREAK', start_time: '09:00', end_time: '09:30', duration_minutes: 30 };
      this.showAddBreak.set(false);
      this.notif.success('Break agregado', `${created.label}`);
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'No se pudo agregar el break');
    } finally {
      this.addingBreak.set(false);
    }
  }

  async deleteBreak(brk: BreakSlot) {
    if (!this.editShiftId) return;
    if (!confirm(`¿Eliminar el break "${brk.label}"?`)) return;
    try {
      await this.shiftSvc.deleteBreak(this.editShiftId, (brk as any).id);
      this.currentBreaks.update(list => list.filter(b => (b as any).id !== (brk as any).id));
      this.notif.success('Break eliminado', '');
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'No se pudo eliminar');
    }
  }
}
