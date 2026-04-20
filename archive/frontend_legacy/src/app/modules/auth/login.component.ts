import { Component, inject, signal, HostListener, OnDestroy, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { lastValueFrom } from 'rxjs';
import { Router } from '@angular/router';
import { AuthService } from '@services/auth.service';
import { ToastService } from '@services/toast.service';
import { TranslationService } from '@services/translation.service';
import { MatIconModule } from '@angular/material/icon';
import { Html5Qrcode } from 'html5-qrcode';
import { TenantSelectionComponent } from './tenant-selection.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, TenantSelectionComponent],
  template: `
    <div class="min-h-screen flex items-center justify-center bg-surface-bg p-4 relative overflow-hidden transition-colors duration-300 font-sans">
      <!-- Background Effects -->
      <div class="absolute top-0 left-0 w-full h-full opacity-30 pointer-events-none">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 blur-[120px] rounded-full animate-pulse-glow"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-ic-blue/10 blur-[120px] rounded-full animate-pulse-glow" style="animation-delay: 1s"></div>
      </div>

      <!-- Language Selector (Top Right) -->
      <div class="absolute top-6 right-6 z-50">
        <div class="relative">
          <button (click)="showLangMenu.set(!showLangMenu())"
                  class="text-surface-text-muted hover:text-primary transition-colors p-2 rounded-lg hover:bg-surface-text/5 flex items-center gap-1">
            <mat-icon class="text-lg">language</mat-icon>
            <span class="text-[9px] font-black uppercase tracking-tighter">
              {{ ts.currentLang() === 'en' ? 'US' : 'ES' }}
            </span>
          </button>

          @if (showLangMenu()) {
            <div class="absolute right-0 mt-2 w-36 bg-surface-card border border-surface-border rounded-xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-50 py-2 animate-fade-in-up origin-top-right">
              <button (click)="ts.setLanguage('es'); showLangMenu.set(false)"
                      class="w-full px-4 py-2.5 text-left text-[10px] font-bold uppercase tracking-widest hover:bg-primary/10 hover:text-primary transition-colors flex items-center justify-between group/lang"
                      [class.text-primary]="ts.currentLang() === 'es'">
                <span class="flex items-center gap-2">
                  <span class="w-1.5 h-1.5 rounded-full bg-surface-text-muted group-hover/lang:bg-primary transition-colors" 
                        [class.bg-primary]="ts.currentLang() === 'es'"></span>
                  Español
                </span>
                @if (ts.currentLang() === 'es') { <mat-icon class="text-sm">check</mat-icon> }
              </button>
              <button (click)="ts.setLanguage('en'); showLangMenu.set(false)"
                      class="w-full px-4 py-2.5 text-left text-[10px] font-bold uppercase tracking-widest hover:bg-primary/10 hover:text-primary transition-colors flex items-center justify-between group/lang"
                      [class.text-primary]="ts.currentLang() === 'en'">
                <span class="flex items-center gap-2">
                  <span class="w-1.5 h-1.5 rounded-full bg-surface-text-muted group-hover/lang:bg-primary transition-colors" 
                        [class.bg-primary]="ts.currentLang() === 'en'"></span>
                  English
                </span>
                @if (ts.currentLang() === 'en') { <mat-icon class="text-sm">check</mat-icon> }
              </button>
            </div>
          }
        </div>
      </div>

      <div class="max-w-md w-full animate-fade-in-up relative z-10">
        <!-- Logo Section (High-Fidelity SVG) -->
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-24 h-24 mb-4 drop-shadow-[0_0_20px_rgba(0,229,255,0.3)]">            <svg version="1.1" viewBox="0 0 630 630" class="w-full h-full text-primary overflow-visible transition-colors duration-300">
               <path fill="currentColor" d="M283.442566,467.396484 C262.120392,454.618988 241.163971,441.949097 220.106964,429.448669 C217.361130,427.818573 216.058136,426.174622 216.139130,422.819214 C216.379929,412.842804 216.225449,402.856842 216.225449,391.756836 C222.217041,395.304138 227.542450,398.403046 232.815720,401.588226 C257.871216,416.722260 282.948395,431.821198 307.919464,447.093445 C311.573212,449.328094 314.302826,449.486786 318.146393,447.152618 C353.730103,425.542633 389.440826,404.141174 425.195038,382.813904 C427.876617,381.214325 428.730133,379.505707 428.691589,376.506409 C428.524597,363.518463 428.598999,350.527435 428.586151,337.537506 C428.584564,335.927002 428.585968,334.316498 428.585968,332.396912 C438.836426,332.396912 448.441071,332.396912 458.523712,332.396912 C458.610016,333.981537 458.769440,335.570068 458.771973,337.158905 C458.801636,355.821960 458.725983,374.485779 458.897614,393.15 C458.927399,396.388306 457.952759,398.185547 455.136902,399.869202 C417.647003,422.284607 380.238403,444.835968 342.810883,467.355621 C334.399323,472.416779 325.916809,477.366089 317.620453,482.609650 C314.193390,484.775604 311.802094,485.204559 308.022400,482.503662 C300.315674,476.996521 291.900421,472.480896 283.442566,467.396484 z" />
               <path fill="currentColor" d="M235.082947,206.927277 C228.952850,210.641693 223.126678,214.158249 216.727325,218.020782 C216.524139,216.346359 216.258240,215.145996 216.251907,213.944244 C216.206238,205.280014 216.421875,196.607849 216.104980,187.954666 C215.970200,184.274109 217.271194,182.332092 220.342957,180.502716 C247.689163,164.216888 275.244720,148.247147 302.042664,131.096878 C310.486816,125.692780 316.027954,126.108505 324.255096,131.165054 C367.352722,157.653641 410.864594,183.469391 454.313843,209.382568 C457.737549,211.424484 458.994995,213.643417 458.939392,217.647873 C458.696472,235.140076 458.824310,252.637421 458.817810,270.132904 C458.817200,271.761902 458.817749,273.390900 458.817749,275.310699 C448.646667,275.310699 438.902893,275.310699 428.537384,275.310699 C428.537384,266.584900 428.525909,257.974396 428.541718,249.363983 C428.551178,244.200806 428.460663,239.031372 428.688995,233.876892 C428.829071,230.714569 427.883118,228.740555 425.011810,227.029099 C388.901855,205.505783 352.871704,183.848557 316.828644,162.213028 C314.669861,160.917175 312.924957,159.900711 310.120148,161.612503 C285.282288,176.771469 260.315552,191.719269 235.082947,206.927277 z" />
               <path fill="currentColor" d="M167.237305,339.999878 C167.231201,317.851624 167.280746,296.203033 167.153702,274.555511 C167.136078,271.554321 167.920334,269.757721 170.640457,268.201569 C179.381302,263.200989 187.936111,257.875275 197.124573,252.336243 C197.124573,306.893494 197.124573,360.744293 197.124573,415.345459 C187.396072,409.520905 178.017197,404.040222 168.842422,398.236908 C167.735657,397.536835 167.295074,395.094055 167.285614,393.454681 C167.183884,375.803589 167.230759,358.151611 167.237305,339.999878 z" />
               <path fill="currentColor" d="M197.510864,222.768204 C198.422928,228.129318 196.353119,231.068268 191.985764,233.426636 C185.028687,237.183426 178.436737,241.614136 171.662277,245.713440 C170.443161,246.451126 169.088699,246.965179 167.188995,247.872879 C167.188995,236.271759 167.036346,225.319336 167.357971,214.380859 C167.404770,212.788727 169.422058,210.785721 171.032471,209.786926 C179.466415,204.555984 188.063080,199.587387 197.508453,193.991287 C197.508453,203.847900 197.508453,213.075729 197.510864,222.768204 z" />
            </svg>
          </div>
          <h1 class="text-3xl font-black text-surface-text tracking-tighter uppercase italic glow-text">InternoCore</h1>
          <p class="text-surface-text-muted font-mono text-[10px] tracking-widest uppercase mt-1">Industrial Operations OS</p>
        </div>

        <!-- Glassmorphism Container -->
        <div 
          class="glass-card p-8 rounded-3xl border border-white/10 transition-all duration-500 shadow-[0_0_50px_rgba(0,0,0,0.5)]"
          [class.animate-shake]="error()"
        >
          @if (auth.authStep() === 'handshake') {
            <div class="animate-fade-in">
              <app-tenant-selection (logout)="onCancelHandshake()"></app-tenant-selection>
            </div>
          } @else if (view() === 'login') {
            <!-- Tab Switcher -->
            <div class="flex items-center justify-center gap-4 mb-8">
              <button 
                (click)="mode.set('admin')"
                class="flex-1 py-2 text-[10px] font-black uppercase tracking-widest transition-all border-b-2"
                [class.text-primary]="mode() === 'admin'"
                [class.border-primary]="mode() === 'admin'"
                [class.text-surface-text-muted]="mode() !== 'admin'"
                [class.border-transparent]="mode() !== 'admin'"
              >
                Office / Admin
              </button>
              <button 
                (click)="mode.set('operator')"
                class="flex-1 py-2 text-[10px] font-black uppercase tracking-widest transition-all border-b-2"
                [class.text-primary]="mode() === 'operator'"
                [class.border-primary]="mode() === 'operator'"
                [class.text-surface-text-muted]="mode() !== 'operator'"
                [class.border-transparent]="mode() !== 'operator'"
              >
                Shop Floor
              </button>
            </div>

            <form (submit)="onLogin($event)" class="space-y-6">
              @if (mode() === 'admin') {
                <div class="space-y-4 animate-fade-in">
                  <div class="space-y-1">
                    <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Email</label>
                    <div class="relative group">
                      <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">alternate_email</mat-icon>
                      <input 
                        type="email" 
                        [(ngModel)]="credentials.email" 
                        name="email"
                        class="w-full bg-surface-bg border border-white/5 rounded-xl py-4 pl-12 pr-4 text-sm focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all placeholder:text-white/10"
                        placeholder="nombre@empresa.com"
                        required
                      >
                    </div>
                  </div>

                  <div class="space-y-1">
                    <label class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted ml-1">Password</label>
                    <div class="relative group">
                      <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">lock</mat-icon>
                      <input 
                        [type]="showPassword() ? 'text' : 'password'" 
                        [(ngModel)]="credentials.password" 
                        name="password"
                        class="w-full bg-surface-bg border border-white/5 rounded-xl py-4 pl-12 pr-12 text-sm focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all placeholder:text-white/10"
                        placeholder="••••••••"
                        required
                      >
                      <button 
                        type="button"
                        (click)="showPassword.set(!showPassword())"
                        class="absolute right-4 top-1/2 -translate-y-1/2 text-surface-text-muted hover:text-primary transition-colors"
                      >
                        <mat-icon class="text-xl">{{ showPassword() ? 'visibility_off' : 'visibility' }}</mat-icon>
                      </button>
                    </div>
                  </div>
                </div>
              } @else {
                <div class="space-y-4 animate-fade-in">
                  <div 
                    class="relative aspect-square max-w-[280px] mx-auto bg-black/40 rounded-2xl border-2 border-dashed border-white/10 flex flex-col items-center justify-center group cursor-pointer overflow-hidden shadow-inner"
                    (click)="startScanner()"
                  >
                    @if (showScanner()) {
                      <div id="reader" class="w-full h-full overflow-hidden rounded-2xl"></div>
                      <div class="absolute inset-0 border-[20px] border-black/40 pointer-events-none"></div>
                      <div class="absolute top-0 left-0 w-full h-1 bg-primary/40 animate-scan-line shadow-[0_0_15px_rgba(0,229,255,0.8)]"></div>
                      <button 
                        (click)="stopScanner(); $event.stopPropagation()"
                        class="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 bg-red-500/80 hover:bg-red-500 rounded-lg text-[9px] font-black uppercase tracking-widest text-white transition-all z-20"
                      >
                        Cancelar
                      </button>
                    } @else {
                      <div class="text-center p-6 transition-transform group-hover:scale-105 duration-500">
                        <div class="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-primary/20 shadow-[0_0_30px_rgba(0,229,255,0.1)]">
                          <mat-icon class="text-4xl text-primary animate-pulse">qr_code_scanner</mat-icon>
                        </div>
                        <h3 class="text-xs font-black text-white uppercase tracking-widest mb-1 italic">Scan ID Card</h3>
                        <p class="text-[10px] text-surface-text-muted max-w-[180px] leading-relaxed">Presente su código QR ante la cámara para acceso instantáneo</p>
                      </div>
                      
                      <!-- Corner Accents -->
                      <div class="absolute top-4 left-4 w-6 h-6 border-t-2 border-l-2 border-primary/30"></div>
                      <div class="absolute top-4 right-4 w-6 h-6 border-t-2 border-r-2 border-primary/30"></div>
                      <div class="absolute bottom-4 left-4 w-6 h-6 border-b-2 border-l-2 border-primary/30"></div>
                      <div class="absolute bottom-4 right-4 w-6 h-6 border-b-2 border-r-2 border-primary/30"></div>
                    }
                  </div>
                  
                  <div class="relative">
                    <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-white/5"></div></div>
                    <div class="relative flex justify-center text-[9px] uppercase font-black"><span class="bg-[#050B14] px-4 text-surface-text-muted tracking-[0.3em]">O ingrese manual</span></div>
                  </div>

                  <div class="relative group">
                    <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">badge</mat-icon>
                    <input 
                      type="text" 
                      [(ngModel)]="operatorId" 
                      name="operatorId"
                      class="w-full bg-surface-bg border border-white/5 rounded-xl py-4 pl-12 pr-4 text-sm focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all placeholder:text-white/10"
                      placeholder="ID DE OPERADOR"
                    >
                  </div>
                </div>
              }

              <button 
                type="submit" 
                class="w-full group relative overflow-hidden bg-primary hover:bg-primary-dark text-ic-dark py-4 rounded-xl font-black uppercase tracking-[0.2em] text-xs transition-all shadow-[0_10px_30px_rgba(0,132,199,0.3)] hover:-translate-y-1 active:translate-y-0 disabled:opacity-50 disabled:translate-y-0 flex items-center justify-center gap-2"
                [disabled]="isLoading()"
              >
                @if (isLoading()) {
                  <div class="w-5 h-5 border-2 border-ic-dark/30 border-t-ic-dark rounded-full animate-spin"></div>
                  <span>Procesando...</span>
                } @else {
                  <mat-icon class="text-lg group-hover:translate-x-1 transition-transform">bolt</mat-icon>
                  <span>{{ mode() === 'admin' ? 'Iniciar Misión' : 'Acceder a Celda' }}</span>
                }
              </button>
            </form>

            @if (mode() === 'admin') {
              <div class="mt-8 text-center">
                <a href="#" class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted hover:text-primary transition-colors underline-offset-4 hover:underline decoration-primary/30">
                  ¿Problemas con el acceso? Contactar QA
                </a>
              </div>
            }
          }
        </div>
      </div>

      <!-- System Status Footer -->
      <div class="absolute bottom-6 left-0 w-full px-8 flex justify-between items-center z-10 pointer-events-none">
        <div class="flex items-center gap-4">
          <div class="flex flex-col">
            <span class="text-[8px] font-black uppercase tracking-[0.2em] text-surface-text-muted">Kernel Status</span>
            <div class="flex items-center gap-2">
              <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] animate-pulse"></div>
              <span class="text-[10px] font-bold text-emerald-500 uppercase">Synchronized</span>
            </div>
          </div>
        </div>
        <div class="text-right">
          <span class="text-[8px] font-black uppercase tracking-[0.2em] text-surface-text-muted block">Build Alpha 2.4.1</span>
          <span class="text-[10px] font-mono text-surface-text-muted">© 2026 NEXOSUITE INDUSTRIAL</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .animate-pulse-glow {
      animation: pulse-glow 4s ease-in-out infinite;
    }
    @keyframes pulse-glow {
      0%, 100% { opacity: 0.3; transform: scale(1); }
      50% { opacity: 0.6; transform: scale(1.2); }
    }
    .animate-shake {
      animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
    }
    @keyframes shake {
      10%, 90% { transform: translate3d(-1px, 0, 0); }
      20%, 80% { transform: translate3d(2px, 0, 0); }
      30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
      40%, 60% { transform: translate3d(4px, 0, 0); }
    }
    .animate-scan-line {
      animation: scan-line 2s linear infinite;
    }
    @keyframes scan-line {
      0% { top: 0; }
      100% { top: 100%; }
    }
    .glow-text {
      text-shadow: 0 0 20px rgba(255,255,255,0.1);
    }
    #reader video {
      object-fit: cover !important;
      border-radius: 1rem;
    }
  `]
})
export class LoginComponent implements OnDestroy {
  auth = inject(AuthService);
  router = inject(Router);
  toast = inject(ToastService);
  ts = inject(TranslationService);

