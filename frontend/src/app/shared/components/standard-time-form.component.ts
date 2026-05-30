import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { StandardTimeService, StandardTime } from '../../core/services/standard-time.service';
import { NotificationService } from '../../core/services/notification.service';

@Component({
  selector: 'app-standard-time-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">

      <!-- Header -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/20">
            <mat-icon class="text-2xl">timer</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              {{ isEdit ? 'Editar Tiempo' : 'Nuevo Tiempo Estándar' }}
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              {{ isEdit ? 'ACTUALIZAR OPERACIÓN' : 'REGISTRAR OPERACIÓN' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Form -->
      <div class="flex-1 overflow-y-auto pr-2">
        <form [formGroup]="form" (ngSubmit)="save()" class="space-y-5">

          <!-- Item Code -->
          <div class="space-y-2">
            <label class="text-[9px] font-bold text-surface-text-muted uppercase block">Código de Ítem *</label>
            <input
              type="text"
              formControlName="item_code"
              placeholder="Ej: TURBO-001, PART-SKU-A"
              class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase"
              [class.border-rose-400]="form.get('item_code')?.invalid && form.get('item_code')?.touched"
            >
            @if (form.get('item_code')?.invalid && form.get('item_code')?.touched) {
              <p class="text-[9px] text-rose-400 font-bold">Código de ítem requerido</p>
            }
          </div>

          <!-- Operation Name + Sequence -->
          <div class="flex gap-3">
            <div class="flex-1 space-y-2">
              <label class="text-[9px] font-bold text-surface-text-muted uppercase block">Nombre de Operación *</label>
              <input
                type="text"
                formControlName="operation_name"
                placeholder="Ej: SOLDADURA, ENSAMBLE"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold text-surface-text outline-none focus:border-primary transition-all"
                [class.border-rose-400]="form.get('operation_name')?.invalid && form.get('operation_name')?.touched"
              >
              @if (form.get('operation_name')?.invalid && form.get('operation_name')?.touched) {
                <p class="text-[9px] text-rose-400 font-bold">Requerido</p>
              }
            </div>
            <div class="w-24 space-y-2">
              <label class="text-[9px] font-bold text-surface-text-muted uppercase block">
                Secuencia
                <span class="text-slate-500 normal-case font-normal">(orden)</span>
              </label>
              <input
                type="number"
                formControlName="sequence_number"
                step="10"
                min="1"
                placeholder="10"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all"
              >
            </div>
          </div>

          <!-- Set Time Hours -->
          <div class="space-y-2">
            <label class="text-[9px] font-bold text-surface-text-muted uppercase block">Tiempo de Preparación (horas) *</label>
            <input
              type="number"
              formControlName="set_time_hours"
              placeholder="Ej: 0.5"
              step="0.0001"
              min="0.0001"
              class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all"
              [class.border-rose-400]="form.get('set_time_hours')?.invalid && form.get('set_time_hours')?.touched"
            >
            @if (form.get('set_time_hours')?.invalid && form.get('set_time_hours')?.touched) {
              <p class="text-[9px] text-rose-400 font-bold">Tiempo de preparación requerido (> 0)</p>
            }
          </div>

          <!-- Cycle Time Seconds -->
          <div class="space-y-2">
            <label class="text-[9px] font-bold text-surface-text-muted uppercase block">
              Tiempo de Ciclo (segundos)
              <span class="text-slate-500 normal-case font-normal ml-1">— opcional, para TakTime</span>
            </label>
            <input
              type="number"
              formControlName="cycle_time_seconds"
              placeholder="Ej: 45"
              step="1"
              min="1"
              class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all"
            >
            <p class="text-[9px] text-surface-text-muted">NULL = operación sin estudio de tiempos. MES usará set_time_hours como respaldo.</p>
          </div>

        </form>
      </div>

      <!-- Footer -->
      <div class="pt-6 border-t border-surface-border flex gap-3">
        <button
          type="button"
          (click)="drawer.close()"
          class="flex-1 py-3 rounded-xl border border-surface-border text-surface-text-muted text-[11px] font-bold uppercase hover:bg-surface-card transition-all"
        >
          Cancelar
        </button>
        <button
          type="button"
          (click)="save()"
          [disabled]="form.invalid || stSvc.saving()"
          class="flex-1 py-3 rounded-xl bg-primary text-white text-[11px] font-black uppercase tracking-widest hover:bg-primary/90 transition-all disabled:opacity-40 flex items-center justify-center gap-2"
        >
          @if (stSvc.saving()) {
            <mat-icon class="text-base animate-spin">refresh</mat-icon>
          }
          {{ isEdit ? 'Actualizar' : 'Guardar' }}
        </button>
      </div>

    </div>
  `
})
export class StandardTimeFormComponent implements OnInit {
  readonly drawer = inject(SideDrawerService);
  readonly stSvc = inject(StandardTimeService);
  private notify = inject(NotificationService);
  private fb = inject(FormBuilder);

  isEdit = false;
  private editId: string | null = null;

  form = this.fb.group({
    item_code: ['', [Validators.required, Validators.maxLength(100)]],
    operation_name: ['', [Validators.required, Validators.maxLength(100)]],
    sequence_number: [10, [Validators.required, Validators.min(1)]],
    set_time_hours: [null as number | null, [Validators.required, Validators.min(0.0001)]],
    cycle_time_seconds: [null as number | null],
  });

  set data(val: StandardTime | null) {
    if (!val) return;
    this.isEdit = true;
    this.editId = val.id;
    this.form.patchValue({
      item_code: val.item_code,
      operation_name: val.operation_name,
      sequence_number: val.sequence_number,
      set_time_hours: val.set_time_hours,
      cycle_time_seconds: val.cycle_time_seconds,
    });
  }

  ngOnInit(): void {
    const d = this.drawer.data();
    if (d) this.data = d as StandardTime;
  }

  async save(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const v = this.form.getRawValue();
    try {
      if (this.isEdit && this.editId) {
        await this.stSvc.update(this.editId, {
          operation_name: v.operation_name!,
          sequence_number: v.sequence_number ?? 10,
          set_time_hours: v.set_time_hours!,
          cycle_time_seconds: v.cycle_time_seconds ?? undefined,
        });
        this.notify.success('Tiempo actualizado', v.operation_name ?? '');
      } else {
        await this.stSvc.create({
          item_code: v.item_code!.toUpperCase(),
          operation_name: v.operation_name!,
          sequence_number: v.sequence_number ?? 10,
          set_time_hours: v.set_time_hours!,
          cycle_time_seconds: v.cycle_time_seconds,
        });
        this.notify.success('Tiempo estándar creado', `${v.item_code} · ${v.operation_name}`);
      }
      this.drawer.notifyRefresh();
      this.drawer.close();
    } catch {
      this.notify.error('Error al guardar', 'Verifica los datos e inténtalo de nuevo.');
    }
  }
}
