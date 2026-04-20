import { Component, EventEmitter, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, Concept } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-concept-modal',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    @if (isVisible()) {
      <div class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-sm animate-fade-in" (click)="close()"></div>
        
        <div class="relative w-full max-w-lg bg-surface-bg border border-surface-border rounded-3xl shadow-2xl animate-slide-up overflow-hidden">
          <!-- Header -->
          <div class="p-6 border-b border-surface-border flex items-center justify-between bg-surface-bg/50">
            <div>
              <h2 class="text-xl font-black text-surface-text uppercase tracking-tighter italic">
                {{ isEdit ? 'Editar Concepto' : 'Nuevo Concepto' }}
              </h2>
              <p class="text-[10px] text-surface-text-muted font-mono uppercase tracking-widest leading-none mt-1">
                Lógica de Operación de Inventario
              </p>
            </div>
            <button (click)="close()" class="p-2 hover:bg-surface-border rounded-xl transition-all">
              <mat-icon>close</mat-icon>
            </button>
          </div>

          <!-- Form -->
          <form [formGroup]="conceptForm" (ngSubmit)="save()" class="p-6 space-y-6">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Código</label>
                <input 
                  type="text" 
                  formControlName="code"
                  placeholder="EX: COMPRA-DIR"
                  class="w-full px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                >
              </div>
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Tipo Movimiento</label>
                <select 
                  formControlName="type"
                  class="w-full px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-bold focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none cursor-pointer"
                >
                  <option value="ENTRY">ENTRADA (IN)</option>
                  <option value="OUTPUT">SALIDA (OUT)</option>
                  <option value="TRANSFER">TRANSFERENCIA</option>
                </select>
              </div>
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Nombre del Concepto</label>
              <input 
                type="text" 
                formControlName="name"
                placeholder="Descripción de la operación..."
                class="w-full px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-bold focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              >
            </div>

            <!-- Business Rules -->
            <div class="space-y-3">
               <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1 italic">Reglas de Negocio</label>
               
               <div class="grid grid-cols-2 gap-3">
                  <div 
                    (click)="toggleControl('requires_external_entity')"
                    [class.border-primary]="conceptForm.get('requires_external_entity')?.value"
                    class="p-4 bg-surface-bg border border-surface-border rounded-2xl cursor-pointer hover:bg-primary/5 transition-all flex items-center gap-3"
                  >
                    <mat-icon [class.text-primary]="conceptForm.get('requires_external_entity')?.value" class="text-surface-text-muted">person_search</mat-icon>
                    <div class="leading-none">
                      <p class="text-[10px] font-black uppercase tracking-tighter">Socio Requerido</p>
                      <p class="text-[8px] text-surface-text-muted font-mono uppercase mt-1">Requiere RFC/Nombre</p>
                    </div>
                  </div>

                  <div 
                    (click)="toggleControl('requires_target_warehouse')"
                    [class.border-primary]="conceptForm.get('requires_target_warehouse')?.value"
                    class="p-4 bg-surface-bg border border-surface-border rounded-2xl cursor-pointer hover:bg-primary/5 transition-all flex items-center gap-3"
                  >
                    <mat-icon [class.text-primary]="conceptForm.get('requires_target_warehouse')?.value" class="text-surface-text-muted">near_me</mat-icon>
                    <div class="leading-none">
                      <p class="text-[10px] font-black uppercase tracking-tighter">Destino Requerido</p>
                      <p class="text-[8px] text-surface-text-muted font-mono uppercase mt-1">Requiere Almacén 2</p>
                    </div>
                  </div>
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
                [disabled]="conceptForm.invalid || isSaving() || (isEdit && !isAdmin())"
                class="flex-[2] py-4 bg-primary text-white dark:text-slate-950 rounded-2xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/20 disabled:opacity-50"
              >
                {{ isSaving() ? 'Guardando...' : (isEdit ? 'Actualizar' : 'Registrar Concepto') }}
              </button>
            </div>

            @if (isEdit && isAdmin()) {
              <div class="pt-4 border-t border-surface-border">
                <button 
                  type="button"
                  (click)="deleteConcept()"
                  [disabled]="isDeleting || isSaving()"
                  class="w-full py-3 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 border border-rose-500/20"
                >
                  <mat-icon class="text-xs">delete</mat-icon>
                  <span>{{ isDeleting ? 'Eliminando...' : 'Eliminar Concepto (Soft-Delete)' }}</span>
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
export class ConceptModalComponent {
  private fb = inject(FormBuilder);
  private masterData = inject(MasterDataService);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);

  @Output() saved = new EventEmitter<Concept>();

  isVisible = signal(false);
  isSaving = signal(false);
  isDeleting = false;
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

  open(concept?: Concept) {
    const roles = this.auth.roles();
    this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));

    this.isEdit = !!concept;
    this.currentId = concept?.id || null;
    if (concept) {
      this.conceptForm.patchValue(concept);
      if (!this.isAdmin()) this.conceptForm.disable();
      else this.conceptForm.enable();
    } else {
      this.conceptForm.enable();
      this.conceptForm.reset({ type: 'ENTRY', requires_external_entity: false, requires_target_warehouse: false });
    }
    this.isVisible.set(true);
  }

  close() {
    this.isVisible.set(false);
    this.isSaving.set(false);
  }

  toggleControl(controlName: string) {
    if (this.isEdit && !this.isAdmin()) return;
    const control = this.conceptForm.get(controlName);
    if (control) {
      control.setValue(!control.value);
    }
  }

  save() {
    if (this.conceptForm.invalid) return;

    this.isSaving.set(true);
    const data = this.conceptForm.value;

    const request = this.isEdit && this.currentId
        ? this.masterData.updateConcept(this.currentId, data)
        : this.masterData.createConcept(data);

    request.subscribe({
      next: (response) => {
        this.notifications.success('Éxito', this.isEdit ? 'Concepto actualizado' : 'Concepto registrado');
        this.saved.emit(response.data);
        this.close();
      },
      error: (err) => {
        this.notifications.error('Error', 'No se pudo guardar: ' + (err.error?.detail || 'Error de servidor'));
        this.isSaving.set(false);
      }
    });
  }

  deleteConcept() {
    if (!this.currentId || !this.isAdmin()) return;
    if (!confirm('¿Eliminar este concepto?')) return;

    this.isDeleting = true;
    this.masterData.deleteConcept(this.currentId).subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Concepto eliminado');
        this.saved.emit({ id: this.currentId } as Concept);
        this.close();
      },
      error: () => {
        this.notifications.error('Error', 'No se pudo eliminar');
        this.isDeleting = false;
      }
    });
  }
}
