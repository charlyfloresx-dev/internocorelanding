import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { ResourceService } from '../../core/services/resource.service';
import { NotificationService } from '../../core/services/notification.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { ProductionAreaRead } from '../../core/models/mes.types';

@Component({
  selector: 'app-resource-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">

      <!-- Header -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/20">
            <mat-icon class="text-2xl">grid_view</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              {{ isEdit ? 'Editar Recurso' : 'Nuevo Recurso' }}
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              CELDA · MÁQUINA · ÁREA · LÍNEA
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
        <form [formGroup]="form" class="space-y-5">

          <!-- Código -->
          <div class="space-y-2">
            <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">
              Código * <span class="text-primary font-mono">(máx. 13 chars)</span>
            </label>
            <input
              type="text"
              formControlName="code"
              placeholder="CELDA-58D"
              [readonly]="isEdit"
              class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase"
              [class.opacity-60]="isEdit"
            />
          </div>

          <!-- Nombre -->
          <div class="space-y-2">
            <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Nombre *</label>
            <input
              type="text"
              formControlName="name"
              placeholder="Celda de Ensamble 58D"
              class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-sm font-bold outline-none focus:border-primary transition-all"
            />
          </div>

          <!-- Tipo + Capacidad -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Tipo</label>
              <select
                formControlName="resource_type"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-bold outline-none focus:border-primary transition-all cursor-pointer"
              >
                <option value="">— Sin tipo —</option>
                <option value="CELL">CELL — Celda</option>
                <option value="MACHINE">MACHINE — Máquina</option>
                <option value="LINE">LINE — Línea</option>
                <option value="AREA">AREA — Área</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">
                Capacidad <span class="text-surface-text-muted/60 font-mono">(pzas/hr)</span>
              </label>
              <input
                type="number"
                formControlName="capacity"
                placeholder="240"
                min="0"
                step="1"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs font-mono outline-none focus:border-primary transition-all"
              />
            </div>
          </div>

          <!-- Área de Producción -->
          <div class="space-y-2">
            <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Área de Producción</label>
            @if (areasLoading()) {
              <div class="h-12 bg-surface-card rounded-xl animate-pulse"></div>
            } @else {
              <select
                formControlName="production_area_id"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs outline-none focus:border-primary transition-all cursor-pointer"
              >
                <option value="">— Sin área —</option>
                @for (area of areas(); track area.id) {
                  <option [value]="area.id">{{ area.name }}</option>
                }
              </select>
            }
          </div>

          <!-- Descripción -->
          <div class="space-y-2">
            <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest block">Descripción</label>
            <textarea
              formControlName="description"
              placeholder="Descripción opcional del recurso..."
              rows="3"
              class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-xs outline-none focus:border-primary transition-all resize-none"
            ></textarea>
          </div>

          @if (isEdit) {
            <div class="flex items-center gap-3 p-4 bg-surface-card rounded-xl border border-surface-border">
              <input
                type="checkbox"
                formControlName="active"
                id="activeToggle"
                class="w-4 h-4 rounded accent-primary cursor-pointer"
              />
              <label for="activeToggle" class="text-xs font-bold text-surface-text cursor-pointer">
                Recurso activo
              </label>
            </div>
          }

        </form>
      </div>

      <!-- Footer -->
      <div class="pt-8 mt-auto border-t border-surface-border">
        <div class="flex flex-col gap-3">
          <button
            (click)="save()"
            [disabled]="form.invalid || saving()"
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic overflow-hidden group relative disabled:opacity-50 disabled:pointer-events-none"
          >
            <mat-icon class="text-lg">{{ saving() ? 'sync' : 'verified' }}</mat-icon>
            <span>{{ saving() ? 'Guardando...' : (isEdit ? 'Actualizar Recurso' : 'Registrar Recurso') }}</span>
          </button>
          <button
            type="button"
            (click)="drawer.close()"
            class="w-full py-4 border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-surface-border transition-all"
          >
            Cancelar
          </button>
        </div>
      </div>

    </div>
  `,
  styles: [`:host { display: block; }`]
})
export class ResourceFormComponent implements OnInit {
  private svc    = inject(ResourceService);
  private notif  = inject(NotificationService);
  drawer         = inject(SideDrawerService);
  private fb     = inject(FormBuilder);

  isEdit  = false;
  editCode: string | null = null;
  saving  = signal(false);
  areas   = signal<ProductionAreaRead[]>([]);
  areasLoading = signal(false);

  form: FormGroup = this.fb.group({
    code:               ['', [Validators.required, Validators.maxLength(13)]],
    name:               ['', [Validators.required, Validators.maxLength(100)]],
    resource_type:      [''],
    capacity:           [null],
    production_area_id: [null],
    description:        [null],
    active:             [true],
  });

  set data(val: any) {
    if (!val) return;
    if (val.item) {
      this.isEdit = true;
      this.editCode = val.item.code;
      this.form.patchValue({
        code:               val.item.code,
        name:               val.item.name,
        resource_type:      val.item.resource_type ?? '',
        capacity:           val.item.capacity,
        production_area_id: val.item.production_area_id,
        description:        val.item.description,
        active:             val.item.active,
      });
    }
  }

  async ngOnInit() {
    this.areasLoading.set(true);
    this.areas.set(await this.svc.listProductionAreas());
    this.areasLoading.set(false);
  }

  async save() {
    if (this.form.invalid) return;
    this.saving.set(true);
    const v = this.form.value;

    const payload: any = {
      name: v.name,
      resource_type: v.resource_type || null,
      capacity: v.capacity ? Number(v.capacity) : null,
      production_area_id: v.production_area_id || null,
      description: v.description || null,
    };

    try {
      if (this.isEdit && this.editCode) {
        await this.svc.updateResource(this.editCode, { ...payload, active: v.active });
        this.notif.success('Éxito', 'Recurso actualizado');
      } else {
        await this.svc.createResource({ code: v.code, ...payload });
        this.notif.success('Éxito', 'Recurso creado');
      }
      this.drawer.notifyRefresh();
      this.drawer.close();
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'No se pudo guardar el recurso');
    } finally {
      this.saving.set(false);
    }
  }
}
