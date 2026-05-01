import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, Category, Brand } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';

@Component({
  selector: 'app-category-brand-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">
      <!-- Header Section -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/20">
            <mat-icon class="text-2xl">{{ context === 'categories' ? 'category' : 'verified' }}</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              {{ isEdit ? 'Configuración' : 'Nueva' }} {{ context === 'categories' ? 'Categoría' : 'Marca' }}
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              {{ isEdit ? 'GESTIÓN DE ATRIBUTO MAESTRO' : 'REGISTRO DE NUEVA ENTIDAD' }}
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
        <form [formGroup]="itemForm" (ngSubmit)="save()" class="space-y-8">
          <div class="space-y-6">
            <div class="space-y-2">
              <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block italic">Atributos Industriales</label>
              
              <div class="space-y-4">
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Código *</label>
                  <input 
                    type="text" 
                    formControlName="code"
                    placeholder="EX: ELECT-01, BOSCH"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase"
                  >
                </div>

                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Nombre *</label>
                  <input 
                    type="text" 
                    formControlName="name"
                    placeholder="Nombre descriptivo..."
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all"
                  >
                </div>
              </div>
            </div>

            @if (isEdit && isAdmin()) {
              <div class="pt-6 border-t border-surface-border">
                <button 
                  type="button"
                  (click)="deleteItem()"
                  [disabled]="isDeleting || isSaving()"
                  class="w-full py-3 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 border border-rose-500/20"
                >
                  <mat-icon class="text-xs">delete</mat-icon>
                  <span>{{ isDeleting ? 'Eliminando...' : 'Eliminar Registro Permanente' }}</span>
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
            [disabled]="itemForm.invalid || isSaving() || (isEdit && !isAdmin())"
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic overflow-hidden group relative"
          >
            <div class="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            <mat-icon class="text-lg">{{ isSaving() ? 'sync' : 'verified' }}</mat-icon>
            <span>{{ isSaving() ? 'Procesando...' : (isEdit ? 'Sincronizar Registro' : 'Registrar Atributo') }}</span>
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
export class CategoryBrandFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private masterData = inject(MasterDataService);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);
  drawerService = inject(SideDrawerService);

  // 'data' property for SideDrawerComponent injection
  set data(val: any) {
    if (val) {
      this.context = val.context;
      this.isEdit = !!val.item;
      this.currentId = val.item?.id || null;
      if (val.item) {
        this.itemForm.patchValue(val.item);
      }
    }
  }

  isSaving = signal(false);
  isDeleting = false;
  isEdit = false;
  isAdmin = signal(false);
  context: 'categories' | 'brands' = 'categories';
  currentId: string | null = null;

  itemForm: FormGroup = this.fb.group({
    code: ['', [Validators.required]],
    name: ['', [Validators.required]]
  });

  ngOnInit() {
    const roles = this.auth.roles();
    this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));
    
    if (this.isEdit && !this.isAdmin()) {
      this.itemForm.disable();
    }
  }

  save() {
    if (this.itemForm.invalid) return;

    this.isSaving.set(true);
    const data = this.itemForm.value;

    const request = this.context === 'categories'
        ? (this.isEdit && this.currentId ? this.masterData.updateCategory(this.currentId, data) : this.masterData.createCategory(data))
        : (this.isEdit && this.currentId ? this.masterData.updateBrand(this.currentId, data) : this.masterData.createBrand(data));

    request.subscribe({
      next: (response) => {
        this.notifications.success('Éxito', 'Registro guardado exitosamente');
        this.drawerService.notifyRefresh(response.data);
        this.drawerService.close();
      },
      error: (err) => {
        this.notifications.error('Error', 'No se pudo guardar: ' + (err.error?.detail || 'Error de servidor'));
        this.isSaving.set(false);
      }
    });
  }

  deleteItem() {
    if (!this.currentId || !this.isAdmin()) return;
    if (!confirm(`¿Estás seguro de eliminar este registro permanentemente?`)) return;

    this.isDeleting = true;
    const request = this.context === 'categories' 
      ? this.masterData.deleteCategory(this.currentId)
      : this.masterData.deleteBrand(this.currentId);

    request.subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Registro eliminado');
        this.drawerService.notifyRefresh({ id: this.currentId, deleted: true });
        this.drawerService.close();
      },
      error: () => {
        this.notifications.error('Error', 'No se pudo eliminar el registro');
        this.isDeleting = false;
      }
    });
  }
}
