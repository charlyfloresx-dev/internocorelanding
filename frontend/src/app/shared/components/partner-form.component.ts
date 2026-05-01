import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, Partner, PartnerType } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';

@Component({
  selector: 'app-partner-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">
      <!-- Header Section -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/20">
            <mat-icon class="text-2xl">handshake</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              {{ isEditing() ? 'Gestión de Maestro' : 'Alta de Socio' }}
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              {{ isEditing() ? 'ACTUALIZACIÓN DE ENTIDAD COMERCIAL' : 'NUEVO SOCIO DE NEGOCIO' }}
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
        <form [formGroup]="partnerForm" (ngSubmit)="save()" class="space-y-8">
          <div class="space-y-6">
            <div class="space-y-2">
              <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block italic">Identificación Legal</label>
              
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Código Interno *</label>
                  <input 
                    type="text" 
                    formControlName="code"
                    placeholder="EJ: PROV-001"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase"
                  >
                </div>
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">RFC / TAX ID</label>
                  <input 
                    type="text" 
                    formControlName="tax_id"
                    placeholder="XAXX010101000"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold outline-none focus:border-primary transition-all uppercase"
                  >
                </div>
              </div>

              <div class="space-y-2">
                <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Razón Social / Nombre *</label>
                <input 
                  type="text" 
                  formControlName="name"
                  placeholder="NOMBRE COMPLETO DE LA EMPRESA"
                  class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all"
                >
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Tipo de Socio</label>
                  <select 
                    formControlName="type"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all cursor-pointer"
                  >
                    <option value="SUPPLIER">PROVEEDOR</option>
                    <option value="CUSTOMER">CLIENTE</option>
                    <option value="BOTH">AMBOS</option>
                  </select>
                </div>
                <div class="space-y-2">
                  <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Contacto (Email)</label>
                  <input 
                    type="email" 
                    formControlName="email"
                    placeholder="ventas@empresa.com"
                    class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all"
                  >
                </div>
              </div>
            </div>

            @if (isEditing() && isAdmin()) {
              <div class="pt-6 border-t border-surface-border">
                <button 
                  type="button"
                  (click)="deletePartner()"
                  [disabled]="isDeleting() || isSaving()"
                  class="w-full py-3 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 border border-rose-500/20"
                >
                  <mat-icon class="text-xs">delete</mat-icon>
                  <span>{{ isDeleting() ? 'Eliminando...' : 'Inactivar Socio de Negocio' }}</span>
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
            [disabled]="partnerForm.invalid || isSaving() || (isEditing() && !isAdmin())"
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic overflow-hidden group relative"
          >
            <div class="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            <mat-icon class="text-lg">{{ isSaving() ? 'sync' : 'verified' }}</mat-icon>
            <span>{{ isSaving() ? 'Procesando...' : (isEditing() ? 'Sincronizar Socio' : 'Dar de Alta Socio') }}</span>
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
export class PartnerFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private masterData = inject(MasterDataService);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);
  drawerService = inject(SideDrawerService);

  set data(val: any) {
    if (val) {
      this.isEditing.set(!!val.partner);
      this.currentPartnerId = val.partner?.id || null;
      if (val.partner) {
        this.partnerForm.patchValue(val.partner);
      } else if (val.defaultType) {
        this.partnerForm.patchValue({ type: val.defaultType });
      }
    }
  }

  isSaving = signal(false);
  isDeleting = signal(false);
  isEditing = signal(false);
  isAdmin = signal(false);
  currentPartnerId: string | null = null;

  partnerForm: FormGroup = this.fb.group({
    code: ['', [Validators.required, Validators.maxLength(50)]],
    name: ['', [Validators.required, Validators.maxLength(250)]],
    tax_id: ['', [Validators.maxLength(20)]],
    email: [''],
    type: ['BOTH']
  });

  ngOnInit() {
    const roles = this.auth.roles();
    this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));
    
    if (this.isEditing() && !this.isAdmin()) {
      this.partnerForm.disable();
    }
  }

  save() {
    if (this.partnerForm.invalid || this.isSaving()) return;

    this.isSaving.set(true);
    const formValue = this.partnerForm.value;
    const partnerData = {
      ...formValue,
      tax_id: formValue.tax_id?.trim() || null,
      email: formValue.email?.trim() || null
    };

    const request = this.isEditing() && this.currentPartnerId
        ? this.masterData.updatePartner(this.currentPartnerId, partnerData)
        : this.masterData.createPartner(partnerData);

    request.subscribe({
      next: () => {
        this.notifications.success('Éxito', this.isEditing() ? 'Socio actualizado' : 'Socio creado');
        this.drawerService.notifyRefresh();
        this.drawerService.close();
      },
      error: (err) => {
        this.notifications.error('Error', err.error?.detail || 'No se pudo guardar');
        this.isSaving.set(false);
      }
    });
  }

  deletePartner() {
    if (!this.currentPartnerId || !this.isAdmin() || this.isDeleting()) return;
    if (!confirm('¿Inactivar este socio permanentemente?')) return;

    this.isDeleting.set(true);
    this.masterData.deletePartner(this.currentPartnerId).subscribe({
      next: () => {
        this.notifications.success('Éxito', 'Socio inactivado');
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
