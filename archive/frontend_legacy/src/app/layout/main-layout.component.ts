import { Component, inject, PLATFORM_ID, HostListener, signal, computed } from '@angular/core';
import { isPlatformBrowser, CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet, Router } from '@angular/router';
import { AuthService } from '@services/auth.service';
import { ThemeService } from '@services/theme.service';
import { TranslationService } from '@services/translation.service';
import { ToastService } from '@services/toast.service';
import { NavigationService, MenuItem } from '@services/navigation.service';
import { MatIconModule } from '@angular/material/icon';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { SystemHealthService } from '@services/system-health.service';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, MatIconModule, TranslatePipe],
  template: `
    <div class="flex h-screen bg-surface-bg overflow-hidden font-sans transition-colors duration-300 relative">
      
      <!-- Mobile Backdrop -->
      @if (isMobileMenuOpen()) {
        <div 
          (click)="isMobileMenuOpen.set(false)"
          class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[45] animate-fade-in lg:hidden uppercase font-black text-[10px] flex items-end justify-center pb-8 text-white/20 select-none"
        >
          Cerrar Menú
        </div>
      }

      <!-- Sidebar Navigation (Two Columns) -->
      <div 
        class="flex h-full z-50 fixed inset-y-0 left-0 lg:relative transition-all duration-500 transform lg:translate-x-0 group/nav shadow-2xl bg-nav-bar"
        [class.translate-x-0]="isMobileMenuOpen()"
        [class.-translate-x-full]="!isMobileMenuOpen()"
      >
        
        <!-- Column 1: Icon Bar (Fixed 80px) -->
        <aside class="w-20 bg-nav-bar border-r border-surface-border/[0.08] flex flex-col items-center py-6 z-50 shadow-2xl transition-colors duration-300">
          <!-- Custom Logo SVG (High-Fidelity) -->
          <div (click)="router.navigate(['/dashboard'])" class="w-12 h-12 mb-10 flex items-center justify-center relative group/logo cursor-pointer shrink-0">
            <div class="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse group-hover:bg-primary/40 transition-all"></div>
            <svg version="1.1" viewBox="0 0 630 630" class="w-11 h-11 relative z-10 drop-shadow-[0_0_10px_rgba(var(--color-primary),0.5)] text-primary overflow-visible transition-transform group-hover/logo:scale-110">
               <path fill="currentColor" d="M338.272552,413.107239 C330.839233,417.587891 323.635864,421.750458 316.649078,426.249237 C314.147339,427.860046 312.337738,427.765350 309.887360,426.264191 C295.698029,417.571625 281.434052,409.000305 267.160767,400.445618 C251.387711,390.992035 235.610611,381.544006 219.750412,372.238220 C217.142288,370.707947 216.119690,369.030518 216.127686,365.948029 C216.232727,325.462097 216.233948,284.975708 216.122742,244.489822 C216.113312,241.053635 217.221832,239.234848 220.231827,237.466171 C239.426285,226.187683 258.471649,214.655045 277.546661,203.173767 C288.055878,196.848251 298.572174,190.532074 308.986481,184.052917 C311.865021,182.262070 314.044312,182.169617 317.112610,184.033737 C347.010559,202.198257 377.041809,220.143265 406.979431,238.242828 C408.214264,238.989395 409.692230,240.630295 409.716217,241.880264 C409.929535,252.985809 409.840302,264.097137 409.840302,275.417236 C399.728363,275.417236 390.114716,275.417236 379.629395,275.417236 C379.629395,270.605988 379.466278,265.855347 379.690308,261.123047 C379.825562,258.265961 378.890594,256.633087 376.361328,255.174744 C359.512085,245.459778 342.747772,235.596924 325.998749,225.709518 C323.027374,223.955460 320.035461,222.115005 317.450348,219.859161 C314.357361,217.160156 311.853790,217.796646 308.676056,219.740143 C288.991638,231.779083 269.163849,243.584183 249.523483,255.693604 C247.929001,256.676697 246.492538,259.351105 246.479782,261.249664 C246.282745,290.570831 246.283813,319.893951 246.455124,349.215363 C246.465103,350.921570 247.898575,353.308319 249.380890,354.213226 C269.629700,366.574463 289.974365,378.780426 310.410675,390.829193 C311.852356,391.679169 314.641815,391.749207 316.055511,390.914032 C336.233826,378.992950 356.255341,366.806763 376.398499,354.825500 C378.900482,353.337280 379.792572,351.701019 379.664124,348.843384 C379.426453,343.556030 379.596100,338.250366 379.596100,332.514282 C389.774567,332.514282 399.497437,332.514282 409.861481,332.514282 C409.861481,341.669586 409.277893,350.991852 410.044250,360.201813 C410.669006,367.710052 408.017487,371.654205 401.523926,375.356476 C380.304047,387.455170 359.532196,400.339630 338.272552,413.107239 z" />
               <path fill="currentColor" opacity="0.8" d="M283.442566,467.396484 C262.120392,454.618988 241.163971,441.949097 220.106964,429.448669 C217.361130,427.818573 216.058136,426.174622 216.139130,422.819214 C216.379929,412.842804 216.225449,402.856842 216.225449,391.756836 C222.217041,395.304138 227.542450,398.403046 232.815720,401.588226 C257.871216,416.722260 282.948395,431.821198 307.919464,447.093445 C311.573212,449.328094 314.302826,449.486786 318.146393,447.152618 C353.730103,425.542633 389.440826,404.141174 425.195038,382.813904 C427.876617,381.214325 428.730133,379.505707 428.691589,376.506409 C428.524597,363.518463 428.598999,350.527435 428.586151,337.537506 C428.584564,335.927002 428.585968,334.316498 428.585968,332.396912 C438.836426,332.396912 448.441071,332.396912 458.523712,332.396912 C458.610016,333.981537 458.769440,335.570068 458.771973,337.158905 C458.801636,355.821960 458.725983,374.485779 458.897614,393.15 C458.927399,396.388306 457.952759,398.185547 455.136902,399.869202 C417.647003,422.284607 380.238403,444.835968 342.810883,467.355621 C334.399323,472.416779 325.916809,477.366089 317.620453,482.609650 C314.193390,484.775604 311.802094,485.204559 308.022400,482.503662 C300.315674,476.996521 291.900421,472.480896 283.442566,467.396484 z" />
               <path fill="currentColor" opacity="0.6" d="M235.082947,206.927277 C228.952850,210.641693 223.126678,214.158249 216.727325,218.020782 C216.524139,216.346359 216.258240,215.145996 216.251907,213.944244 C216.206238,205.280014 216.421875,196.607849 216.104980,187.954666 C215.970200,184.274109 217.271194,182.332092 220.342957,180.502716 C247.689163,164.216888 275.244720,148.247147 302.042664,131.096878 C310.486816,125.692780 316.027954,126.108505 324.255096,131.165054 C367.352722,157.653641 410.864594,183.469391 454.313843,209.382568 C457.737549,211.424484 458.994995,213.643417 458.939392,217.647873 C458.696472,235.140076 458.824310,252.637421 458.817810,270.132904 C458.817200,271.761902 458.817749,273.390900 458.817749,275.310699 C448.646667,275.310699 438.902893,275.310699 428.537384,275.310699 C428.537384,266.584900 428.525909,257.974396 428.541718,249.363983 C428.551178,244.200806 428.460663,239.031372 428.688995,233.876892 C428.829071,230.714569 427.883118,228.740555 425.011810,227.029099 C388.901855,205.505783 352.871704,183.848557 316.828644,162.213028 C314.669861,160.917175 312.924957,159.900711 310.120148,161.612503 C285.282288,176.771469 260.315552,191.719269 235.082947,206.927277 z" />
               <path fill="currentColor" opacity="0.4" d="M167.237305,339.999878 C167.231201,317.851624 167.280746,296.203033 167.153702,274.555511 C167.136078,271.554321 167.920334,269.757721 170.640457,268.201569 C179.381302,263.200989 187.936111,257.875275 197.124573,252.336243 C197.124573,306.893494 197.124573,360.744293 197.124573,415.345459 C187.396072,409.520905 178.017197,404.040222 168.842422,398.236908 C167.735657,397.536835 167.295074,395.094055 167.285614,393.454681 C167.183884,375.803589 167.230759,358.151611 167.237305,339.999878 z" />
               <path fill="currentColor" opacity="0.2" d="M197.510864,222.768204 C198.422928,228.129318 196.353119,231.068268 191.985764,233.426636 C185.028687,237.183426 178.436737,241.614136 171.662277,245.713440 C170.443161,246.451126 169.088699,246.965179 167.188995,247.872879 C167.188995,236.271759 167.036346,225.319336 167.357971,214.380859 C167.404770,212.788727 169.422058,210.785721 171.032471,209.786926 C179.466415,204.555984 188.063080,199.587387 197.508453,193.991287 C197.508453,203.847900 197.508453,213.075729 197.510864,222.768204 z" />
            </svg>
          </div>

          <!-- Main Icons -->
          <nav class="flex-1 flex flex-col gap-4 w-full px-2">
            @for (item of navService.menuItems(); track item.id) {
              <button 
                (mouseenter)="onHoverItem(item)"
                (click)="onSelectItem(item)"
                [class]="(navService.activeSubMenuId() === item.id || isRouteActive(item.route)) ? 'w-full h-14 flex items-center justify-center rounded-xl transition-all duration-300 relative group/item bg-primary/10 text-primary' : 'w-full h-14 flex items-center justify-center rounded-xl transition-all duration-300 relative group/item text-surface-text-muted hover:text-primary hover:bg-white/5'"
              >
                <!-- Active Indicator Bar -->
                @if (isRouteActive(item.route)) {
                  <div class="absolute left-0 w-1 h-8 bg-primary rounded-r-full shadow-[0_0_10px_rgba(var(--color-primary),0.8)]"></div>
                }
                
                <mat-icon class="text-2xl transition-transform group-hover/item:scale-110">{{ item.icon }}</mat-icon>
                
                <!-- Tooltip (Desktop) -->
                <div class="absolute left-24 px-3 py-2 bg-surface-card text-surface-text text-[10px] font-bold uppercase tracking-widest rounded-lg opacity-0 group-hover/item:opacity-100 pointer-events-none transition-opacity whitespace-nowrap border border-surface-border/[0.1] shadow-2xl z-[60]">
                  {{ item.translation_key | translate:item.label }}
                </div>
              </button>
            }
          </nav>

          <!-- Health Indicator & Bottom Actions -->
          <div class="mt-auto flex flex-col items-center gap-4">
            <div class="flex flex-col items-center gap-1 group/health cursor-help">
              <div class="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] animate-pulse"></div>
              <span class="text-[8px] text-emerald-500 font-black uppercase tracking-tighter opacity-0 group-hover/health:opacity-100 transition-opacity">Online</span>
            </div>
            
            <button (click)="theme.toggleTheme()" class="w-12 h-12 flex items-center justify-center rounded-xl text-surface-text-muted hover:bg-primary/10 hover:text-primary transition-all">
              <mat-icon>{{ theme.darkMode() ? 'light_mode' : 'dark_mode' }}</mat-icon>
            </button>
            
            <button (click)="logout()" class="w-12 h-12 flex items-center justify-center rounded-xl text-red-500/60 hover:bg-red-500/10 hover:text-red-400 transition-all">
              <mat-icon>logout</mat-icon>
            </button>
          </div>
        </aside>

        <!-- Column 2: Fly-out Panel (260px) -->
        <aside 
          class="w-64 bg-nav-panel/30 backdrop-blur-3xl border-r border-surface-border flex flex-col transition-all duration-500 absolute left-20 h-full z-40 shadow-2xl transform"
          [class.translate-x-0]="navService.activeSubMenuId()"
          [class.-translate-x-full]="!navService.activeSubMenuId()"
          (mouseleave)="onMouseLeavePanel()"
        >
          <div class="p-8 h-20 flex items-center border-b border-surface-border bg-surface-card/5">
            <span class="text-xs font-black text-surface-text uppercase tracking-[0.2em] italic">
              {{ getActiveMenuItemLabel() | translate:'Módulo' }}
            </span>
          </div>

          <div class="flex-1 p-6 space-y-2 overflow-y-auto custom-scrollbar">
            @if (getActiveSubItems(); as subItems) {
              @for (sub of subItems; track sub.id) {
                <a 
                  [routerLink]="sub.route"
                  routerLinkActive="bg-primary/10 text-primary border-primary/20"
                  (click)="navService.closeSubMenu()"
                  class="flex items-center gap-3 px-4 py-3 rounded-xl text-surface-text-muted hover:bg-primary/5 hover:text-primary transition-all border border-transparent group/sub"
                >
                  <div class="w-1.5 h-1.5 rounded-full bg-surface-text-muted group-hover/sub:bg-primary transition-colors"></div>
                  <span class="text-[10px] font-black uppercase tracking-widest">{{ sub.translation_key | translate:sub.label }}</span>
                </a>
              }
            } @else {
              <div class="flex flex-col items-center justify-center h-full opacity-20">
                <mat-icon class="text-4xl mb-2 text-surface-text-muted">auto_awesome</mat-icon>
                <span class="text-[10px] uppercase font-bold tracking-widest text-surface-text-muted">Select Module</span>
              </div>
            }
          </div>

          <!-- User Quick Switch Footer -->
          <div class="p-6 border-t border-surface-border bg-surface-card/10">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-8 h-8 rounded-lg bg-primary/20 border border-primary/30 flex items-center justify-center text-primary font-black text-xs">
                {{ auth.userFullName().substring(0,2).toUpperCase() }}
              </div>
              <div class="flex flex-col min-w-0">
                <span class="text-[10px] text-surface-text font-black truncate uppercase tracking-tight">{{ auth.userFullName() }}</span>
                <span class="text-[8px] text-surface-text-muted uppercase font-black tracking-widest opacity-60">Sesión Activa</span>
              </div>
            </div>
            <button 
              (click)="switchCompany()"
              class="w-full py-2 bg-primary/10 hover:bg-primary/20 border border-primary/20 rounded-lg text-[9px] font-black text-primary uppercase tracking-widest transition-all active:scale-95"
            >
              Cambiar Empresa
            </button>
          </div>
        </aside>
      </div>

      <!-- Main Content Area -->
      <div class="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <!-- Scan-line Overlay (Industrial Aesthetic) -->
        <div class="scan-line-overlay"></div>

        <!-- Main Content Background Accents -->
        <div class="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 blur-[120px] rounded-full pointer-events-none"></div>
        <div class="absolute bottom-0 left-0 w-[300px] h-[300px] bg-primary/5 blur-[100px] rounded-full pointer-events-none"></div>

        <!-- Read-Only Banner (Global) -->
        @if (health.isReadOnly()) {
          <div class="bg-red-600/90 backdrop-blur-md text-white px-8 py-2 text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-4 z-[100] shadow-lg animate-pulse shrink-0">
            <mat-icon class="text-sm">lock</mat-icon>
            <span>Modo Lectura: Pago Pendiente - Funciones de escritura deshabilitadas</span>
            <button class="bg-white text-red-600 px-3 py-1 rounded font-black hover:bg-red-50 transition-colors uppercase text-[9px]">Regularizar</button>
          </div>
        }

        <!-- Header -->
        <header class="h-20 bg-surface-card/30 backdrop-blur-xl border-b border-surface-border/[0.05] flex items-center justify-between px-4 lg:px-8 z-30 shrink-0 transition-colors">
          <div class="flex items-center gap-4">
            <!-- Hamburger Menu Button -->
            <button 
              (click)="isMobileMenuOpen.set(true)"
              class="lg:hidden p-2.5 text-surface-text-muted hover:text-primary transition-all rounded-xl hover:bg-surface-text/5 flex items-center justify-center border border-surface-border/[0.1]"
            >
              <mat-icon>menu</mat-icon>
            </button>

            <!-- Logo Completo (Icon + Text) -->
            <div class="hidden lg:flex items-center gap-2 mr-4 group/brand cursor-pointer" (click)="router.navigate(['/dashboard'])">
               <div class="w-8 h-8 relative flex items-center justify-center">
                  <div class="absolute inset-0 bg-primary/20 blur-lg rounded-full animate-pulse group-hover/brand:bg-primary/40"></div>
                  <svg version="1.1" viewBox="0 0 630 630" class="w-6 h-6 relative z-10 text-primary overflow-visible">
                    <path fill="currentColor" d="M338.272552,413.107239 C330.839233,417.587891 323.635864,421.750458 316.649078,426.249237 C314.147339,427.860046 312.337738,427.765350 309.887360,426.264191 C295.698029,417.571625 281.434052,409.000305 267.160767,400.445618 C251.387711,390.992035 235.610611,381.544006 219.750412,372.238220 C217.142288,370.707947 216.119690,369.030518 216.127686,365.948029 C216.232727,325.462097 216.233948,284.975708 216.122742,244.489822 C216.113312,241.053635 217.221832,239.234848 220.231827,237.466171 C239.426285,226.187683 258.471649,214.655045 277.546661,203.173767 C288.055878,196.848251 298.572174,190.532074 308.986481,184.052917 C311.865021,182.262070 314.044312,182.169617 317.112610,184.033737 C347.010559,202.198257 377.041809,220.143265 406.979431,238.242828 C408.214264,238.989395 409.692230,240.630295 409.716217,241.880264 C409.929535,252.985809 409.840302,264.097137 409.840302,275.417236 C399.728363,275.417236 390.114716,275.417236 379.629395,275.417236 C379.629395,270.605988 379.466278,265.855347 379.690308,261.123047 C379.825562,258.265961 378.890594,256.633087 376.361328,255.174744 C359.512085,245.459778 342.747772,235.596924 325.998749,225.709518 C323.027374,223.955460 320.035461,222.115005 317.450348,219.859161 C314.357361,217.160156 311.853790,217.796646 308.676056,219.740143 C288.991638,231.779083 269.163849,243.584183 249.523483,255.693604 C247.929001,256.676697 246.492538,259.351105 246.479782,261.249664 C246.282745,290.570831 246.283813,319.893951 246.455124,349.215363 C246.465103,350.921570 247.898575,353.308319 249.380890,354.213226 C269.629700,366.574463 289.974365,378.780426 310.410675,390.829193 C311.852356,391.679169 314.641815,391.749207 316.055511,390.914032 C336.233826,378.992950 356.255341,366.806763 376.398499,354.825500 C378.900482,353.337280 379.792572,351.701019 379.664124,348.843384 C379.426453,343.556030 379.596100,338.250366 379.596100,332.514282 C389.774567,332.514282 399.497437,332.514282 409.861481,332.514282 C409.861481,341.669586 409.277893,350.991852 410.044250,360.201813 C410.669006,367.710052 408.017487,371.654205 401.523926,375.356476 C380.304047,387.455170 359.532196,400.339630 338.272552,413.107239 z" />
                  </svg>
               </div>
               <span class="text-xl font-black text-surface-text tracking-tighter uppercase italic group-hover/brand:text-primary transition-colors">InternoCore</span>
            </div>

            <div class="flex flex-col">
              <span class="text-[9px] text-surface-text-muted font-black uppercase tracking-[0.2em] opacity-60">Contexto Operativo</span>
              <span class="text-sm text-surface-text font-black tracking-tighter uppercase italic">{{ activeCompanyName() }}</span>
            </div>
            <div class="h-8 w-px bg-surface-border/[0.1] mx-2"></div>
            <div class="flex items-center gap-2">
               <span class="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded text-[8px] font-black uppercase tracking-widest">Master Ledger</span>
            </div>
          </div>

          <div class="flex items-center gap-6">
            <div class="flex items-center gap-2">
              <!-- Language Switch -->
              <div class="relative group/lang-menu">
                <button (click)="showLangMenu.set(!showLangMenu())" class="text-surface-text-muted hover:text-primary transition-colors p-2.5 rounded-xl hover:bg-surface-text/5 flex items-center gap-2">
                  <mat-icon class="text-lg">language</mat-icon>
                  <span class="text-[10px] font-black uppercase tracking-tighter">{{ ts.currentLang()?.toUpperCase() || 'ES' }}</span>
                </button>
                @if (showLangMenu()) {
                  <div class="absolute right-0 mt-2 w-40 bg-surface-card border border-surface-border rounded-2xl shadow-2xl py-2 z-[200] animate-fade-in-up">
                    <button (click)="changeLang('es')" class="w-full px-5 py-3 text-left hover:bg-primary/10 text-[10px] font-black tracking-widest uppercase transition-colors" [class.text-primary]="ts.currentLang() === 'es'">
                      Español
                    </button>
                    <button (click)="changeLang('en')" class="w-full px-5 py-3 text-left hover:bg-primary/10 text-[10px] font-black tracking-widest uppercase transition-colors" [class.text-primary]="ts.currentLang() === 'en'">
                      English (US)
                    </button>
                  </div>
                }
              </div>

              <button class="relative text-surface-text-muted hover:text-primary transition-colors p-2.5 rounded-xl hover:bg-surface-text/5">
                <mat-icon class="text-lg">notifications</mat-icon>
                <span class="absolute top-2.5 right-2.5 w-1.5 h-1.5 bg-red-500 rounded-full border border-surface-card"></span>
              </button>

                <div class="h-8 w-px bg-surface-border/[0.1] mx-2"></div>

                <!-- Theme Toggle -->
                <button (click)="theme.toggleTheme()" class="text-surface-text-muted hover:text-primary transition-colors p-2.5 rounded-xl hover:bg-surface-text/5 flex items-center justify-center">
                  <mat-icon>{{ theme.darkMode() ? 'light_mode' : 'dark_mode' }}</mat-icon>
                </button>

                <div class="h-8 w-px bg-surface-border/[0.1] mx-2"></div>
                
                <div class="flex items-center gap-3 pl-2 group/user cursor-pointer">
                <div class="text-right hidden sm:block">
                  <div class="text-[10px] text-surface-text font-black uppercase tracking-tight truncate max-w-[120px]">{{ auth.userFullName() }}</div>
                  <div class="text-[8px] text-surface-text-muted uppercase font-black tracking-widest opacity-60 italic">{{ 'AUTH_ROLE_USER' }}</div>
                </div>
                <div class="w-9 h-9 rounded-xl border border-surface-border bg-surface-card/5 flex items-center justify-center overflow-hidden transition-all group-hover/user:border-primary/30">
                   <mat-icon class="text-surface-text-muted group-hover/user:text-primary transition-colors">person</mat-icon>
                </div>
              </div>
            </div>
          </div>
        </header>

        <!-- Main Content -->
        <main class="flex-1 overflow-y-auto custom-scrollbar bg-surface-bg p-8 relative z-20 transition-colors duration-300">
          <div class="max-w-7xl mx-auto">
             <router-outlet></router-outlet>
          </div>
        </main>
      </div>
    </div>
  `
})
export class MainLayoutComponent {
  auth = inject(AuthService);
  theme = inject(ThemeService);
  ts = inject(TranslationService);
  toast = inject(ToastService);
  navService = inject(NavigationService);
  router = inject(Router);
  health = inject(SystemHealthService);
  platformId = inject(PLATFORM_ID);
  isBrowser = isPlatformBrowser(this.platformId);

