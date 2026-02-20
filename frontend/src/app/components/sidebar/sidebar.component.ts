
import { Component, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NavigationService, MenuItem } from '@services/navigation.service';
import { AuthService } from '@services/auth.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <!-- 
      Hit Area Container: 
      Handles the mouseleave event for the entire navigation system (Icons + Panel)
      to prevent the panel from flickering or closing when moving between columns.
    -->
    <aside class="relative h-full flex z-50" (mouseleave)="closeFlyout()">
      
      <!-- COLUMN 1: Fixed Icon Bar (Z-50) -->
      <nav class="w-20 h-full flex flex-col items-center bg-slate-900 border-r border-slate-800 py-4 z-50 relative">
        
        <!-- Brand -->
        <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 flex items-center justify-center text-green-500 mb-8 shadow-lg shadow-black/40 flex-shrink-0">
          <i class="fa-solid fa-cogs text-2xl animate-spin-slow"></i>
        </div>

        <!-- Icons List -->
        <div class="flex-1 flex flex-col w-full space-y-3 px-2 overflow-y-auto no-scrollbar">
          @for (item of navService.menuItems(); track item.title) {
            <div (mouseenter)="onIconHover(item)"
                 (click)="onIconHover(item)"
                 [class.bg-slate-800]="isActiveOrHovered(item)"
                 [class.text-white]="isActiveOrHovered(item)"
                 [class.text-slate-500]="!isActiveOrHovered(item)"
                 [class.border-slate-700]="isActiveOrHovered(item)"
                 [class.border-transparent]="!isActiveOrHovered(item)"
                 class="group w-full aspect-square flex flex-col items-center justify-center rounded-xl border transition-all duration-200 cursor-pointer relative hover:text-white hover:bg-slate-800/80">
              
              <i [class]="item.icon + ' text-xl mb-1 transition-transform duration-300 group-hover:scale-110'"></i>
              <span class="text-[9px] font-medium tracking-wide opacity-80 text-center leading-tight">{{ item.title.split(' ')[0] }}</span>
              
              <!-- Active Indicator Bar -->
              <div class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-sky-500 rounded-r opacity-0 transition-opacity"
                   [class.opacity-100]="isActiveOrHovered(item)"></div>
            </div>
          }
        </div>

        <!-- User Avatar / Menu Trigger -->
        <div class="mt-auto px-2 w-full relative flex-shrink-0">
           <button (click)="toggleUserMenu()" class="w-full aspect-square rounded-full bg-slate-800 border border-slate-700 relative cursor-pointer group hover:border-slate-500 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500/50">
              <img [src]="auth.currentUser()?.avatar" class="w-full h-full rounded-full object-cover opacity-80 group-hover:opacity-100">
              <div class="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-slate-900 rounded-full"></div>
           </button>

           <!-- User Menu Popover -->
           @if (isUserMenuOpen()) {
             <!-- Backdrop to close when clicking outside -->
             <div class="fixed inset-0 z-40 cursor-default" (click)="closeUserMenu()"></div>
             
             <!-- Menu -->
             <div class="absolute bottom-2 left-16 ml-3 w-64 bg-slate-800 border border-slate-700 rounded-xl shadow-[0_0_40px_rgba(0,0,0,0.5)] overflow-hidden z-50 animate-fade-in-up origin-bottom-left">
                <!-- User Header -->
                <div class="p-4 border-b border-slate-700 bg-slate-900/80">
                  <p class="text-white font-bold text-sm truncate">{{ auth.currentUser()?.firstName }} {{ auth.currentUser()?.lastName }}</p>
                  <p class="text-slate-500 text-xs truncate mt-0.5">{{ auth.currentUser()?.email }}</p>
                </div>
                
                <!-- Actions -->
                <div class="p-2 space-y-1 bg-slate-800">
                   <button (click)="switchCompany()" class="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-slate-300 hover:text-white hover:bg-slate-700 rounded-lg transition-colors text-left group">
                     <div class="w-6 flex justify-center"><i class="fa-solid fa-building-user text-sky-500 group-hover:scale-110 transition-transform"></i></div>
                     <span>Cambiar Empresa</span>
                   </button>
                   <button (click)="logout()" class="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-slate-300 hover:text-red-400 hover:bg-slate-700 rounded-lg transition-colors text-left group">
                     <div class="w-6 flex justify-center"><i class="fa-solid fa-arrow-right-from-bracket text-red-500 group-hover:scale-110 transition-transform"></i></div>
                     <span>Cerrar Sesión</span>
                   </button>
                </div>
             </div>
           }
        </div>
      </nav>

      <!-- COLUMN 2: Floating Fly-out Panel (Z-40) -->
      <!-- Positioned Absolute relative to the aside container -->
      <div class="absolute top-0 left-20 h-full bg-slate-850/95 backdrop-blur-xl border-r border-slate-700 shadow-2xl transition-all duration-300 ease-[cubic-bezier(0.25,0.8,0.25,1)] overflow-hidden z-40"
           [style.width.px]="hoveredItem() ? 260 : 0">
        
        <div class="w-[260px] h-full flex flex-col p-6">
           
           <!-- Panel Header -->
           @if (hoveredItem(); as item) {
             <div class="mb-6 animate-fade-in">
               <h2 class="text-xl font-bold text-white tracking-tight flex items-center gap-3">
                 <i [class]="item.icon + ' text-sky-500'"></i>
                 {{ item.title }}
               </h2>
               <p class="text-xs text-slate-400 mt-1 pl-8">Módulo de Gestión</p>
             </div>

             <!-- Submenu Links -->
             <div class="flex-1 space-y-1 overflow-y-auto pr-2 custom-scrollbar">
               @if (item.children) {
                 @for (sub of item.children; track sub.title) {
                   <a [routerLink]="sub.link" 
                      class="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:text-white hover:bg-slate-700/50 transition-colors group">
                      <i [class]="(sub.icon || 'fa-solid fa-circle') + ' text-xs w-5 text-center text-slate-500 group-hover:text-sky-400'"></i>
                      <span class="text-sm font-medium">{{ sub.title }}</span>
                   </a>
                 }
               } @else {
                 <!-- Fallback for items with no children (Direct Link) -->
                 <a [routerLink]="item.link" 
                    class="flex items-center gap-3 px-4 py-3 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400 hover:bg-sky-500/20 transition-colors">
                    <i class="fa-solid fa-arrow-right"></i>
                    <span class="text-sm font-bold">Ir al Dashboard Principal</span>
                 </a>
               }
             </div>
           }

           <!-- Decorative Footer inside Panel -->
           <div class="mt-auto pt-6 border-t border-slate-700">
             <div class="p-4 rounded-lg bg-slate-900 border border-slate-800">
               <p class="text-[10px] text-slate-500 uppercase font-bold mb-1">Estado del Sistema</p>
               <div class="flex items-center gap-2">
                 <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                 <span class="text-xs text-slate-300 font-mono">ONLINE 99.9%</span>
               </div>
             </div>
           </div>
        </div>

      </div>

    </aside>
  `
})
export class SidebarComponent {
  navService = inject(NavigationService);
  auth = inject(AuthService);
  
  // State for the Fly-out panel
  hoveredItem = signal<MenuItem | null>(null);
  
  // State for User Menu
  isUserMenuOpen = signal(false);

  constructor() {
    // Efecto: Actualizar menú cuando cambian los roles del usuario (currentContext)
    effect(() => {
      const context = this.auth.currentContext();
      if (context) {
        console.log(`[Sidebar] 🔄 Sincronizando menú con ${context.permissions?.length || 0} scopes.`);
        this.navService.generateMenu(context.permissions || []);
      } else {
        // Sin contexto, mostrar menú vacío (usuario guest)
        this.navService.generateMenu([]);
      }
    });
  }

  onIconHover(item: MenuItem) {
    if (!this.isUserMenuOpen()) {
       this.hoveredItem.set(item);
    }
  }

  closeFlyout() {
    this.hoveredItem.set(null);
  }

  isActiveOrHovered(item: MenuItem): boolean {
    return this.hoveredItem() === item;
  }

  toggleUserMenu() {
    this.isUserMenuOpen.update(v => !v);
    if (this.isUserMenuOpen()) {
      this.closeFlyout(); // Close modules when opening user menu
    }
  }

  closeUserMenu() {
    this.isUserMenuOpen.set(false);
  }

  switchCompany() {
    this.closeUserMenu();
    this.auth.switchCompany();
  }

  logout() {
    this.closeUserMenu();
    this.auth.logout();
  }
}
