import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, UOM } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';

@Component({
  selector: 'app-uom-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">
      <!-- Header Section -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/20">
            <mat-icon class="text-2xl">straighten</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              {{ isEdit ? 'Edición de Unidad' : 'Registro de Unidad' }}
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              {{ isEdit ? 'GESTIÓN DE MAGNITUD FÍSICA' : 'NUEVA UNIDAD DE MEDIDA' }}
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
        <form [formGroup]="uomForm" (ngSubmit)="save()" class="space-y-8">
          <div class="space-y-6">
            <div class="space-y-2">
              <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block italic">Atributos de Conversión</label>
              
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Código (ISO) *</label>
                  <input 
                    type="text" 
                    formControlName="code"
                    placeholder="EX: PZA, KG"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase"
                  >
                </div>
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Abreviación</label>
                  <input 
                    type="text" 
                    formControlName="abbreviation"
                    placeholder="EX: pz, kg"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold outline-none focus:border-primary transition-all"
                  >
                </div>
              </div>

              <div class="space-y-2">
                <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Nombre Descriptivo *</label>
                <input 
                  type="text" 
                  formControlName="name"
                  placeholder="Nombre de la unidad..."
                  class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all"
                >
              </div>

              <div class="space-y-2">
                <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Factor de Conversión (Base)</label>
                <div class="relative">
                  <input 
                    type="number" 
                    formControlName="conversion_factor"
                    step="0.00000001"
                    class="w-full pl-4 pr-12 py-3 bg-surface-card border border-surface-border rounded-xl text-xs font-mono text-emerald-500 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-bold"
                  >
                  <mat-icon class="absolute right-4 top-1/2 -translate-y-1/2 text-surface-text-muted text-sm">calculate</mat-icon>
                </div>
                <p class="text-[8px] text-surface-text-muted italic px-1 leading-relaxed">
                  Relación contra la unidad base del sistema (Ej: G → KG = 0.001)
                </p>
              </div>
            </div>

            @if (isEdit && isAdmin()) {
              <div class="pt-6 border-t border-surface-border">
                <button 
                  type="button"
                  (click)="deleteUom()"
                  [disabled]="isDeleting || isSaving()"
                  class="w-full py-3 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 border border-rose-500/20"
                >
                  <mat-icon class="text-xs">delete</mat-icon>
                  <span>{{ isDeleting ? 'Eliminando...' : 'Eliminar Unidad Permanente' }}</span>
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
            [disabled]="uomForm.invalid || isSaving() || (isEdit && !isAdmin())"
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic overflow-hidden group relative"
          >
            <div class="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            <mat-icon class="text-lg">{{ isSaving() ? 'sync' : 'verified' }}</mat-icon>
            <span>{{ isSaving() ? 'Procesando...' : (isEdit ? 'Actualizar Unidad' : 'Registrar Unidad') }}</span>
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
export class UomFormComponent implements OnInit {
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
        this.uomForm.patchValue(val.item);
      }
    }
  }

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

  ngOnInit() {
    const roles = this.auth.roles();
    this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));
    
    if (this.isEdit && !this.isAdmin()) {
      this.uomForm.disable();
    }
  }

  save() {
    if (this.uomForm.invalid) return;

    this.isSaving.set(true);
    const data = this.uomForm.value;

    const request = this.isEdit && this.currentId
        ? this.masterData.updateUom(this.currentId, data)
        : this.masterData.createUom(data);

    request.subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Unidad de medida guardada');
        this.drawerService.notifyRefresh();
        this.drawerService.close();
      },
      error: (err) => {
        this.notifications.error('Error', err.error?.detail || 'No se pudo guardar');
        this.isSaving.set(false);
      }
    });
  }

  deleteUom() {
    if (!this.currentId || !this.isAdmin()) return;
    if (!confirm('¿Eliminar esta unidad de medida permanentemente?')) return;

    this.isDeleting = true;
    this.masterData.deleteUom(this.currentId).subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Unidad eliminada');
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
