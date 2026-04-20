import { Component, EventEmitter, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, Warehouse } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-warehouse-modal',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    @if (isVisible()) {
      <div class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-sm animate-fade-in" (click)="close()"></div>
        
        <div class="relative w-full max-w-md bg-surface-bg border border-surface-border rounded-3xl shadow-2xl animate-slide-up overflow-hidden">
          <!-- Header -->
          <div class="p-6 border-b border-surface-border flex items-center justify-between bg-surface-bg/50">
            <div>
              <h2 class="text-xl font-black text-surface-text uppercase tracking-tighter italic">
                {{ isEdit ? 'Editar Almacén' : 'Nuevo Almacén' }}
              </h2>
              <p class="text-[10px] text-surface-text-muted font-mono uppercase tracking-widest leading-none mt-1">
                Estructura de Almacenamiento
              </p>
            </div>
            <button (click)="close()" class="p-2 hover:bg-surface-border rounded-xl transition-all">
              <mat-icon>close</mat-icon>
            </button>
          </div>

          <!-- Form -->
          <form [formGroup]="warehouseForm" (ngSubmit)="save()" class="p-6 space-y-5">
            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Código</label>
              <input 
                type="text" 
                formControlName="code"
                placeholder="EX: TJ-CENTRAL"
                class="w-full px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              >
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Nombre</label>
              <input 
                type="text" 
                formControlName="name"
                placeholder="Nombre del almacen..."
                class="w-full px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-bold focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              >
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Tipo</label>
                <select 
                  formControlName="type"
                  class="w-full px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-bold focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none cursor-pointer"
                >
                  <option value="PHYSICAL">FISICO</option>
                  <option value="VIRTUAL">VIRTUAL</option>
                  <option value="TRANSIT">TRANSITO</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Capacidad (Unidades)</label>
                <input 
                  type="number" 
                  formControlName="capacity"
                  class="w-full px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                >
              </div>
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
                [disabled]="warehouseForm.invalid || isSaving() || (isEdit && !isAdmin())"
                class="flex-[2] py-4 bg-primary text-white dark:text-slate-950 rounded-2xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/20 disabled:opacity-50"
              >
                {{ isSaving() ? 'Guardando...' : (isEdit ? 'Actualizar' : 'Registrar Almacén') }}
              </button>
            </div>

            @if (isEdit && isAdmin()) {
              <div class="pt-4 border-t border-surface-border">
                <button 
                  type="button"
                  (click)="deleteWarehouse()"
                  [disabled]="isDeleting || isSaving()"
                  class="w-full py-3 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 border border-rose-500/20"
                >
                  <mat-icon class="text-xs">delete</mat-icon>
                  <span>{{ isDeleting ? 'Eliminando...' : 'Eliminar Almacén (Soft-Delete)' }}</span>
                </button>
              </div>
            }
          </form>
        </div>
      </div>
    }
  `,
  styles: [`
    .animate-fade-in { animation: fadeIn 0.15s ease-out; }
    .animate-slide-up { animation: slideUp 0.25s cubic-bezier(0.34, 1.56, 0.64, 1); }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideUp { from { opacity: 0; transform: translateY(15px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
  `]
})
export class WarehouseModalComponent {
  private fb = inject(FormBuilder);
  private masterData = inject(MasterDataService);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);

  @Output() saved = new EventEmitter<Warehouse>();

  isVisible = signal(false);
  isSaving = signal(false);
  isDeleting = false;
  isEdit = false;
  isAdmin = signal(false);
  currentId: string | null = null;

  warehouseForm: FormGroup = this.fb.group({
    code: ['', [Validators.required]],
    name: ['', [Validators.required]],
    type: ['PHYSICAL', [Validators.required]],
    capacity: [1000000, [Validators.required, Validators.min(0)]]
  });

  open(warehouse?: Warehouse) {
    const roles = this.auth.roles();
    this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));
    
    this.isEdit = !!warehouse;
    this.currentId = warehouse?.id || null;
    if (warehouse) {
      this.warehouseForm.patchValue(warehouse);
      if (!this.isAdmin()) this.warehouseForm.disable();
      else this.warehouseForm.enable();
    } else {
      this.warehouseForm.enable();
      this.warehouseForm.reset({ type: 'PHYSICAL', capacity: 1000000 });
    }
    this.isVisible.set(true);
  }

  close() {
    this.isVisible.set(false);
    this.isSaving.set(false);
  }

  save() {
    if (this.warehouseForm.invalid) return;

    this.isSaving.set(true);
    const data = this.warehouseForm.value;

    const request = this.isEdit && this.currentId
        ? this.masterData.updateWarehouse(this.currentId, data)
        : this.masterData.createWarehouse(data);

    request.subscribe({
      next: (response) => {
        this.notifications.success('Éxito', this.isEdit ? 'Almacén actualizado' : 'Almacén creado');
        this.saved.emit(response.data);
        this.close();
      },
      error: (err) => {
        this.notifications.error('Error', 'No se pudo guardar: ' + (err.error?.detail || 'Error de servidor'));
        this.isSaving.set(false);
      }
    });
  }

  deleteWarehouse() {
    if (!this.currentId || !this.isAdmin()) return;
    if (!confirm('¿Eliminar este almacén?')) return;

    this.isDeleting = true;
    this.masterData.deleteWarehouse(this.currentId).subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Almacén eliminado');
        this.saved.emit({ id: this.currentId } as Warehouse);
        this.close();
      },
      error: () => {
        this.notifications.error('Error', 'No se pudo eliminar');
        this.isDeleting = false;
      }
    });
  }
}
