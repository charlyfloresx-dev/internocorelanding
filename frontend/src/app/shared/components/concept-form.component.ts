import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, Concept } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';

@Component({
  selector: 'app-concept-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">
      <!-- Header Section -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/20">
            <mat-icon class="text-2xl">psychology</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              {{ isEdit ? 'Lógica de Operación' : 'Nuevo Concepto' }}
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              {{ isEdit ? 'CONFIGURACIÓN DE REGLAS TRANSACCIONALES' : 'ALTA DE LÓGICA DE INVENTARIO' }}
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
        <form [formGroup]="conceptForm" (ngSubmit)="save()" class="space-y-8">
          <div class="space-y-6">
            <div class="space-y-2">
              <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block italic">Atributos del Concepto</label>
              
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Código *</label>
                  <input 
                    type="text" 
                    formControlName="code"
                    placeholder="EX: COMPRA-DIR"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase"
                  >
                </div>
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Dirección *</label>
                  <select 
                    formControlName="type"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all cursor-pointer"
                  >
                    <option value="ENTRY">ENTRADA (IN)</option>
                    <option value="OUTPUT">SALIDA (OUT)</option>
                    <option value="TRANSFER">TRANSFERENCIA</option>
                  </select>
                </div>
              </div>

              <div class="space-y-2">
                <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Nombre Descriptivo *</label>
                <input 
                  type="text" 
                  formControlName="name"
                  placeholder="Descripción de la operación..."
                  class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all"
                >
              </div>
            </div>

            <!-- Business Rules -->
            <div class="space-y-3">
              <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] block italic">Smart Logic (Reglas Dinámicas)</label>
              
              <div class="grid grid-cols-1 gap-3">
                <div 
                  (click)="toggleControl('requires_external_entity')"
                  [class.border-primary]="conceptForm.get('requires_external_entity')?.value"
                  class="p-4 bg-surface-card border border-surface-border rounded-2xl cursor-pointer hover:bg-primary/5 transition-all flex items-center gap-4 group"
                >
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center transition-all"
                       [class.bg-primary/10]="conceptForm.get('requires_external_entity')?.value"
                       [class.bg-surface-bg]="!conceptForm.get('requires_external_entity')?.value">
                    <mat-icon [class.text-primary]="conceptForm.get('requires_external_entity')?.value" class="text-surface-text-muted">person_search</mat-icon>
                  </div>
                  <div class="flex-1 leading-none">
                    <p class="text-[10px] font-black uppercase tracking-tighter" [class.text-primary]="conceptForm.get('requires_external_entity')?.value">Socio Comercial Requerido</p>
                    <p class="text-[8px] text-surface-text-muted font-mono uppercase mt-1">Habilita selector de Cliente/Proveedor</p>
                  </div>
                  @if (conceptForm.get('requires_external_entity')?.value) {
                    <mat-icon class="text-primary text-sm">check_circle</mat-icon>
                  }
                </div>

                <div 
                  (click)="toggleControl('requires_target_warehouse')"
                  [class.border-primary]="conceptForm.get('requires_target_warehouse')?.value"
                  class="p-4 bg-surface-card border border-surface-border rounded-2xl cursor-pointer hover:bg-primary/5 transition-all flex items-center gap-4 group"
                >
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center transition-all"
                       [class.bg-primary/10]="conceptForm.get('requires_target_warehouse')?.value"
                       [class.bg-surface-bg]="!conceptForm.get('requires_target_warehouse')?.value">
                    <mat-icon [class.text-primary]="conceptForm.get('requires_target_warehouse')?.value" class="text-surface-text-muted">near_me</mat-icon>
                  </div>
                  <div class="flex-1 leading-none">
                    <p class="text-[10px] font-black uppercase tracking-tighter" [class.text-primary]="conceptForm.get('requires_target_warehouse')?.value">Almacén Destino Requerido</p>
                    <p class="text-[8px] text-surface-text-muted font-mono uppercase mt-1">Habilita lógica de transferencia interna</p>
                  </div>
                  @if (conceptForm.get('requires_target_warehouse')?.value) {
                    <mat-icon class="text-primary text-sm">check_circle</mat-icon>
                  }
                </div>
              </div>
            </div>

            @if (isEdit && isAdmin()) {
              <div class="pt-6 border-t border-surface-border">
                <button 
                  type="button"
                  (click)="deleteConcept()"
                  [disabled]="isDeleting() || isSaving()"
                  class="w-full py-3 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 border border-rose-500/20"
                >
                  <mat-icon class="text-xs">delete</mat-icon>
                  <span>{{ isDeleting() ? 'Eliminando...' : 'Eliminar Concepto Permanente' }}</span>
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
            [disabled]="conceptForm.invalid || isSaving() || (isEdit && !isAdmin())"
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic overflow-hidden group relative"
          >
            <div class="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            <mat-icon class="text-lg">{{ isSaving() ? 'sync' : 'verified' }}</mat-icon>
            <span>{{ isSaving() ? 'Procesando...' : (isEdit ? 'Sincronizar Lógica' : 'Registrar Concepto') }}</span>
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
export class ConceptFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private masterData = inject(MasterDataService);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);
  drawerService = inject(SideDrawerService);

  set data(val: any) {
    if (val) {
      this.isEdit = !!val.concept;
      this.currentId = val.concept?.id || null;
      if (val.concept) {
        this.conceptForm.patchValue(val.concept);
      }
    }
  }

  isSaving = signal(false);
  isDeleting = signal(false);
  isEdit = false;
  isAdmin = signal(false);
  currentId: string | null = null;

  conceptForm: FormGroup = this.fb.group({
    code: ['', [Validators.required]],
    name: ['', [Validators.required]],
    type: ['ENTRY', [Validators.required]],
    requires_external_entity: [false],
    requires_target_warehouse: [false]
  });

  ngOnInit() {
    const roles = this.auth.roles();
    this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));
    
    if (this.isEdit && !this.isAdmin()) {
      this.conceptForm.disable();
    }
  }

  toggleControl(controlName: string) {
    if (this.isEdit && !this.isAdmin()) return;
    const control = this.conceptForm.get(controlName);
    if (control) {
      control.setValue(!control.value);
    }
  }

  save() {
    if (this.conceptForm.invalid || this.isSaving()) return;

    this.isSaving.set(true);
    const data = this.conceptForm.value;

    const request = this.isEdit && this.currentId
        ? this.masterData.updateConcept(this.currentId, data)
        : this.masterData.createConcept(data);

    request.subscribe({
      next: () => {
        this.notifications.success('Éxito', this.isEdit ? 'Concepto actualizado' : 'Concepto registrado');
        this.drawerService.notifyRefresh();
        this.drawerService.close();
      },
      error: (err) => {
        this.notifications.error('Error', err.error?.detail || 'No se pudo guardar');
        this.isSaving.set(false);
      }
    });
  }

  deleteConcept() {
    if (!this.currentId || !this.isAdmin() || this.isDeleting()) return;
    if (!confirm('¿Eliminar este concepto permanentemente?')) return;

    this.isDeleting.set(true);
    this.masterData.deleteConcept(this.currentId).subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Concepto eliminado');
        this.drawerService.notifyRefresh();
        this.drawerService.close();
      },
      error: () => {
        this.notifications.error('Error', 'No se pudo eliminar');
        this.isDeleting.set(false);
      }
    });
  }
}
