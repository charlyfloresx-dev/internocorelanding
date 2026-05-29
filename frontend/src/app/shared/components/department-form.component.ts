import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { DepartmentService, Department } from '../../core/services/department.service';
import { NotificationService } from '../../core/services/notification.service';

@Component({
  selector: 'app-department-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">

      <!-- Header -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/20">
            <mat-icon class="text-2xl">corporate_fare</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              {{ isEdit ? 'Editar Departamento' : 'Nuevo Departamento' }}
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              {{ isEdit ? 'ACTUALIZAR ÁREA ORGANIZACIONAL' : 'REGISTRAR ÁREA DE EMPRESA' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Form -->
      <div class="flex-1 overflow-y-auto pr-2">
        <form [formGroup]="form" (ngSubmit)="save()" class="space-y-6">

          <div class="space-y-2">
            <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] block italic">
              Identificación
            </label>

            <div class="space-y-2">
              <label class="text-[9px] font-bold text-surface-text-muted uppercase block">Código *</label>
              <input
                type="text"
                formControlName="code"
                placeholder="Ej: PROD-A, QC-01, MANT"
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase"
                [class.border-rose-400]="form.get('code')?.invalid && form.get('code')?.touched"
              >
              @if (form.get('code')?.invalid && form.get('code')?.touched) {
                <p class="text-[9px] text-rose-400 font-bold">Código requerido (máx. 20 caracteres)</p>
              }
            </div>

            <div class="space-y-2">
              <label class="text-[9px] font-bold text-surface-text-muted uppercase block">Nombre *</label>
              <input
                type="text"
                formControlName="name"
                placeholder="Nombre descriptivo del área..."
                class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all"
                [class.border-rose-400]="form.get('name')?.invalid && form.get('name')?.touched"
              >
              @if (form.get('name')?.invalid && form.get('name')?.touched) {
                <p class="text-[9px] text-rose-400 font-bold">Nombre requerido (máx. 100 caracteres)</p>
              }
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] block italic">
              Descripción
            </label>
            <textarea
              formControlName="description"
              rows="3"
              placeholder="Descripción opcional del área o sus responsabilidades..."
              class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] outline-none focus:border-primary transition-all resize-none"
            ></textarea>
          </div>

          @if (isEdit) {
            <div class="flex items-center justify-between p-4 bg-surface-card border border-surface-border rounded-xl">
              <div>
                <p class="text-[10px] font-black text-surface-text uppercase tracking-widest">Estado</p>
                <p class="text-[9px] text-surface-text-muted mt-0.5">Departamentos inactivos no aparecen en selectores</p>
              </div>
              <button
                type="button"
                (click)="toggleActive()"
                class="relative w-12 h-6 rounded-full transition-colors duration-200 focus:outline-none"
                [class.bg-primary]="form.get('is_active')?.value"
                [class.bg-surface-border]="!form.get('is_active')?.value"
              >
                <span
                  class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
                  [class.translate-x-6]="form.get('is_active')?.value"
                ></span>
              </button>
            </div>
          }

          @if (conflictError()) {
            <div class="p-4 bg-rose-50 border border-rose-200 rounded-xl">
              <p class="text-[10px] text-rose-600 font-bold">{{ conflictError() }}</p>
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
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic overflow-hidden group relative disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            <div class="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            <mat-icon class="text-lg">{{ saving() ? 'sync' : 'verified' }}</mat-icon>
            <span>{{ saving() ? 'Guardando...' : (isEdit ? 'Guardar Cambios' : 'Crear Departamento') }}</span>
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
  `
})
export class DepartmentFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private deptService = inject(DepartmentService);
  private notifications = inject(NotificationService);
  drawer = inject(SideDrawerService);

  saving = signal(false);
  conflictError = signal<string | null>(null);
  isEdit = false;
  private currentId: string | null = null;

  form = this.fb.group({
    code:        ['', [Validators.required, Validators.maxLength(20)]],
    name:        ['', [Validators.required, Validators.maxLength(100)]],
    description: [''],
    is_active:   [true]
  });

  set data(val: any) {
    if (val?.item) {
      const dept: Department = val.item;
      this.isEdit = true;
      this.currentId = dept.id;
      this.form.patchValue({
        code:        dept.code,
        name:        dept.name,
        description: dept.description ?? '',
        is_active:   dept.is_active
      });
    }
  }

  ngOnInit() {}

  toggleActive() {
    const current = this.form.get('is_active')?.value;
    this.form.patchValue({ is_active: !current });
  }

  save() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.conflictError.set(null);
    this.saving.set(true);

    const payload = {
      code:        (this.form.value.code ?? '').toUpperCase(),
      name:        this.form.value.name ?? '',
      description: this.form.value.description || null,
      is_active:   this.form.value.is_active ?? true
    };

    const req = this.isEdit && this.currentId
      ? this.deptService.update(this.currentId, payload)
      : this.deptService.create(payload);

    req.subscribe({
      next: () => {
        this.notifications.success('Éxito', this.isEdit ? 'Departamento actualizado' : 'Departamento creado');
        this.deptService.saving.set(false);
        this.saving.set(false);
        this.drawer.notifyRefresh();
        this.drawer.close();
      },
      error: (err) => {
        this.saving.set(false);
        this.deptService.saving.set(false);
        if (err.status === 409) {
          this.conflictError.set(`El código '${payload.code}' ya existe en esta empresa.`);
        } else {
          this.notifications.error('Error', err.error?.detail || 'No se pudo guardar');
        }
      }
    });
  }
}
