import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, Warehouse } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';

@Component({
  selector: 'app-warehouse-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">
      <!-- Header Section -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/20">
            <mat-icon class="text-2xl">warehouse</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              {{ isEdit ? 'Control de Almacén' : 'Nuevo Almacén' }}
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              {{ isEdit ? 'GESTIÓN DE NODOS LOGÍSTICOS' : 'REGISTRO DE INFRAESTRUCTURA FÍSICA' }}
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
        <form [formGroup]="warehouseForm" (ngSubmit)="save()" class="space-y-8">
          <div class="space-y-6">
            <div class="space-y-2">
              <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block italic">Identificación del Nodo</label>
              
              <div class="space-y-2">
                <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Código Forense *</label>
                <input 
                  type="text" 
                  formControlName="code"
                  placeholder="EX: TJ-CENTRAL"
                  class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase"
                >
              </div>

              <div class="space-y-2">
                <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Nombre Comercial / Referencia *</label>
                <input 
                  type="text" 
                  formControlName="name"
                  placeholder="Nombre descriptivo..."
                  class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all"
                >
              </div>
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block italic">Atributos Operativos</label>
              
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Tipo de Nodo</label>
                  <select 
                    formControlName="type"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all cursor-pointer"
                  >
                    <option value="PHYSICAL">FISICO</option>
                    <option value="VIRTUAL">VIRTUAL</option>
                    <option value="TRANSIT">TRANSITO</option>
                  </select>
                </div>
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Capacidad (Unidades)</label>
                  <input 
                    type="number" 
                    formControlName="capacity"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold outline-none focus:border-primary transition-all text-right"
                  >
                </div>
              </div>
            </div>

            @if (isEdit && isAdmin()) {
              <div class="pt-6 border-t border-surface-border">
                <button 
                  type="button"
                  (click)="deleteWarehouse()"
                  [disabled]="isDeleting || isSaving()"
                  class="w-full py-3 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 border border-rose-500/20"
                >
                  <mat-icon class="text-xs">delete</mat-icon>
                  <span>{{ isDeleting ? 'Eliminando...' : 'Eliminar Almacén Permanente' }}</span>
                </button>
              </div>
            }
          </div>
        </form>
      </div>

      <!-- Sticky Footer Action -->
      <div class="pt-8 mt-auto border-t border-surface-border">
        <div class="flex flex-col gap-3">
          <button 
            (click)="save()"
            [disabled]="warehouseForm.invalid || isSaving() || (isEdit && !isAdmin())"
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic overflow-hidden group relative"
          >
            <div class="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            <mat-icon class="text-lg">{{ isSaving() ? 'sync' : 'verified' }}</mat-icon>
            <span>{{ isSaving() ? 'Procesando...' : (isEdit ? 'Sincronizar Nodo' : 'Registrar Almacén') }}</span>
          </button>
          
          <button 
            type="button"
            (click)="drawerService.close()"
            class="w-full py-4 border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-surface-border transition-all"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  `
})
export class WarehouseFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private masterData = inject(MasterDataService);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);
  drawerService = inject(SideDrawerService);

  set data(val: any) {
    if (val) {
      this.isEdit = !!val.item;
      this.currentId = val.item?.id || null;
      if (val.item) {
        this.warehouseForm.patchValue(val.item);
      }
    }
  }

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

  ngOnInit() {
    const roles = this.auth.roles();
    this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));
    
    if (this.isEdit && !this.isAdmin()) {
      this.warehouseForm.disable();
    }
  }

  save() {
    if (this.warehouseForm.invalid) return;

    this.isSaving.set(true);
    const data = this.warehouseForm.value;

    const request = this.isEdit && this.currentId
        ? this.masterData.updateWarehouse(this.currentId, data)
        : this.masterData.createWarehouse(data);

    request.subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Almacén guardado exitosamente');
        this.drawerService.notifyRefresh();
        this.drawerService.close();
      },
      error: (err) => {
        this.notifications.error('Error', err.error?.detail || 'No se pudo guardar');
        this.isSaving.set(false);
      }
    });
  }

  deleteWarehouse() {
    if (!this.currentId || !this.isAdmin()) return;
    if (!confirm('¿Eliminar este almacén permanentemente?')) return;

    this.isDeleting = true;
    this.masterData.deleteWarehouse(this.currentId).subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Almacén eliminado');
        this.drawerService.notifyRefresh();
        this.drawerService.close();
      },
      error: () => {
        this.notifications.error('Error', 'No se pudo eliminar');
        this.isDeleting = false;
      }
    });
  }
}