  isMobileMenuOpen = signal(false);
  showLangMenu = signal(false);

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.group\\/lang-menu')) {
      this.showLangMenu.set(false);
    }
  }

  onHoverItem(item: MenuItem) {
    if (item.subItems && item.subItems.length > 0) {
      this.navService.activeSubMenuId.set(item.id);
    }
  }

  onSelectItem(item: MenuItem) {
    if (item.route) {
      this.router.navigate([item.route]);
      this.navService.closeSubMenu();
    } else if (item.subItems && item.subItems.length > 0) {
      this.navService.toggleSubMenu(item.id);
    }
  }

  onMouseLeavePanel() {
    this.navService.closeSubMenu();
  }

  getActiveMenuItemLabel() {
    const activeId = this.navService.activeSubMenuId();
    const item = this.navService.menuItems().find(i => i.id === activeId);
    return item?.translation_key ? item.translation_key : (item?.label || 'Módulo');
  }

  getActiveSubItems() {
    const activeId = this.navService.activeSubMenuId();
    const item = this.navService.menuItems().find(i => i.id === activeId);
    return item?.subItems || null;
  }

  isRouteActive(route?: string) {
    if (!route) return false;
    return this.router.url.startsWith(route);
  }

  logout() {
    this.toast.info('Finalizando sesión industrial...', 'Seguridad');
    this.auth.logout();
  }

  switchCompany() {
    this.toast.info('Cambiando contexto de empresa...', 'Sistema');
    this.auth.authStep.set('handshake');
    this.router.navigate(['/select-company']);
  }

  changeLang(lang: 'es' | 'en') {
    this.ts.setLanguage(lang);
    this.showLangMenu.set(false);
  }

  activeCompanyName = computed(() => {
    const ctx = this.auth.currentContext();
    if (ctx && ctx.company_name) return ctx.company_name;

    if (this.isBrowser) {
      const stored = localStorage.getItem('_ic_auth_ctx');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          return parsed.company_name || 'Planta Norte - Automotriz';
        } catch {
          return 'Planta Norte - Automotriz';
        }
      }
    }
    return 'Seleccione Empresa';
  });
}
