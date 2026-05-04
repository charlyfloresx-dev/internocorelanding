import {Component, inject, PLATFORM_ID, HostListener, signal, computed} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {CommonModule, KeyValuePipe} from '@angular/common';
import {RouterLink, RouterLinkActive, RouterOutlet, Router} from '@angular/router';
import {AuthService} from '../../core/services/auth.service';
import {ThemeService} from '../../core/services/theme.service';
import {TranslationService} from '../../core/services/translation.service';
import {ToastService} from '../../core/services/toast.service';
import {NavigationService, MenuItem} from '../../core/services/navigation.service';
import {MatIconModule} from '@angular/material/icon';
import {TranslatePipe} from '../../shared/pipes/translate.pipe';
import {CurrencyService} from '../../core/services/currency.service';
import {SystemHealthService} from '../../core/services/system-health.service';
import {NotificationHubService} from '../../core/services/notification-hub.service';
import {SupportDrawerComponent} from '../../shared/components/support-drawer.component';
import {SideDrawerComponent} from '../../shared/components/side-drawer.component';
import {SideDrawerService} from '../../core/services/side-drawer.service';
import {TicketsFormComponent} from '../../modules/monitor/tickets/components/tickets-form.component';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, MatIconModule, TranslatePipe, KeyValuePipe, SideDrawerComponent],
  template: `
    <div 
      [class.dark]="themeService.darkMode()"
      class="flex h-screen overflow-hidden font-sans transition-colors duration-300"
      [ngClass]="themeService.darkMode() ? 'bg-ic-dark' : 'bg-white'"
    >
      
      <!-- Mobile Overlay -->
      <div 
        *ngIf="isMobileMenuOpen()" 
        (click)="isMobileMenuOpen.set(false)"
        class="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-[55] animate-in fade-in duration-300"
      ></div>

      <div 
        class="fixed lg:relative flex h-full z-[100] no-print transition-transform duration-500 ease-out"
        [class.-translate-x-full]="!isMobileMenuOpen() && isMobile()"
        [class.translate-x-0]="isMobileMenuOpen() || !isMobile()"
      >
        
        <!-- Column 1: Icon Bar (Fixed 80px) -->
        <aside class="w-20 bg-nav-bar border-r border-surface-border flex flex-col items-center py-6 z-[110] shadow-2xl transition-colors duration-300">
          <!-- Custom Logo SVG -->
          <div class="w-12 h-12 mb-10 flex items-center justify-center relative group/logo cursor-pointer" (click)="isMobileMenuOpen.set(false)">
            <div class="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse group-hover:bg-primary/40 transition-all"></div>
            <svg version="1.1" viewBox="0 0 630 630" class="w-11 h-11 relative z-10 drop-shadow-[0_0_10px_rgba(0,229,255,0.5)] text-primary overflow-visible transition-colors duration-300">
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
                [class.bg-primary/10]="navService.activeSubMenuId() === item.id || isRouteActive(item.route)"
                [class.text-primary]="navService.activeSubMenuId() === item.id || isRouteActive(item.route)"
                class="w-full h-14 flex items-center justify-center rounded-xl transition-all duration-300 relative group/item text-surface-text-muted hover:text-primary hover:bg-white/5"
              >
                <!-- Active Indicator Bar -->
                @if (isRouteActive(item.route)) {
                  <div class="absolute left-0 w-1 h-8 bg-primary rounded-r-full shadow-[0_0_10px_rgba(0,229,255,0.8)]"></div>
                }
                
                <mat-icon class="text-2xl transition-transform group-hover/item:scale-110">{{ item.icon }}</mat-icon>
                
                <!-- Tooltip (Desktop) -->
                <div class="absolute left-24 px-3 py-2 bg-surface-card text-surface-text text-[10px] font-bold uppercase tracking-widest rounded-lg opacity-0 group-hover/item:opacity-100 pointer-events-none transition-opacity whitespace-nowrap border border-surface-border shadow-2xl z-[60]">
                  {{ item.translation_key | translate:item.label }}
                </div>
              </button>
            }
          </nav>

          <!-- Column 1 Footer Buttons: Premium User Context -->
          <div class="mt-auto flex flex-col items-center gap-3 pb-6 w-full px-2">
            
            <!-- Health Indicator (Subtle) -->
            <div class="flex items-center justify-center mb-2 group/health cursor-help" [title]="'System Health: ' + healthService.overallStatus()">
              <div class="w-1.5 h-1.5 rounded-full"
                   [ngClass]="{
                     'bg-neon-green neon-glow-green': healthService.overallStatus() === 'online',
                     'bg-yellow-500': healthService.overallStatus() === 'degraded',
                     'bg-red-500 animate-pulse': healthService.overallStatus() === 'offline'
                   }"></div>
            </div>

            <!-- Quick Tickets (If allowed) -->
            @if (authService.hasPermission('tickets:view')) {
              <button 
                routerLink="/monitor/tickets"
                routerLinkActive="bg-primary/20 text-primary"
                (click)="navService.closeSubMenu()"
                class="w-12 h-12 flex items-center justify-center rounded-xl text-surface-text-muted hover:bg-primary/10 hover:text-primary transition-all relative group/tickets"
              >
                <mat-icon class="text-xl">confirmation_number</mat-icon>
                <div class="absolute left-16 px-2 py-1 bg-surface-card border border-surface-border rounded text-[8px] font-bold uppercase opacity-0 group-hover/tickets:opacity-100 pointer-events-none transition-all whitespace-nowrap z-50">
                  {{ 'menu.my_tickets' | translate:'Mis Tickets' }}
                </div>
              </button>
            }
            
            <!-- User Profile Block -->
            <button 
              (click)="navService.toggleSubMenu('user')" 
              [class.bg-primary/10]="navService.activeSubMenuId() === 'user'"
              [class.ring-2]="navService.activeSubMenuId() === 'user'"
              class="w-12 h-12 flex items-center justify-center rounded-2xl bg-surface-card border border-surface-border text-surface-text-muted hover:bg-primary/10 hover:text-primary transition-all relative group/user overflow-hidden"
            >
              @if (authService.currentUser()?.full_name) {
                <span class="text-[10px] font-black tracking-tighter text-primary">
                  {{ authService.currentUser()?.full_name?.substring(0,2)?.toUpperCase() }}
                </span>
              } @else {
                <mat-icon>person</mat-icon>
              }
              
              <!-- Operative Plan Glow (Only for Demo) -->
              @if (isDemoCompany()) {
                <div class="absolute inset-0 bg-primary/5 animate-pulse"></div>
                <div class="absolute -top-1 -right-1 w-3 h-3 bg-primary rounded-full border-2 border-nav-bar z-10"></div>
              }
            </button>
          </div>
        </aside>

        <!-- Column 2: Fly-out Panel (260px) -->
        <aside 
          class="w-64 bg-white/70 dark:bg-slate-900/70 backdrop-blur-2xl border-r border-slate-200 dark:border-white/10 flex flex-col transition-all duration-500 absolute left-20 h-full z-[105] shadow-2xl transform"
          [class.translate-x-0]="navService.activeSubMenuId()"
          [class.-translate-x-full]="!navService.activeSubMenuId()"
          (mouseleave)="onMouseLeavePanel()"
        >
          <div class="p-8 h-20 flex items-center border-b border-slate-100 dark:border-white/10 bg-white/40 dark:bg-black/40">
            <span class="text-[10px] font-black text-primary uppercase tracking-[0.2em]">
              {{ navService.activeSubMenuId() === 'user' ? ('auth.user_menu' | translate:'Menú de Usuario') : (getActiveMenuItem()?.translation_key | translate:(getActiveMenuItem()?.label || 'Módulo')) }}
            </span>
          </div>

          <div class="flex-1 p-6 space-y-2 overflow-y-auto custom-scrollbar">
            @if (navService.activeSubMenuId() === 'user') {
              <!-- User Specific Menu -->
              <!-- User Identity Header -->
              <div class="px-2 mb-6">
                <div class="flex items-center gap-3 mb-2">
                  <div class="text-[14px] font-black text-slate-900 dark:text-white truncate max-w-[150px]">
                    {{ authService.currentUser()?.full_name }}
                  </div>
                  @if (isDemoCompany()) {
                    <span class="px-1.5 py-0.5 rounded bg-primary/20 border border-primary/40 text-[7px] text-primary font-black uppercase tracking-widest animate-pulse">
                      Operative Plan
                    </span>
                  }
                </div>
                <div class="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-[0.1em] mb-4 truncate">
                  {{ authService.currentUser()?.email }}
                </div>
                
                <button 
                  (click)="navService.closeSubMenu()" 
                  routerLink="/monitor/tickets"
                  [queryParams]="{ filter: 'mine' }"
                  class="bg-primary/10 hover:bg-primary/20 text-primary rounded-xl px-4 py-2 flex items-center gap-2 transition-all border border-primary/20 group-hover:scale-105 active:scale-95">
                  <mat-icon class="text-[18px]">confirmation_number</mat-icon>
                  <span class="text-[10px] font-black uppercase tracking-wider">Mis Tickets</span>
                </button>
              </div>

              @if (navService.isAdmin()) {
                <div class="pt-4 border-t border-slate-100 dark:border-white/5 space-y-1">
                  <span class="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-2 block px-2">Administración</span>
                  
                  <a 
                    routerLink="/admin/users"
                    (click)="navService.closeSubMenu()"
                    routerLinkActive="bg-primary/10 text-primary border-primary/20 shadow-inner"
                    class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-500 dark:text-slate-400 hover:bg-primary/5 hover:text-primary transition-all border border-transparent group/sub"
                  >
                    <mat-icon class="text-lg">group</mat-icon>
                    <span class="text-[10px] font-bold uppercase tracking-widest">{{ 'menu.settings_users' | translate:'Usuarios' }}</span>
                  </a>

                  <a 
                    routerLink="/admin/staff"
                    (click)="navService.closeSubMenu()"
                    routerLinkActive="bg-primary/10 text-primary border-primary/20 shadow-inner"
                    class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-500 dark:text-slate-400 hover:bg-primary/5 hover:text-primary transition-all border border-transparent group/sub"
                  >
                    <mat-icon class="text-lg">badge</mat-icon>
                    <span class="text-[10px] font-bold uppercase tracking-widest">{{ 'menu.settings_staff' | translate:'Personal de Planta' }}</span>
                  </a>

                  <a 
                    routerLink="/system/config"
                    (click)="navService.closeSubMenu()"
                    routerLinkActive="bg-primary/10 text-primary border-primary/20 shadow-inner"
                    class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-500 dark:text-slate-400 hover:bg-primary/5 hover:text-primary transition-all border border-transparent group/sub"
                  >
                    <mat-icon class="text-lg">settings_suggest</mat-icon>
                    <span class="text-[10px] font-bold uppercase tracking-widest">{{ 'menu.settings_system' | translate:'Configuración' }}</span>
                  </a>
                </div>
              }
            } @else if (getActiveSubItems(); as subItems) {
              @for (sub of subItems; track sub.id) {
                <a 
                  [routerLink]="sub.route"
                  [queryParams]="sub.queryParams || {}"
                  routerLinkActive="bg-primary/10 text-primary border-primary/20 shadow-inner"
                  (click)="navService.closeSubMenu()"
                  class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-500 dark:text-slate-400 hover:bg-primary/5 hover:text-primary transition-all border border-transparent group/sub"
                >
                  <div class="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-700 group-hover/sub:bg-primary transition-colors"></div>
                  <span class="text-[10px] font-bold uppercase tracking-widest">{{ sub.translation_key | translate:sub.label }}</span>
                </a>
              }
            } @else {
              <div class="flex flex-col items-center justify-center h-full opacity-20">
                <mat-icon class="text-4xl mb-2">auto_awesome</mat-icon>
                <span class="text-[10px] uppercase font-bold tracking-widest">{{ 'auth.select_module' | translate:'Seleccione Módulo' }}</span>
              </div>
            }
          </div>

            <!-- Context Footer -->
            <div class="flex flex-col gap-3">
              <div class="px-4 py-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-white/5">
                <div class="text-[7px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Empresa Activa</div>
                <div class="text-[10px] font-bold text-slate-700 dark:text-slate-300 truncate">
                  {{ ($any(authService.session())).company_name || 'InternoCore' }}
                </div>
              </div>

              <button 
                (click)="logout()"
                class="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl bg-red-500/5 hover:bg-red-500/10 text-red-500 transition-all border border-red-500/10 group/logout"
              >
                <mat-icon class="text-lg">logout</mat-icon>
                <span class="text-[10px] font-black uppercase tracking-[0.2em]">{{ 'auth.logout' | translate:'Cerrar Sesión' }}</span>
              </button>
            </div>
        </aside>
      </div>

      <!-- Main Content -->
      <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
        <!-- Read-Only Banner (Global) -->
        @if (authService.isReadOnly()) {
          <div class="bg-red-600 text-white px-8 py-2 text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-4 z-30 shadow-lg animate-pulse">
            <mat-icon class="text-sm">lock</mat-icon>
            <span>Modo Lectura: Pago Pendiente - Funciones de escritura deshabilitadas</span>
            <button 
              (click)="router.navigate(['/billing/subscription'])"
              class="bg-white text-red-600 px-3 py-1 rounded font-bold hover:bg-red-50 transition-colors"
            >
              Regularizar
            </button>
          </div>
        }

        <!-- Header Container -->
        <div class="relative z-[80]">
          <header 
            class="h-20 bg-white/70 dark:bg-slate-900/70 backdrop-blur-2xl border-b border-slate-200 dark:border-white/10 flex items-center justify-between px-4 md:px-8 shadow-2xl transition-all duration-300 no-print"
          >
            <div class="flex items-center gap-4">
              <!-- Hamburger Toggle (Mobile) -->
              <button 
                (click)="isMobileMenuOpen.set(!isMobileMenuOpen())"
                class="lg:hidden p-2 text-surface-text-muted hover:text-primary transition-colors"
                [title]="translationService.translate('common.menu', 'Menu')"
              >
                <mat-icon>{{ isMobileMenuOpen() ? 'close' : 'menu' }}</mat-icon>
              </button>

              <div class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 ml-2">
                <!-- Company Selector (Premium Remodel) -->
                <div class="relative group group/tenant">
                  <button 
                    (click)="showCompanyMenu.set(!showCompanyMenu())"
                    class="flex items-center gap-3 p-2 pr-6 rounded-2xl transition-all relative z-[101]
                           bg-transparent text-slate-900 hover:bg-slate-100/50
                           dark:text-white dark:hover:bg-white/5"
                  >
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-xl shadow-cyan-500/10 transition-transform group-hover:scale-110">
                      <mat-icon class="text-sm">business</mat-icon>
                    </div>
                    <div class="text-left hidden md:block">
                      <p class="text-[8px] font-black uppercase tracking-[0.25em] leading-none mb-1 text-primary/70 dark:text-primary/90">
                        TENANT ACTIVO
                      </p>
                      <p class="text-xs font-black truncate max-w-[140px] text-slate-900 dark:text-white">
                        {{ activeCompanyName() }}
                      </p>
                    </div>
                    <mat-icon class="text-slate-400 dark:text-slate-500 group-hover:text-primary transition-all text-xl ml-1">expand_more</mat-icon>
                  </button>

                  @if (showCompanyMenu()) {
                    <div class="absolute top-full mt-3 left-0 w-80 border rounded-2xl shadow-[0_30px_60px_-12px_rgba(0,0,0,0.5)] backdrop-blur-2xl overflow-hidden z-[100] animate-in fade-in zoom-in-95 duration-200
                                bg-white/95 border-slate-200
                                dark:bg-slate-900/95 dark:border-white/10">
                      <div class="p-4 border-b border-slate-100 dark:border-white/5 flex items-center justify-between">
                        <h3 class="text-[10px] font-black text-primary uppercase tracking-widest">Cambiar Contexto</h3>
                        <mat-icon class="text-slate-300 text-sm">settings</mat-icon>
                      </div>
                      
                      <div class="max-h-80 overflow-y-auto custom-scrollbar">
                        @for (company of authService.availableCompanies(); track company.company_id) {
                          <button 
                            (click)="switchCompanyTo(company.company_id)"
                            [disabled]="company.company_id === authService.activeCompanyId()"
                            class="w-full p-4 flex items-center gap-4 transition-all text-left group/item disabled:opacity-50 disabled:cursor-default
                                   hover:bg-primary/5 dark:hover:bg-white/5"
                          >
                            <div class="w-10 h-10 rounded-xl flex items-center justify-center border transition-all
                                        bg-slate-100 border-slate-200 dark:bg-slate-800 dark:border-white/5 group-hover/item:border-primary/50">
                              <mat-icon class="text-slate-400 dark:text-slate-500 group-hover/item:text-primary transition-colors">domain</mat-icon>
                            </div>
                            <div class="flex-1 min-w-0">
                              <p class="text-xs font-bold truncate text-slate-900 dark:text-white">{{ company.company_name }}</p>
                              <p class="text-[9px] font-medium text-slate-400 dark:text-slate-500 truncate">{{ company.role_name || 'Collaborator' }}</p>
                            </div>
                            @if (company.company_id === authService.activeCompanyId()) {
                              <mat-icon class="text-primary text-[18px]">check_circle</mat-icon>
                            }
                          </button>
                        }
                      </div>

                      <div class="p-3 bg-slate-50/50 dark:bg-black/20 flex justify-center border-t border-slate-100 dark:border-white/5">
                        <button (click)="switchCompany()" class="text-[9px] font-black text-slate-500 hover:text-primary uppercase tracking-[0.2em] transition-colors flex items-center gap-2">
                          <mat-icon class="text-xs">grid_view</mat-icon>
                          Full Manager Protocol
                        </button>
                      </div>
                    </div>

                    <!-- Overlay to close -->
                    <div class="fixed inset-0 z-40 bg-transparent" (click)="showCompanyMenu.set(false)"></div>
                  }
                </div>
              </div>
            </div>

            <div class="flex items-center gap-6">
              <div class="flex items-center gap-4">
                <!-- Currency Selector & Decision Dashboard -->
                <div class="relative">
                  <button 
                    (click)="showCurrencyMenu.set(!showCurrencyMenu())"
                    class="text-surface-text-muted hover:text-primary transition-colors p-2 rounded-lg hover:bg-surface-text/5 flex items-center gap-2"
                    [title]="'Decision Dashboard / Currency'"
                  >
                    <mat-icon class="text-xl">payments</mat-icon>
                    <span class="text-[11px] font-black uppercase tracking-tighter">{{ currencyService.currentCurrency().code }}</span>
                  </button>

                  @if (showCurrencyMenu()) {
                    <div class="absolute right-0 mt-2 w-72 bg-surface-card border border-surface-border rounded-xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-50 py-2 animate-in fade-in zoom-in duration-200">
                      
                      <!-- Currency Tabs -->
                      <div class="px-4 py-2 border-b border-surface-border mb-2 flex justify-between items-center bg-black/20">
                        <span class="text-[10px] font-black uppercase text-surface-text-muted tracking-widest">Active Currency</span>
                      </div>
                      <div class="flex px-3 gap-2 mb-3">
                        @for (curr of currencyService.currencies; track curr.code) {
                          <button 
                            (click)="currencyService.setCurrency(curr.code)"
                            class="flex-1 py-1.5 text-center text-[10px] font-black uppercase tracking-widest rounded-lg transition-all border"
                            [class.bg-primary/10]="currencyService.currentCurrency().code === curr.code"
                            [class.text-primary]="currencyService.currentCurrency().code === curr.code"
                            [class.border-primary/50]="currencyService.currentCurrency().code === curr.code"
                            [class.text-surface-text-muted]="currencyService.currentCurrency().code !== curr.code"
                            [class.border-transparent]="currencyService.currentCurrency().code !== curr.code"
                            [class.hover:bg-white/5]="currencyService.currentCurrency().code !== curr.code"
                          >
                            {{ curr.code }}
                          </button>
                        }
                      </div>

                      <!-- Decision Dashboard: 4 Sources -->
                      <div class="px-4 py-2 border-y border-surface-border mt-1 mb-2 bg-black/40">
                        <span class="text-[9px] font-black uppercase text-surface-text tracking-widest flex items-center gap-2">
                           <mat-icon class="text-[14px] text-primary">auto_graph</mat-icon>
                           Decision Dashboard
                        </span>
                        <p class="text-[8px] text-surface-text-muted mt-1 leading-tight">Compare 4 sources (Banxico, Banks, Houses, Global) to set the operational rate.</p>
                      </div>
                      
                      <div class="px-3 space-y-1 mb-3">
                        @for (market of currencyService.markets() | keyvalue; track market.key) {
                           <div 
                              class="flex items-center justify-between px-3 py-1.5 rounded-lg bg-surface-text/5 hover:bg-primary/20 hover:border-primary/50 transition-all group cursor-pointer border border-transparent"
                              title="Adopt this rate"
                              (click)="manualRateInput.value = market.value.toString()"
                            >
                              <span class="text-[9px] font-bold text-surface-text uppercase tracking-wider group-hover:text-primary transition-colors">{{ market.key }}</span>
                              <div class="flex items-center gap-2">
                                <span class="text-[11px] font-black text-primary group-hover:text-white transition-colors">{{ market.value | currency:'':'':'1.2-4' }}</span>
                              </div>
                           </div>
                        }
                      </div>

                      <!-- Manual Override -->
                      <div class="px-3 mt-1 mb-2 flex flex-col gap-2">
                         <div class="flex gap-2">
                           <input type="number" step="0.01" class="flex-1 bg-ic-dark border border-surface-border text-xs rounded-lg px-3 py-1.5 text-surface-text font-bold focus:border-primary outline-none transition-colors" placeholder="$ 17.50..." #manualRateInput>
                           <button 
                              class="bg-primary text-ic-dark hover:bg-white hover:text-black px-4 rounded-lg font-black text-[9px] uppercase tracking-widest transition-all shadow-lg"
                              (click)="setManualRate(manualRateInput.value); showCurrencyMenu.set(false)"
                            >
                              Fix
                           </button>
                         </div>
                      </div>

                    </div>
                  }
                </div>

                <!-- Language Selector -->
                <div class="relative">
                  <button 
                    (click)="showLangMenu.set(!showLangMenu())"
                    class="text-surface-text-muted hover:text-primary transition-colors p-2 rounded-lg hover:bg-surface-text/5 flex items-center gap-2"
                    [title]="translationService.translate('common.change_language', 'Change Language')"
                  >
                    <mat-icon class="text-xl">language</mat-icon>
                    <span class="text-[11px] font-black uppercase tracking-tighter">{{ translationService.currentLang().toUpperCase() }}</span>
                  </button>

                  @if (showLangMenu()) {
                    <div class="absolute right-0 mt-2 w-36 bg-surface-card border border-surface-border rounded-xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-50 py-2 animate-in fade-in zoom-in duration-200">
                      <button 
                        (click)="translationService.setLanguage('es'); showLangMenu.set(false)"
                        class="w-full px-4 py-2.5 text-left text-[10px] font-bold uppercase tracking-widest hover:bg-primary/10 hover:text-primary transition-colors flex items-center justify-between group/lang"
                        [class.text-primary]="translationService.currentLang() === 'es'"
                      >
                        <span class="flex items-center gap-2">
                          <span class="w-1.5 h-1.5 rounded-full bg-surface-text-muted group-hover/lang:bg-primary transition-colors" [class.bg-primary]="translationService.currentLang() === 'es'"></span>
                          Español
                        </span>
                        @if (translationService.currentLang() === 'es') {
                          <mat-icon class="text-sm">check</mat-icon>
                        }
                      </button>
                      <button 
                        (click)="translationService.setLanguage('en'); showLangMenu.set(false)"
                        class="w-full px-4 py-2.5 text-left text-[10px] font-bold uppercase tracking-widest hover:bg-primary/10 hover:text-primary transition-colors flex items-center justify-between group/lang"
                        [class.text-primary]="translationService.currentLang() === 'en'"
                      >
                        <span class="flex items-center gap-2">
                          <span class="w-1.5 h-1.5 rounded-full bg-surface-text-muted group-hover/lang:bg-primary transition-colors" [class.bg-primary]="translationService.currentLang() === 'en'"></span>
                          English (US)
                        </span>
                        @if (translationService.currentLang() === 'en') {
                          <mat-icon class="text-sm">check</mat-icon>
                        }
                      </button>
                    </div>
                  }
                </div>

                <!-- Theme Toggle -->
                <button 
                  (click)="themeService.toggleDarkMode()"
                  class="text-surface-text-muted hover:text-primary transition-colors p-2 rounded-lg hover:bg-surface-text/5"
                  [title]="themeService.darkMode() ? 'Switch to light mode' : 'Switch to dark mode'"
                >
                  <mat-icon class="text-xl">{{ themeService.darkMode() ? 'light_mode' : 'dark_mode' }}</mat-icon>
                </button>

                  <!-- Support AI Drawer -->
                  <button 
                    (click)="openSupportDrawer()"
                    class="text-surface-text-muted hover:text-primary transition-colors p-2 rounded-lg hover:bg-surface-text/5"
                    title="Soporte AI"
                  >
                    <mat-icon class="text-xl">support_agent</mat-icon>
                  </button>

                  <div class="h-8 w-px bg-surface-border mx-2"></div>
                </div>
              </div>
            </header>
          </div>

          <!-- Generic Side Drawer Instance -->
          <app-side-drawer></app-side-drawer>

        <!-- Content Area -->
        <main 
          class="flex-1 overflow-y-auto p-4 md:p-8 custom-scrollbar relative transition-colors duration-300"
          [ngClass]="themeService.darkMode() ? 'bg-ic-dark' : 'bg-white'"
          (click)="isMobileMenuOpen.set(false)"
        >
          <!-- Background Glow -->
          <div *ngIf="themeService.darkMode()" class="absolute top-0 right-0 w-1/2 h-1/2 bg-primary/5 blur-[150px] pointer-events-none"></div>
          
          <div class="relative max-w-7xl mx-auto">
            <router-outlet></router-outlet>
          </div>
        </main>
      </div>
    </div>
  `
})
export class MainLayoutComponent {
  authService = inject(AuthService);
  themeService = inject(ThemeService);
  translationService = inject(TranslationService);
  toastService = inject(ToastService);
  navService = inject(NavigationService);
  currencyService = inject(CurrencyService);
  healthService = inject(SystemHealthService);
  router = inject(Router);
  platformId = inject(PLATFORM_ID);
  isBrowser = isPlatformBrowser(this.platformId);

