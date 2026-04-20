import {Component, inject, signal, OnInit, computed} from '@angular/core';
import {TranslationService} from '../../core/services/translation.service';
import {TranslatePipe} from '../../shared/pipes/translate.pipe';
import {CommonModule} from '@angular/common';
import {MatIconModule} from '@angular/material/icon';
import {AdminService, AdminUser, AdminRole} from '../../core/services/admin.service';
import {ToastService} from '../../core/services/toast.service';
import {FormsModule} from '@angular/forms';

@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule, TranslatePipe],
  template: `
    <div class="p-12 space-y-10 animate-fade-in bg-white min-h-screen">
      <div class="flex justify-between items-center bg-white">
        <div>
          <h2 class="text-4xl font-black text-slate-950 uppercase tracking-tighter italic">{{ 'settings.users.title' | translate:'Gestión de Usuarios' }}</h2>
          <p class="text-slate-500 text-[10px] font-mono uppercase tracking-widest mt-1">{{ 'settings.users.subtitle' | translate:'Administración de accesos y roles del tenant' }}</p>
        </div>
        <button 
          (click)="showInviteModal = true"
          class="px-8 py-4 bg-primary text-white rounded-2xl font-black text-[10px] uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-[0_10px_30px_rgba(0,229,255,0.3)] flex items-center gap-3"
        >
          <mat-icon class="text-base">person_add</mat-icon>
          {{ 'settings.users.invite_user' | translate:'Invitar Nuevo Usuario' }}
        </button>
      </div>

      <!-- Users List (Card System) -->
      <div class="space-y-6 bg-white">
        @for (user of users(); track user.id) {
          <div class="bg-white rounded-[2rem] p-6 border border-slate-200 shadow-[0_4px_20px_rgba(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.08)] hover:scale-[1.01] transition-all duration-500 group flex items-center justify-between">
            
            <div class="flex items-center gap-6">
              <!-- Avatar -->
              <div class="w-14 h-14 rounded-2xl bg-slate-50 dark:bg-primary/10 flex items-center justify-center text-slate-400 dark:text-primary font-black text-xl border border-slate-100 dark:border-primary/20 group-hover:border-primary/50 transition-colors">
                {{ user.email.charAt(0).toUpperCase() }}
              </div>
              
              <!-- Info -->
              <div class="flex flex-col">
                <div class="flex items-center gap-3">
                  <span class="text-base font-black text-slate-900 dark:text-white uppercase tracking-tight">{{ user.full_name || ('settings.users.pending_registration' | translate:'Pendiente de Registro') }}</span>
                  <span class="text-[9px] font-mono text-slate-400 bg-slate-50 dark:bg-white/5 px-2 py-0.5 rounded-md uppercase">#{{ user.id.slice(0, 4) }}</span>
                </div>
                <span class="text-xs text-slate-500 dark:text-surface-text-muted font-mono tracking-wider italic">{{ user.email }}</span>
              </div>
            </div>

            <!-- Role & Status -->
            <div class="flex items-center gap-12">
              <div class="flex flex-col items-center gap-1">
                <span class="text-[9px] font-black text-slate-400 dark:text-white/30 uppercase tracking-[0.2em]">{{ 'settings.users.assigned_role' | translate:'Rol Asignado' }}</span>
                <span class="px-4 py-1 bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-white/10 rounded-full text-[10px] font-black text-slate-600 dark:text-primary uppercase tracking-widest">
                  {{ user.role_name }}
                </span>
              </div>

              <div class="flex flex-col items-center gap-1">
                <span class="text-[9px] font-black text-slate-400 dark:text-white/30 uppercase tracking-[0.2em]">{{ 'settings.users.access_status' | translate:'Estado de Acceso' }}</span>
                <span 
                  [ngClass]="{
                    'bg-emerald-50 text-emerald-600 border-emerald-100 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20': user.status === 'active',
                    'bg-amber-50 text-amber-600 border-amber-100 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20': user.status === 'invited',
                    'bg-rose-50 text-rose-600 border-rose-100 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20': user.status === 'inactive'
                  }"
                  class="px-4 py-1 border rounded-full text-[10px] font-black uppercase tracking-widest shadow-sm min-w-[100px] text-center"
                >
                  • {{ user.status }}
                </span>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex gap-3 opacity-0 group-hover:opacity-100 scale-95 group-hover:scale-100 transition-all duration-300">
              <button (click)="editPermissions(user)" 
                class="w-11 h-11 flex items-center justify-center bg-slate-50 dark:bg-white/5 hover:bg-primary hover:text-white dark:hover:bg-primary dark:hover:text-slate-950 text-slate-400 rounded-2xl transition-all border border-slate-100 dark:border-white/10 shadow-sm" 
                [title]="'settings.users.edit_permissions' | translate:'Editar Permisos'">
                <mat-icon style="font-size: 20px; width: 20px; height: 20px;">security</mat-icon>
              </button>
              <button (click)="revokeAccess(user)" 
                class="w-11 h-11 flex items-center justify-center bg-slate-50 dark:bg-white/5 hover:bg-rose-500 hover:text-white dark:hover:bg-rose-500 text-slate-400 rounded-2xl transition-all border border-slate-100 dark:border-white/10 shadow-sm" 
                [title]="'settings.users.revoke_access' | translate:'Revocar Acceso'">
                <mat-icon style="font-size: 20px; width: 20px; height: 20px;">person_remove</mat-icon>
              </button>
            </div>

          </div>
        }
      </div>

      <!-- Invite Modal -->
      @if (showInviteModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-950/20 dark:bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div class="bg-white dark:bg-slate-900 w-full max-w-md p-8 rounded-3xl border border-slate-200 dark:border-white/10 shadow-2xl space-y-6">
            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-xl font-black text-slate-800 dark:text-white uppercase tracking-tighter">{{ 'settings.users.invite_modal_title' | translate:'Invitar Usuario' }}</h3>
                <p class="text-[10px] text-slate-500 dark:text-surface-text-muted uppercase tracking-widest font-mono">{{ 'settings.users.invite_modal_subtitle' | translate:'Se enviará un código de acceso' }}</p>
              </div>
              <button (click)="showInviteModal = false" class="text-slate-400 dark:text-surface-text-muted hover:text-slate-800 dark:hover:text-white">
                <mat-icon>close</mat-icon>
              </button>
            </div>

            <div class="space-y-4">
              <div class="space-y-1">
                <label for="invite-email" class="text-[10px] font-black text-primary uppercase tracking-widest ml-1">Email</label>
                <input 
                  id="invite-email"
                  type="email" 
                  [(ngModel)]="inviteForm.email"
                  [placeholder]="'settings.users.email_placeholder' | translate:'usuario@empresa.com'"
                  class="w-full bg-slate-100 border border-slate-300 rounded-xl px-4 py-3 text-sm text-slate-900 outline-none focus:border-primary transition-all placeholder:text-slate-400"
                >
              </div>
              <div class="space-y-1">
                <label for="invite-role" class="text-[10px] font-black text-primary uppercase tracking-widest ml-1">{{ 'settings.users.initial_role_label' | translate:'Rol Inicial' }}</label>
                <div class="relative">
                  <select 
                    id="invite-role"
                    [(ngModel)]="inviteForm.role_id"
                    class="w-full bg-slate-100 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-900 outline-none focus:border-primary transition-all appearance-none cursor-pointer"
                  >
                    <option value="" class="bg-white text-slate-900">{{ 'settings.users.select_role' | translate:'Seleccione Rol...' }}</option>
                    @for (role of roles(); track role.id) {
                      <option [value]="role.id" class="bg-white text-slate-900">{{ role.name }}</option>
                    }
                  </select>
                  <mat-icon class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none text-sm">expand_more</mat-icon>
                </div>
              </div>
            </div>

            <div class="pt-4 flex gap-3">
              <button 
                (click)="showInviteModal = false"
                class="flex-1 py-3 bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-slate-200 dark:hover:bg-white/10 transition-all"
              >
                {{ 'common.cancel' | translate:'Cancelar' }}
              </button>
              <button 
                (click)="sendInvite()"
                [disabled]="!inviteForm.email || !inviteForm.role_id"
                class="flex-1 py-3 bg-primary text-white dark:text-slate-950 rounded-xl font-black text-[10px] uppercase tracking-widest hover:scale-105 transition-all disabled:opacity-30"
              >
                {{ 'settings.users.send_invitation' | translate:'Enviar Invitación' }}
              </button>
            </div>
          </div>
        </div>
      }

      <!-- Permissions Matrix Modal -->
      @if (selectedUserForPermissions) {
        <div class="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-950/20 dark:bg-slate-950/90 backdrop-blur-md animate-fade-in">
          <div class="bg-white dark:bg-slate-900 w-full max-w-xl p-8 rounded-[2rem] border border-slate-200 dark:border-white/10 shadow-2xl space-y-8 relative overflow-hidden">
            <!-- Decorative background glow -->
            <div class="absolute -top-24 -right-24 w-48 h-48 bg-primary/10 blur-[100px] rounded-full"></div>
            
            <div class="flex justify-between items-start relative z-10">
              <div>
                <h3 class="text-2xl font-black text-slate-950 dark:text-white uppercase tracking-tighter italic">{{ 'settings.users.permissions_matrix' | translate:'Matriz de Permisos' }}</h3>
                <div class="flex items-center gap-2 mt-1">
                  <div class="w-1 h-1 rounded-full bg-primary animate-pulse"></div>
                  <p class="text-[10px] text-primary font-mono uppercase tracking-[0.2em]">{{ selectedUserForPermissions.email }}</p>
                </div>
              </div>
              <button (click)="selectedUserForPermissions = null" class="w-10 h-10 flex items-center justify-center rounded-full bg-slate-100 dark:bg-white/5 text-slate-400 dark:text-white/40 hover:bg-slate-200 dark:hover:bg-white/10 hover:text-slate-950 dark:hover:text-white transition-all">
                <mat-icon>close</mat-icon>
              </button>
            </div>

            <div class="space-y-8 max-h-[60vh] overflow-y-auto pr-4 custom-scrollbar relative z-10">
              @for (group of groupedScopes(); track group.name) {
                <div class="space-y-4">
                  <div class="flex items-center gap-3">
                    <div class="h-[1px] flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent"></div>
                    <h4 class="text-[10px] font-bold text-slate-800 uppercase tracking-[0.3em] whitespace-nowrap">{{ group.name }}</h4>
                    <div class="h-[1px] flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent"></div>
                  </div>

                  <div class="grid grid-cols-1 gap-3">
                    @for (scope of group.scopes; track scope.id) {
                      <label 
                        [class.bg-slate-50]="!isScopeSelected(scope.id)"
                        [class.bg-primary/5]="isScopeSelected(scope.id)"
                        [class.border-slate-200]="!isScopeSelected(scope.id)"
                        [class.border-primary/30]="isScopeSelected(scope.id)"
                        class="flex items-center justify-between p-5 rounded-2xl border transition-all cursor-pointer group relative overflow-hidden shadow-sm hover:shadow-md"
                      >
                        <!-- Active Glow Background -->
                        @if (isScopeSelected(scope.id)) {
                          <div class="absolute inset-0 opacity-[0.03] pointer-events-none" 
                               [ngClass]="scope.id.includes(':admin') ? 'bg-primary' : 'bg-emerald-500'">
                          </div>
                        }

                        <div class="flex flex-col relative z-10">
                          <span class="text-sm font-bold text-slate-900 uppercase tracking-tight group-hover:text-primary transition-colors">
                            {{ scope.name }}
                          </span>
                          <span class="text-[10px] font-mono uppercase tracking-wider mt-1"
                                [ngClass]="scope.id.includes(':admin') ? 'text-primary' : 'text-emerald-600'">
                            {{ scope.id }}
                          </span>
                        </div>

                        <div class="relative flex items-center z-10">
                          <input 
                            type="checkbox" 
                            [checked]="isScopeSelected(scope.id)"
                            (change)="toggleScope(scope.id)"
                            class="peer hidden"
                          >
                          <!-- Industrial Toggle -->
                          <div class="w-14 h-7 bg-slate-200 rounded-full p-1 transition-all duration-500 border border-slate-300 relative"
                               [ngClass]="{
                                 'peer-checked:border-primary/50': scope.id.includes(':admin'),
                                 'peer-checked:border-emerald-500/50': !scope.id.includes(':admin')
                                }">
                            <div class="w-5 h-5 bg-white rounded-full transition-all duration-500 transform peer-checked:translate-x-7 flex items-center justify-center shadow-sm"
                                 [ngClass]="{
                                   'peer-checked:bg-primary': scope.id.includes(':admin'),
                                   'peer-checked:bg-emerald-500': !scope.id.includes(':admin')
                                 }">
                              <div class="w-1.5 h-1.5 rounded-full bg-slate-300 peer-checked:bg-white"></div>
                            </div>
                          </div>
                        </div>
                      </label>
                    }
                  </div>
                </div>
              }
            </div>

            <div class="pt-6 flex gap-4 relative z-10">
              <button 
                (click)="selectedUserForPermissions = null"
                class="flex-1 py-4 bg-slate-100 text-slate-600 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:bg-slate-200 transition-all border border-slate-200"
              >
                {{ 'common.cancel' | translate:'Cancelar' }}
              </button>
              <button 
                (click)="savePermissions()"
                class="flex-1 py-4 bg-primary text-white rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-95 transition-all shadow-[0_10px_20px_rgba(0,229,255,0.2)]"
              >
                {{ 'common.save_changes' | translate:'Guardar Cambios' }}
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `
})
export class UserManagementComponent implements OnInit {
  private adminService = inject(AdminService);
  protected translationService = inject(TranslationService);
  private toastService = inject(ToastService);

