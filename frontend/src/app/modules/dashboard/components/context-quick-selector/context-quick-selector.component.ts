// temp_future/src/app/modules/dashboard/components/context-quick-selector/context-quick-selector.component.ts
import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../../core/services/auth.service';
import { DashboardService } from '../../../../core/services/dashboard.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-context-quick-selector',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="relative group">
      <!-- Active Context Trigger -->
      <button (click)="toggleDropdown()" 
              class="flex items-center gap-3 p-2 pr-4 rounded-xl transition-all border shadow-sm
                     bg-white border-slate-200 text-slate-900
                     dark:bg-white/5 dark:border-white/10 dark:text-white dark:hover:bg-white/10 dark:group-hover:border-cyan-500/30">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
          <mat-icon class="text-sm">business</mat-icon>
        </div>
        <div class="text-left hidden md:block">
          <p class="text-[8px] font-black uppercase tracking-widest leading-none mb-1 text-slate-500 dark:text-white/50">TENANT ACTIVO</p>
          <p class="text-[11px] font-black truncate max-w-[120px] text-slate-900 dark:text-white">
            {{ activeCompanyName() }}
          </p>
        </div>
        <mat-icon class="text-slate-400 dark:text-slate-500 group-hover:text-primary transition-colors">expand_more</mat-icon>
      </button>

      <!-- Glassmorphism Dropdown -->
      @if (isOpen()) {
        <div class="absolute top-full mt-3 right-0 w-72 border rounded-2xl shadow-[0_30px_60px_-12px_rgba(0,0,0,0.5)] backdrop-blur-2xl overflow-hidden z-[100] animate-in fade-in zoom-in-95 duration-200
                    bg-white/95 border-slate-200
                    dark:bg-slate-900/95 dark:border-white/10">
          <div class="p-4 border-b border-slate-100 dark:border-white/5">
            <h3 class="text-[10px] font-black text-primary uppercase tracking-widest">Cambio de Contexto</h3>
          </div>
          
          <div class="max-h-64 overflow-y-auto custom-scrollbar">
            @for (company of auth.availableCompanies(); track company.company_id) {
              <button (click)="onSelect(company.company_id)"
                      [disabled]="company.company_id === auth.activeCompanyId()"
                      class="w-full p-4 flex items-center gap-4 transition-colors text-left group/item disabled:opacity-50 disabled:cursor-default
                             hover:bg-slate-50 dark:hover:bg-white/5">
                <div class="w-10 h-10 rounded-xl flex items-center justify-center border transition-all
                            bg-slate-100 border-slate-200 dark:bg-slate-800 dark:border-white/5 group-hover/item:border-primary/50">
                  @if (company.logo) {
                    <img [src]="company.logo" class="w-6 h-6 object-contain">
                  } @else {
                    <mat-icon class="text-slate-400 dark:text-slate-500 group-hover/item:text-primary transition-colors">factory</mat-icon>
                  }
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-bold truncate text-slate-900 dark:text-white">{{ company.company_name }}</p>
                  <p class="text-[10px] text-slate-500">{{ getCompanyRoles(company) }}</p>
                </div>
                @if (company.company_id === auth.activeCompanyId()) {
                  <mat-icon class="text-primary text-sm">check_circle</mat-icon>
                }
              </button>
            }
          </div>

          <div class="p-3 bg-slate-50 dark:bg-black/20 flex justify-center border-t border-slate-100 dark:border-white/5">
             <button (click)="auth.logout()" class="text-[9px] font-black text-red-500/70 hover:text-red-500 uppercase tracking-widest transition-colors">
               Cerrar Sesión Global
             </button>
          </div>
        </div>

        <!-- Overlay to close -->
        <div class="fixed inset-0 z-40 bg-transparent" (click)="toggleDropdown()"></div>
      }
    </div>
  `
})
export class ContextQuickSelectorComponent {
  auth = inject(AuthService);
  dashboard = inject(DashboardService);
  isOpen = signal(false);

  activeCompanyName = computed(() => {
    const id = this.auth.activeCompanyId();
    if (id) {
      const match = this.auth.availableCompanies().find(c => c.company_id === id);
      if (match) return match.company_name;
    }
    return (this.auth.session() as any)?.company_name || 'Sin Empresa';
  });

  toggleDropdown() {
    this.isOpen.update(v => !v);
  }

  async onSelect(companyId: string) {
    this.isOpen.set(false);
    await this.dashboard.quickSwitchCompany(companyId);
  }

  getCompanyRoles(company: any): string {
    const roles = company.role_names || company.roles || [];
    return roles.join(', ');
  }
}