  headerHovered = signal(false);
  showLangMenu = signal(false);
  showCurrencyMenu = signal(false);
  showCompanyMenu = signal(false);
  isMobileMenuOpen = signal(false);
  isMobile = signal(false);
  showNotifPanel = signal(false);
  notifHub = inject(NotificationHubService);
  drawerService = inject(SideDrawerService);
  
  // ✅ Detect if we are in the Operative Plan Demo
  isDemoCompany = computed(() => {
    return this.authService.activeCompanyId() === 'd3d3d3d3-bbaa-46e6-a7f0-aeb4b92b6d38';
  });

  constructor() {
    this.checkMobile();
    this.notifHub.startPolling();
  }

  @HostListener('window:resize')
  checkMobile() {
    if (this.isBrowser) {
      this.isMobile.set(window.innerWidth < 1024);
      if (!this.isMobile()) {
        this.isMobileMenuOpen.set(false);
      }
    }
  }

  // Reactive Company Name using Signal
  activeCompanyName = computed(() => {
    const actId = this.authService.activeCompanyId();
    if (actId) {
      const match = this.authService.availableCompanies().find(c => c.company_id === actId);
      if (match) return match.company_name;
    }

    const session = this.authService.session();
    if (session) {
      return (session as any).company_name || this.translationService.translate('auth.select_module', 'Select Company');
    }
    
    if (this.isBrowser) {
       const stored = localStorage.getItem('_ic_auth_ctx');
       if (stored) {
         try {
           return JSON.parse(stored).company_name || this.translationService.translate('auth.select_module', 'Select Company');
         } catch {}
       }
    }
    return this.translationService.translate('auth.select_module', 'Select Company');
  });

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.relative')) {
      this.showLangMenu.set(false);
      this.showCurrencyMenu.set(false);
    }
    // Specific check for company menu which might be inside a different relative container
    if (!target.closest('.group\\/tenant') && !target.closest('.animate-in')) {
       this.showCompanyMenu.set(false);
    }
  }

  onHoverItem(item: MenuItem) {
    if (item.subItems) {
      this.navService.activeSubMenuId.set(item.id);
    }
  }

  onSelectItem(item: MenuItem) {
    if (item.route) {
      this.router.navigate([item.route]);
      this.navService.closeSubMenu();
    } else if (item.subItems) {
      this.navService.toggleSubMenu(item.id);
    }
  }

  onMouseLeavePanel() {
    this.navService.closeSubMenu();
  }

  getActiveMenuItem() {
    const activeId = this.navService.activeSubMenuId();
    return this.navService.menuItems().find((i: MenuItem) => i.id === activeId);
  }

  getActiveSubItems() {
    const activeId = this.navService.activeSubMenuId();
    const item = this.navService.menuItems().find((i: MenuItem) => i.id === activeId);
    return item?.subItems || null;
  }

  isRouteActive(route?: string) {
    if (!route) return false;
    return this.router.url.startsWith(route);
  }

  logout() {
    this.toastService.info(this.translationService.translate('auth.logging_out', 'Logging out...'), 'System');
    this.authService.logout();
  }

  switchCompany() {
    this.toastService.info(this.translationService.translate('auth.switching_context', 'Switching context...'), 'System');
    this.authService.authStep.set('handshake');
    this.router.navigate(['/select-company']);
  }

  async switchCompanyTo(companyId: string) {
    this.showCompanyMenu.set(false);
    this.toastService.info(this.translationService.translate('auth.switching_company', 'Switching company...'), 'System');
    try {
      // ✅ Stay on the same route after company switch
      const currentRoute = this.router.url;
      await this.authService.selectCompany(companyId, currentRoute);
      this.toastService.success(this.translationService.translate('common.environment_updated', 'Environment updated'), 'Success');
    } catch (err) {
      this.toastService.error(this.translationService.translate('common.error_changing_company', 'Error changing company'), 'Error');
    }
  }

  async setManualRate(rate: string) {
    const val = parseFloat(rate);
    if (!isNaN(val) && val > 0) {
      const success = await this.currencyService.manualUpdateRate(val);
      if (success) {
        this.toastService.success(`Tasa operativa fijada en $${val.toFixed(4)}`, 'Divisas');
      } else {
        this.toastService.error('Error al persistir la tasa en el servidor', 'Divisas');
      }
    } else {
      this.toastService.error('Ingresa una tasa válida mayor a 0', 'Divisas');
    }
  }
  
  handleNotificationClick(n: any) {
    this.notifHub.markAsRead(n.id);
    this.showNotifPanel.set(false);
    
    // Extract action_url from payload
    const actionUrl = n.payload?.action_url;
    if (actionUrl) {
      console.log(`[MainLayout] Navigating to notification link: ${actionUrl}`);
      this.router.navigateByUrl(actionUrl);
    }
  }

  openSupportDrawer() {
    this.drawerService.open(TicketsFormComponent, {
      title: 'SOPORTE TÉCNICO',
      subtitle: 'CENTRO DE AYUDA AI',
      icon: 'support_agent',
      width: 'w-[400px]'
    }, {
      context: 'support',
      isEdit: false
    });
  }
}