  users = signal<AdminUser[]>([]);
  roles = signal<AdminRole[]>([]);
  
  showInviteModal = false;
  inviteForm = {
    email: '',
    role_id: ''
  };

  selectedUserForPermissions: AdminUser | null = null;
  tempScopes: string[] = [];

  availableScopes = [
    { id: 'catalog:admin', name: this.translationService.translate('settings.users.scopes.catalog_admin', 'Administración de Catálogo'), module: this.translationService.translate('settings.users.scopes.catalog_module', 'Módulo Catálogo') },
    { id: 'inventory:admin', name: this.translationService.translate('settings.users.scopes.inventory_admin', 'Administración de Inventario'), module: this.translationService.translate('settings.users.scopes.inventory_module', 'Módulo Inventario') },
    { id: 'inventory:read', name: this.translationService.translate('settings.users.scopes.inventory_read', 'Consulta de Inventario'), module: this.translationService.translate('settings.users.scopes.inventory_module', 'Módulo Inventario') },
    { id: 'production_mes:admin', name: this.translationService.translate('settings.users.scopes.production_admin', 'Control de Producción (MES)'), module: this.translationService.translate('settings.users.scopes.production_module', 'Módulo Producción') },
    { id: 'admin:users', name: this.translationService.translate('settings.users.scopes.user_management', 'Gestión de Usuarios'), module: this.translationService.translate('settings.users.scopes.system_module', 'Módulo Sistema') }
  ];

