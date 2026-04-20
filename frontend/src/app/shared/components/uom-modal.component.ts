import { Component, EventEmitter, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, UOM } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-uom-modal',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    @if (isVisible()) {
      <div class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-sm animate-fade-in" (click)="close()"></div>
        
        <!-- Modal Content -->
        <div class="relative w-full max-w-md bg-surface-bg border border-surface-border rounded-3xl shadow-2xl shadow-primary/10 overflow-hidden animate-slide-up">
          <!-- Header -->
          <div class="p-6 border-b border-surface-border flex items-center justify-between bg-surface-bg/50">
            <div>
              <h2 class="text-xl font-black text-surface-text uppercase tracking-tighter italic">
                {{ isEdit ? 'Editar Unidad' : 'Nueva Unidad' }}
              </h2>
              <p class="text-[10px] text-surface-text-muted font-mono uppercase tracking-widest leading-none mt-1">
                Configuración de Magnitud Industrial
              </p>
            </div>
            <button (click)="close()" class="p-2 hover:bg-surface-border rounded-xl transition-all text-surface-text-muted hover:text-surface-text">
              <mat-icon>close</mat-icon>
            </button>
          </div>

          <!-- Form -->
          <form [formGroup]="uomForm" (ngSubmit)="save()" class="p-6 space-y-6">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Código (ISO)</label>
                <input 
                  type="text" 
                  formControlName="code"
                  placeholder="EX: PZA, KG"
                  class="w-full px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                  [class.border-red-500]="uomForm.get('code')?.touched && uomForm.get('code')?.invalid"
                >
              </div>
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Abreviación</label>
                <input 
                  type="text" 
                  formControlName="abbreviation"
                  placeholder="EX: pz, kg"
                  class="w-full px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                >
              </div>
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Nombre Descriptivo</label>
              <input 
                type="text" 
                formControlName="name"
                placeholder="Nombre de la unidad..."
                class="w-full px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-bold focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                [class.border-red-500]="uomForm.get('name')?.touched && uomForm.get('name')?.invalid"
              >
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1 italic">Factor de Conversión (Base)</label>
              <div class="relative">
                <input 
                  type="number" 
                  formControlName="conversion_factor"
                  step="0.00000001"
                  class="w-full pl-4 pr-12 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono text-emerald-500 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-bold"
                >
                <mat-icon class="absolute right-4 top-1/2 -translate-y-1/2 text-surface-text-muted text-sm">calculate</mat-icon>
              </div>
              <p class="text-[9px] text-surface-text-muted italic px-1">
                Relación contra la unidad base del sistema (Ej: G$\rightarrow$KG = 0.001)
              </p>
            </div>

            <!-- Actions -->
            <div class="flex gap-3 pt-4">
              <button 
                type="button"
                (click)="close()"
                class="flex-1 py-4 border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-surface-border transition-all"
              >
                Cancelar
              </button>
              <button 
                type="submit"
                [disabled]="uomForm.invalid || isSaving() || (isEdit && !isAdmin())"
                class="flex-[2] py-4 bg-primary text-white dark:text-slate-950 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg shadow-primary/20 disabled:opacity-50 disabled:grayscale disabled:scale-100"
              >
                {{ isSaving() ? 'Guardando...' : (isEdit ? 'Actualizar' : 'Registrar Unidad') }}
              </button>
            </div>

            @if (isEdit && isAdmin()) {
              <div class="pt-4 border-t border-surface-border">
                <button 
                  type="button"
                  (click)="deleteUom()"
                  [disabled]="isDeleting || isSaving()"
                  class="w-full py-3 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 border border-rose-500/20"
                >
                  <mat-icon class="text-xs">delete</mat-icon>
                  <span>{{ isDeleting ? 'Eliminando...' : 'Eliminar Unidad' }}</span>
                </button>
              </div>
            }
          </form>
        </div>
      </div>
    }
  `,
  styles: [`
    .animate-fade-in { animation: fadeIn 0.2s ease-out; }
    .animate-slide-up { animation: slideUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideUp { from { opacity: 0; transform: translateY(20px) scale(0.95); } to { opacity: 1; transform: translateY(0) scale(1); } }
  `]
})
export class UomModalComponent {
  private fb = inject(FormBuilder);
  private masterData = inject(MasterDataService);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);

  @Output() saved = new EventEmitter<UOM>();

  isVisible = signal(false);
  isSaving = signal(false);
  isDeleting = false;
  isEdit = false;
  isAdmin = signal(false);
  currentId: string | null = null;

  uomForm: FormGroup = this.fb.group({
    code: ['', [Validators.required, Validators.maxLength(10)]],
    name: ['', [Validators.required, Validators.maxLength(100)]],
    abbreviation: ['', [Validators.maxLength(10)]],
    conversion_factor: [1.0, [Validators.required, Validators.min(0.00000001)]]
  });

  open(uom?: UOM) {
    const roles = this.auth.roles();
    this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));

    this.isEdit = !!uom;
    this.currentId = uom?.id || null;
    
    if (uom) {
      this.uomForm.patchValue(uom);
      if (!this.isAdmin()) this.uomForm.disable();
      else this.uomForm.enable();
    } else {
      this.uomForm.enable();
      this.uomForm.reset({ conversion_factor: 1.0 });
    }
    
    this.isVisible.set(true);
  }

  close() {
    this.isVisible.set(false);
    this.isSaving.set(false);
  }

  save() {
    if (this.uomForm.invalid) return;

    this.isSaving.set(true);
    const data = this.uomForm.value;

    const request = this.isEdit && this.currentId
        ? this.masterData.updateUom(this.currentId, data)
        : this.masterData.createUom(data);

    request.subscribe({
      next: (response) => {
        this.notifications.success(
          this.isEdit ? 'Unidad actualizada' : 'Unidad creada',
          `La unidad ${data.code} ha sido guardada exitosamente.`
        );
        this.saved.emit(response.data);
        this.close();
      },
      error: (err) => {
        console.error('Error saving UOM:', err);
        this.notifications.error('Error al guardar', err.error?.detail || 'No se pudo procesar la solicitud.');
        this.isSaving.set(false);
      }
    });
  }

  deleteUom() {
    if (!this.currentId || !this.isAdmin()) return;
    if (!confirm('¿Eliminar esta unidad de medida?')) return;

    this.isDeleting = true;
    this.masterData.deleteUom(this.currentId).subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Unidad eliminada');
        this.saved.emit({ id: this.currentId } as UOM);
        this.close();
      },
      error: () => {
        this.notifications.error('Error', 'No se pudo eliminar');
        this.isDeleting = false;
      }
    });
  }
}
