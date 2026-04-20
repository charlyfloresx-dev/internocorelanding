import { Component, inject, signal, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, Partner, PartnerType } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-partner-modal',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in" (click)="close()">
      <div class="industrial-card max-w-lg w-full p-8 space-y-8 shadow-2xl animate-in zoom-in-95 duration-300" (click)="$event.stopPropagation()">
        <div class="flex items-center gap-4 border-b border-surface-border pb-6 relative">
          <button (click)="close()" class="absolute -top-2 -right-2 p-2 text-surface-text-muted hover:text-primary transition-colors rounded-xl hover:bg-surface-bg">
            <mat-icon>close</mat-icon>
          </button>
          <div class="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center text-primary shadow-inner">
            <mat-icon class="text-3xl">business_center</mat-icon>
          </div>
          <div>
            <h2 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic">
              {{ isEditing() ? 'Editar Socio' : 'Nuevo Socio de Negocio' }}
            </h2>
            <p class="text-[10px] text-surface-text-muted font-mono uppercase tracking-[0.2em]">
              {{ isEditing() ? 'GESTIÓN DE MAESTRO' : 'ALTA DE SOCIO COMERCIAL' }}
            </p>
          </div>
        </div>

        <form [formGroup]="partnerForm" class="grid grid-cols-2 gap-6">
          <div class="col-span-1 space-y-2">
            <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Código Interno</label>
            <input formControlName="code" class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-xs font-bold text-surface-text outline-none focus:border-primary" placeholder="EJ: PROV-001">
          </div>
          <div class="col-span-1 space-y-2">
            <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">RFC / TAX ID</label>
            <input formControlName="tax_id" class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-xs font-bold text-surface-text outline-none focus:border-primary" placeholder="XAXX010101000">
          </div>
          <div class="col-span-2 space-y-2">
            <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Razón Social / Nombre</label>
            <input formControlName="name" class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-xs font-bold text-surface-text outline-none focus:border-primary" placeholder="NOMBRE COMPLETO DE LA EMPRESA">
          </div>
          <div class="col-span-2 space-y-2">
            <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Correo Electrónico</label>
            <input formControlName="email" class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-xs font-bold text-surface-text outline-none focus:border-primary" placeholder="ventas@empresa.com">
          </div>
          <div class="col-span-2 space-y-2">
            <label class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Tipo de Socio</label>
            <select formControlName="type" class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-xs font-bold text-surface-text outline-none focus:border-primary">
              <option value="SUPPLIER">PROVEEDOR</option>
              <option value="CUSTOMER">CLIENTE</option>
              <option value="BOTH">AMBOS (ESTRATEGIA MIXTA)</option>
            </select>
          </div>
        </form>

        <div class="flex items-center gap-4 pt-4">
          <button (click)="close()" class="flex-1 py-4 border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-white/5 transition-all">Cancelar</button>
          <button 
            (click)="save()" 
            [disabled]="partnerForm.invalid || isSaving() || (isEditing() && !isAdmin())"
            class="flex-[2] py-4 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-widest hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-30 flex items-center justify-center gap-2 shadow-xl shadow-primary/20"
          >
            @if (isSaving()) {
              <mat-icon class="animate-spin text-sm">sync</mat-icon>
              <span>{{ isEditing() ? 'Actualizando...' : 'Guardando...' }}</span>
            } @else {
              <mat-icon class="text-sm">save</mat-icon>
              <span>{{ isEditing() ? 'Guardar Cambios' : 'Dar de Alta Socio' }}</span>
            }
          </button>
        </div>

        @if (isEditing() && isAdmin()) {
          <div class="pt-4 border-t border-surface-border">
            <button 
              (click)="deletePartner()"
              [disabled]="isDeleting() || isSaving()"
              class="w-full py-3 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 border border-rose-500/20"
            >
              @if (isDeleting()) {
                <mat-icon class="animate-spin text-xs">sync</mat-icon>
                <span>Eliminando...</span>
              } @else {
                <mat-icon class="text-xs">delete</mat-icon>
                <span>Eliminar Socio (Soft-Delete)</span>
              }
            </button>
            <p class="text-[8px] text-surface-text-muted font-mono uppercase text-center mt-2 italic">Solo administradores pueden realizar esta acción</p>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .animate-fade-in {
      animation: fadeIn 0.3s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
  `]
})
export class PartnerModalComponent {
  masterData = inject(MasterDataService);
  notifications = inject(NotificationService);
  auth = inject(AuthService);
  fb = inject(FormBuilder);

  onSaved = output<Partner>();
  onClosed = output<void>();

  isSaving = signal(false);
  isDeleting = signal(false);
  isEditing = signal(false);
  currentPartnerId: string | null = null;

  isAdmin = signal(false);
  partnerForm: FormGroup = this.fb.group({
    code: ['', [Validators.required, Validators.maxLength(50)]],
    name: ['', [Validators.required, Validators.maxLength(250)]],
    tax_id: ['', [Validators.maxLength(20)]],
    email: [''], // Removed Validators.email as it can be strict on empty strings
    type: ['BOTH']
  });

  open(defaultType: PartnerType = PartnerType.BOTH, partner?: Partner) {
    // Check admin permissions
    const roles = this.auth.roles();
    this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));

    if (partner) {
      this.isEditing.set(true);
      this.currentPartnerId = partner.id;
      this.partnerForm.patchValue({
        code: partner.code,
        name: partner.name,
        tax_id: partner.tax_id || '',
        email: partner.email || '',
        type: partner.type
      });
      
      // If not admin, disable the form fields
      if (!this.isAdmin()) {
        this.partnerForm.disable();
      } else {
        this.partnerForm.enable();
      }
    } else {
      this.isEditing.set(false);
      this.currentPartnerId = null;
      this.partnerForm.enable();
      this.partnerForm.reset({
        type: defaultType,
        code: '',
        name: '',
        tax_id: '',
        email: ''
      });
    }
  }

  close() {
    this.onClosed.emit();
  }

  save() {
    if (this.partnerForm.invalid || this.isSaving()) return;
    
    this.isSaving.set(true);
    const formValue = this.partnerForm.value;
    
    // Clean up empty strings to null for the backend
    const partnerData = {
      ...formValue,
      tax_id: formValue.tax_id?.trim() || null,
      email: formValue.email?.trim() || null
    };

    const request = this.isEditing() && this.currentPartnerId
      ? this.masterData.updatePartner(this.currentPartnerId, partnerData)
      : this.masterData.createPartner(partnerData);

    request.subscribe({
      next: (res) => {
        this.notifications.success('Éxito', this.isEditing() ? 'Socio actualizado correctamente' : 'Socio creado exitosamente');
        this.onSaved.emit(res.data);
      },
      error: (err) => {
        console.error('[Partner] Operation failed:', err);
        const action = this.isEditing() ? 'actualizar' : 'crear';
        this.notifications.error('Error', `No se pudo ${action} el socio: ` + (err.error?.detail || 'Error desconocido'));
        this.isSaving.set(false);
      },
      complete: () => this.isSaving.set(false)
    });
  }

  deletePartner() {
    if (!this.currentPartnerId || !this.isAdmin() || this.isDeleting()) return;

    if (!confirm('¿Está seguro de que desea eliminar este socio? Esta acción es un borrado lógico (quedará inactivo).')) return;

    this.isDeleting.set(true);
    this.masterData.deletePartner(this.currentPartnerId).subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Socio eliminado (inactivado) correctamente');
        this.onSaved.emit({ id: this.currentPartnerId } as Partner);
        this.close();
      },
      error: (err) => {
        this.notifications.error('Error', 'No se pudo eliminar el socio: ' + (err.error?.detail || 'Acceso denegado'));
        this.isDeleting.set(false);
      },
      complete: () => this.isDeleting.set(false)
    });
  }
}