  view = signal<'login' | 'select-company'>('login');
  mode = signal<'admin' | 'operator'>('admin');
  isLoading = signal(false);
  error = signal(false);
  showPassword = signal(false);
  showLangMenu = signal(false);
  operatorId = '';

  credentials = {
    email: '',
    password: ''
  };

  private scanner: Html5Qrcode | null = null;
  showScanner = signal(false);

  constructor() {
    effect(() => {
      if (this.auth.isAuthenticated() && !this.auth.activeCompanyId()) {
        this.router.navigate(['/select-company']);
      } else if (this.auth.isAuthenticated() && this.auth.activeCompanyId()) {
        this.router.navigate(['/dashboard']);
      }
    });
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.relative')) {
      this.showLangMenu.set(false);
    }
  }

  async onLogin(event?: Event) {
    if (event) event.preventDefault();
    
    if (this.mode() === 'admin' && (!this.credentials.email || !this.credentials.password)) {
      this.toast.error('Complete todos los campos', 'Error');
      return;
    }

    if (this.mode() === 'operator' && !this.operatorId) {
      this.toast.error('Ingrese su ID de operador', 'Error');
      return;
    }

    this.isLoading.set(true);
    this.error.set(false);

    try {
      if (this.mode() === 'admin') {
        await lastValueFrom(this.auth.login({ email: this.credentials.email, password: this.credentials.password }));
      } else {
        await lastValueFrom(this.auth.login({ email: this.operatorId, password: 'operator-pass' }));
      }
      this.toast.success('Acceso concedido');
    } catch (err) {
      this.error.set(true);
      this.toast.error('Credenciales inválidas');
      setTimeout(() => this.error.set(false), 1000);
    } finally {
      this.isLoading.set(false);
    }
  }

  async startScanner() {
    this.showScanner.set(true);
    try {
      setTimeout(async () => {
        this.scanner = new Html5Qrcode("reader");
        await this.scanner.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: { width: 250, height: 250 } },
          (decodedText) => {
            this.operatorId = decodedText;
            this.stopScanner();
            this.onLogin();
          },
          undefined
        );
      }, 100);
    } catch (err) {
      this.toast.error('No se pudo acceder a la cámara', 'Hardware Error');
      this.showScanner.set(false);
    }
  }

  stopScanner() {
    if (this.scanner) {
      this.scanner.stop().then(() => {
        this.scanner = null;
        this.showScanner.set(false);
      });
    } else {
      this.showScanner.set(false);
    }
  }

  onCancelHandshake() {
    this.auth.logout();
    this.view.set('login');
  }

  ngOnDestroy() {
    this.stopScanner();
  }
}