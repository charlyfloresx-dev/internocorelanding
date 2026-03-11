import { Component, inject, output, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '@services/auth.service';
import { UserCompanyAccess } from '@models/api.types';

@Component({
  selector: 'app-tenant-selection',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="w-full max-w-lg mx-auto bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl overflow-hidden animate-fade-in-up">
      
      <div class="p-8 pb-6 text-center border-b border-slate-700/50 relative">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-sky-500 via-purple-500 to-sky-500 opacity-50"></div>
        
        <div class="relative inline-block mb-4">
          <div class="w-24 h-24 rounded-full p-1 bg-slate-900 border-2 border-slate-700 shadow-inner overflow-hidden">
            <img [src]="auth.currentUser()?.avatar || 'https://ui-avatars.com/api/?name=' + auth.currentUser()?.email" 
                 class="w-full h-full rounded-full object-cover"
                 alt="User Avatar">
          </div>
          <div class="absolute bottom-1 right-1 w-5 h-5 bg-green-500 border-4 border-slate-800 rounded-full"></div>
        </div>

        <h2 class="text-2xl font-bold text-white tracking-tight">Selecciona tu Empresa</h2>
        <p class="text-slate-400 text-sm mt-1">Elige el entorno donde deseas trabajar</p>
      </div>

      <div class="p-6 bg-slate-800/50 max-h-[450px] overflow-y-auto custom-scrollbar">
        <div class="space-y-6">
          
          @for (group of groupedAccesses(); track group.name) {
            <div class="space-y-3">
              <!-- Cluster Header -->
              <div class="flex items-center gap-3 px-1">
                <div class="h-[1px] flex-1 bg-slate-700"></div>
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] whitespace-nowrap">
                  {{ group.name }}
                </span>
                <div class="h-[1px] flex-1 bg-slate-700"></div>
              </div>

              @for (item of group.items; track item.company.id) {
                <div (click)="selectCompany(item)"
                     [class.opacity-50]="isLoading || (selectedId && selectedId !== item.company.id)"
                     [class.pointer-events-none]="isLoading"
                     class="group relative flex items-center gap-4 p-4 rounded-xl bg-slate-900 border border-slate-800 cursor-pointer transition-all duration-200 hover:bg-slate-700/50 hover:border-slate-600 hover:shadow-lg hover:-translate-y-0.5">
                  
                  <!-- Logo/Avatar de la Empresa -->
                  <div class="w-12 h-12 flex-shrink-0 rounded-lg bg-slate-800 flex items-center justify-center overflow-hidden border border-slate-700 group-hover:border-slate-500 transition-colors">
                    @if (item.company.logo) {
                      <img [src]="item.company.logo" class="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all" [alt]="item.company.name">
                    } @else {
                      <span class="text-slate-500 font-bold text-lg group-hover:text-white">{{ item.company.name.charAt(0) }}</span>
                    }
                  </div>

                  <!-- Información de la Empresa -->
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <h4 class="font-bold text-white text-base truncate group-hover:text-sky-400 transition-colors">{{ item.company.name }}</h4>
                      <span class="text-[10px] bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded border border-slate-600 uppercase">{{ item.role.name }}</span>
                    </div>
                    
                    <div class="flex items-center gap-3 mt-1.5">
                      <span class="text-[10px] uppercase font-bold tracking-wider text-slate-500 border border-slate-700 px-1.5 py-0.5 rounded bg-slate-800">ACTIVE</span>
                      
                      <!-- Badge para empresas nuevas -->
                      @if (item.company.is_new) {
                        <span class="text-[10px] font-bold text-sky-400 flex items-center gap-1.5">
                          <i class="fa-solid fa-wand-magic-sparkles"></i>
                          <span>Configuración Requerida</span>
                        </span>
                      }
                    </div>
                  </div>

                  <!-- Spinner / Chevron -->
                  <div class="w-8 h-8 flex items-center justify-center rounded-full bg-slate-800 text-slate-500 group-hover:bg-sky-500 group-hover:text-white transition-all">
                    @if (isLoading && selectedId === item.company.id) {
                      <i class="fa-solid fa-circle-notch fa-spin"></i>
                    } @else {
                      <i class="fa-solid fa-chevron-right text-sm"></i>
                    }
                  </div>
                </div>
              }
            </div>
          }

        </div>
      </div>

      <div class="p-4 bg-slate-900 border-t border-slate-800 text-center">
        <button (click)="logout.emit()" class="text-slate-500 hover:text-red-400 text-sm font-medium transition-colors flex items-center justify-center gap-2 w-full py-2">
          <i class="fa-solid fa-power-off"></i> Cerrar Sesión
        </button>
      </div>
    </div>
  `
})
export class TenantSelectionComponent {
  public auth = inject(AuthService);
  private router = inject(Router);
  logout = output<void>();

  isLoading = false;
  selectedId: string | null = null;

  /**
   * Agrupa los accesos disponibles por el nombre del grupo (Cluster)
   */
  groupedAccesses = computed(() => {
    const accesses = this.auth.availableAccesses();
    const groups: { [key: string]: UserCompanyAccess[] } = {};

    accesses.forEach(a => {
      const gName = a.company.group_name || 'Corporativo Local';
      if (!groups[gName]) groups[gName] = [];
      groups[gName].push(a);
    });

    return Object.entries(groups).map(([name, items]) => ({ name, items }));
  });

  /**
   * Maneja la selección de empresa
   * Llama a auth.selectCompany(companyId) que:
   * 1. Envía selection_token al backend
   * 2. Recibe access_token
   * 3. Redirige a /dashboard o /onboarding según is_new
   */
  selectCompany(access: UserCompanyAccess) {
    this.isLoading = true;
    this.selectedId = access.company.id;

    // Llamar al AuthService para manejar la selección
    this.auth.selectCompany(access.company.id);
  }
}