  groupedScopes = computed(() => {
    const groups: Record<string, typeof this.availableScopes> = {};
    this.availableScopes.forEach(scope => {
      if (!groups[scope.module]) groups[scope.module] = [];
      groups[scope.module].push(scope);
    });
    return Object.entries(groups).map(([name, scopes]) => ({ name, scopes }));
  });

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.adminService.getUsers().subscribe({
      next: (res) => this.users.set(res.data),
      error: () => {
        // Mock data for demo
        this.users.set([
          { id: '1', email: 'admin@demo.com', full_name: 'Admin Principal', role_id: 'r1', role_name: 'Admin', status: 'active', created_at: new Date().toISOString(), scopes: ['catalog:admin', 'inventory:admin'] },
          { id: '2', email: 'operador@demo.com', full_name: 'Juan Pérez', role_id: 'r2', role_name: 'Operador', status: 'active', created_at: new Date().toISOString(), scopes: ['inventory:read'] },
          { id: '3', email: 'nuevo@demo.com', full_name: '', role_id: 'r2', role_name: 'Operador', status: 'invited', created_at: new Date().toISOString(), scopes: [] }
        ]);
      }
    });

    this.adminService.getRoles().subscribe({
      next: (res) => this.roles.set(res.data),
      error: () => {
        this.roles.set([
          { id: 'r1', name: 'Admin' },
          { id: 'r2', name: 'Operador' },
          { id: 'r3', name: 'Supervisor' }
        ]);
      }
    });
  }

  sendInvite() {
    this.toastService.info(this.translationService.translate('settings.users.sending_invitation', 'Enviando invitación...'), 'Sistema');
    this.adminService.inviteUser(this.inviteForm).subscribe({
      next: (res) => {
        this.toastService.success(`${this.translationService.translate('settings.users.invitation_sent', 'Invitación enviada')}. Código: ${res.data.code}`, this.translationService.translate('common.success', 'Éxito'));
        this.showInviteModal = false;
        this.inviteForm = { email: '', role_id: '' };
        this.loadData();
      },
      error: () => {
        // Mock success for demo
        this.toastService.success(this.translationService.translate('settings.users.invitation_sent_demo', 'Invitación enviada (Demo)'), this.translationService.translate('common.success', 'Éxito'));
        this.showInviteModal = false;
        this.loadData();
      }
    });
  }

  editPermissions(user: AdminUser) {
    this.selectedUserForPermissions = user;
    this.tempScopes = [...user.scopes];
  }

  isScopeSelected(scopeId: string): boolean {
    return this.tempScopes.includes(scopeId);
  }

  toggleScope(scopeId: string) {
    if (this.isScopeSelected(scopeId)) {
      this.tempScopes = this.tempScopes.filter(s => s !== scopeId);
    } else {
      this.tempScopes.push(scopeId);
    }
  }

  savePermissions() {
    if (!this.selectedUserForPermissions) return;
    
    this.toastService.info(this.translationService.translate('settings.users.updating_permissions', 'Actualizando permisos...'), 'Sistema');
    this.adminService.updateScopes(this.selectedUserForPermissions.id, this.tempScopes).subscribe({
      next: () => {
        this.toastService.success(this.translationService.translate('settings.users.permissions_updated', 'Permisos actualizados'), this.translationService.translate('common.success', 'Éxito'));
        this.selectedUserForPermissions = null;
        this.loadData();
      },
      error: () => {
        this.toastService.success(this.translationService.translate('settings.users.permissions_updated_demo', 'Permisos actualizados (Demo)'), this.translationService.translate('common.success', 'Éxito'));
        this.selectedUserForPermissions = null;
        this.loadData();
      }
    });
  }

  revokeAccess(user: AdminUser) {
    if (confirm(this.translationService.translate('settings.users.revoke_confirm', `¿Está seguro de revocar el acceso a ${user.email}?`))) {
      this.adminService.revokeAccess(user.id).subscribe({
        next: () => {
          this.toastService.success(this.translationService.translate('settings.users.access_revoked', 'Acceso revocado'), this.translationService.translate('common.success', 'Éxito'));
          this.loadData();
        },
        error: () => {
          this.toastService.success(this.translationService.translate('settings.users.access_revoked_demo', 'Acceso revocado (Demo)'), this.translationService.translate('common.success', 'Éxito'));
          this.loadData();
        }
      });
    }
  }
}
