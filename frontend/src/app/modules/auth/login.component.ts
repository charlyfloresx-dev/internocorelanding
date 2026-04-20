import {Component, inject, signal, HostListener, OnDestroy} from '@angular/core';
import {TranslationService} from '../../core/services/translation.service';
import {TranslatePipe} from '../../shared/pipes/translate.pipe';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {Router} from '@angular/router';
import {AuthService} from '../../core/services/auth.service';
import {ToastService} from '../../core/services/toast.service';
import {MatIconModule} from '@angular/material/icon';
import {Html5Qrcode} from 'html5-qrcode';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, TranslatePipe],
  template: `
    <div class="min-h-screen flex items-center justify-center bg-surface-bg p-4 relative overflow-hidden transition-colors duration-300">
      <!-- Background Effects -->
      <div class="absolute top-0 left-0 w-full h-full opacity-30 pointer-events-none">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 blur-[120px] rounded-full animate-pulse-glow"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-ic-blue/10 blur-[120px] rounded-full animate-pulse-glow" style="animation-delay: 1s"></div>
      </div>

      <div class="max-w-md w-full animate-fade-in-up relative z-10">
        <!-- Logo Section (Restored) -->
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-24 h-24 mb-4 drop-shadow-[0_0_20px_rgba(0,229,255,0.3)]">
            <svg version="1.1" viewBox="0 0 630 630" class="w-full h-full text-primary overflow-visible transition-colors duration-300">
              <path fill="currentColor" d="M338.272552,413.107239 C330.839233,417.587891 323.635864,421.750458 316.649078,426.249237 C314.147339,427.860046 312.337738,427.765350 309.887360,426.264191 C295.698029,417.571625 281.434052,409.000305 267.160767,400.445618 C251.387711,390.992035 235.610611,381.544006 219.750412,372.238220 C217.142288,370.707947 216.119690,369.030518 216.127686,365.948029 C216.232727,325.462097 216.233948,284.975708 216.122742,244.489822 C216.113312,241.053635 217.221832,239.234848 220.231827,237.466171 C239.426285,226.187683 258.471649,214.655045 277.546661,203.173767 C288.055878,196.848251 298.572174,190.532074 308.986481,184.052917 C311.865021,182.262070 314.044312,182.169617 317.112610,184.033737 C347.010559,202.198257 377.041809,220.143265 406.979431,238.242828 C408.214264,238.989395 409.692230,240.630295 409.716217,241.880264 C409.929535,252.985809 409.840302,264.097137 409.840302,275.417236 C399.728363,275.417236 390.114716,275.417236 379.629395,275.417236 C379.629395,270.605988 379.466278,265.855347 379.690308,261.123047 C379.825562,258.265961 378.890594,256.633087 376.361328,255.174744 C359.512085,245.459778 342.747772,235.596924 325.998749,225.709518 C323.027374,223.955460 320.035461,222.115005 317.450348,219.859161 C314.357361,217.160156 311.853790,217.796646 308.676056,219.740143 C288.991638,231.779083 269.163849,243.584183 249.523483,255.693604 C247.929001,256.676697 246.492538,259.351105 246.479782,261.249664 C246.282745,290.570831 246.283813,319.893951 246.455124,349.215363 C246.465103,350.921570 247.898575,353.308319 249.380890,354.213226 C269.63,366.574463 289.97,378.78 310.41,390.83 C311.85,391.68 314.64,391.75 316.06,390.91 C336.23,378.99 356.26,366.81 376.4,354.83 C378.9,353.34 379.79,351.7 379.66,348.84 C379.43,343.56 379.6,338.25 379.6,332.51 L409.86,332.51 C409.86,341.67 409.28,351 410.04,360.2 C410.67,367.71 408.02,371.65 401.52,375.36 C380.3,387.46 359.53,400.34 338.27,413.11 Z" />
              <path fill="currentColor" opacity="0.8" d="M283.442566,467.396484 C262.120392,454.618988 241.163971,441.949097 220.106964,429.448669 C217.361130,427.818573 216.058136,426.174622 216.139130,422.819214 C216.379929,412.842804 216.225449,402.856842 216.225449,391.756836 C222.217041,395.304138 227.542450,398.403046 232.815720,401.588226 C257.871216,416.722260 282.948395,431.821198 307.919464,447.093445 C311.573212,449.328094 314.302826,449.486786 318.146393,447.152618 C353.730103,425.542633 389.440826,404.141174 425.195038,382.813904 C427.876617,381.214325 428.730133,379.505707 428.691589,376.506409 C428.524597,363.518463 428.598999,350.527435 428.586151,337.537506 C428.584564,335.927002 428.585968,334.316498 428.585968,332.396912 C438.836426,332.396912 448.441071,332.396912 458.523712,332.396912 C458.610016,333.981537 458.769440,335.570068 458.771973,337.158905 C458.801636,355.821960 458.725983,374.485779 458.897614,393.15 C458.927399,396.388306 457.952759,398.185547 455.136902,399.869202 C417.647003,422.284607 380.238403,444.835968 342.810883,467.355621 C334.399323,472.416779 325.916809,477.366089 317.620453,482.609650 C314.193390,484.775604 311.802094,485.204559 308.022400,482.503662 C300.315674,476.996521 291.900421,472.480896 283.442566,467.396484 z" />
              <path fill="currentColor" opacity="0.6" d="M235.082947,206.927277 C228.952850,210.641693 223.126678,214.158249 216.727325,218.020782 C216.524139,216.346359 216.258240,215.145996 216.251907,213.944244 C216.206238,205.280014 216.421875,196.607849 216.104980,187.954666 C215.970200,184.274109 217.271194,182.332092 220.342957,180.502716 C247.689163,164.216888 275.244720,148.247147 302.042664,131.096878 C310.486816,125.692780 316.027954,126.108505 324.255096,131.165054 C367.352722,157.653641 410.864594,183.469391 454.313843,209.382568 C457.737549,211.424484 458.994995,213.643417 458.939392,217.647873 C458.696472,235.140076 458.824310,252.637421 458.817810,270.132904 C458.817200,271.761902 458.817749,273.390900 458.817749,275.310699 C448.646667,275.310699 438.902893,275.310699 428.537384,275.310699 C428.537384,266.584900 428.525909,257.974396 428.541718,249.363983 C428.551178,244.200806 428.460663,239.031372 428.688995,233.876892 C428.829071,230.714569 427.883118,228.740555 425.011810,227.029099 C388.901855,205.505783 352.871704,183.848557 316.828644,162.213028 C314.669861,160.917175 312.924957,159.900711 310.120148,161.612503 C285.282288,176.771469 260.315552,191.719269 235.082947,206.927277 z" />
              <path fill="currentColor" opacity="0.4" d="M167.237305,339.999878 C167.231201,317.851624 167.280746,296.203033 167.153702,274.555511 C167.136078,271.554321 167.920334,269.757721 170.640457,268.201569 C179.381302,263.200989 187.936111,257.875275 197.124573,252.336243 C197.124573,306.893494 197.124573,360.744293 197.124573,415.345459 C187.396072,409.520905 178.017197,404.040222 168.842422,398.236908 C167.735657,397.536835 167.295074,395.094055 167.285614,393.454681 C167.183884,375.803589 167.230759,358.151611 167.237305,339.999878 z" />
              <path fill="currentColor" opacity="0.2" d="M197.510864,222.768204 C198.422928,228.129318 196.353119,231.068268 191.985764,233.426636 C185.028687,237.183426 178.436737,241.614136 171.662277,245.713440 C170.443161,246.451126 169.088699,246.965179 167.188995,247.872879 C167.188995,236.271759 167.036346,225.319336 167.357971,214.380859 C167.404770,212.788727 169.422058,210.785721 171.032471,209.786926 C179.466415,204.555984 188.063080,199.587387 197.508453,193.991287 C197.508453,203.847900 197.508453,213.075729 197.510864,222.768204 z" />
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
          @if (view() === 'login') {
            <!-- Subtle Tab Switcher -->
            <div class="flex items-center justify-center gap-4 mb-8">
              <button 
                (click)="mode.set('admin')"
                class="flex-1 py-2 text-[10px] font-black uppercase tracking-widest transition-all border-b-2"
                [class.text-primary]="mode() === 'admin'"
                [class.border-primary]="mode() === 'admin'"
                [class.text-surface-text-muted]="mode() !== 'admin'"
                [class.border-transparent]="mode() !== 'admin'"
              >
                {{ 'auth.login.office_admin' | translate:'Office / Admin' }}
              </button>
              <button 
                (click)="mode.set('plant')"
                class="flex-1 py-2 text-[10px] font-black uppercase tracking-widest transition-all border-b-2"
                [class.text-primary]="mode() === 'plant'"
                [class.border-primary]="mode() === 'plant'"
                [class.text-surface-text-muted]="mode() !== 'plant'"
                [class.border-transparent]="mode() !== 'plant'"
              >
                {{ 'auth.login.plant_floor' | translate:'Plant Floor' }}
              </button>
            </div>

            @if (mode() === 'admin') {
              <!-- Admin Form -->
              <form (submit)="onSubmit($event)" class="space-y-6 animate-fade-in">
                <div class="space-y-4">
                  <div class="relative group">
                    <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors text-lg">email</mat-icon>
                    <input 
                      id="email"
                      type="email" 
                      [(ngModel)]="email" 
                      name="email"
                      class="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-4 text-sm text-surface-text outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all placeholder:text-surface-text-muted/50" 
                      [placeholder]="'auth.login.email_placeholder' | translate:'Email Address'"
                    >
                  </div>
                  
                  <div class="relative group">
                    <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors text-lg">lock</mat-icon>
                    <input 
                      id="password"
                      [type]="showPassword() ? 'text' : 'password'" 
                      [(ngModel)]="password" 
                      name="password"
                      class="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-12 py-4 text-sm text-surface-text outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all placeholder:text-surface-text-muted/50" 
                      [placeholder]="'auth.login.password_placeholder' | translate:'Password'"
                    >
                    <button 
                      type="button"
                      (click)="showPassword.set(!showPassword())"
                      class="absolute right-4 top-1/2 -translate-y-1/2 text-surface-text-muted hover:text-primary transition-colors"
                    >
                      <mat-icon class="text-lg">{{ showPassword() ? 'visibility_off' : 'visibility' }}</mat-icon>
                    </button>
                  </div>
                </div>

                <div class="flex justify-end">
                  <button type="button" (click)="view.set('forgot')" class="text-[10px] font-bold text-primary uppercase tracking-widest hover:underline">
                    {{ 'auth.login.forgot_password' | translate:'Forgot Password?' }}
                  </button>
                </div>

                @if (error()) {
                  <div class="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 animate-fade-in">
                    <mat-icon class="text-sm h-4 w-4">error_outline</mat-icon>
                    {{ error() }}
                  </div>
                }

                <button 
                  type="submit" 
                  class="w-full bg-primary text-ic-dark py-4 rounded-xl font-black text-xs uppercase tracking-[0.2em] transition-all active:scale-95 flex items-center justify-center gap-3 shadow-[0_0_20px_rgba(0,229,255,0.2)] hover:shadow-primary/40 disabled:opacity-50"
                  [disabled]="loading()"
                >
                  @if (loading()) {
                    <mat-icon class="animate-gear-spin">settings</mat-icon>
                    <span>{{ 'auth.login.verifying' | translate:'Verifying...' }}</span>
                  } @else if (success()) {
                    <mat-icon class="text-emerald-900">check_circle</mat-icon>
                    <span>{{ 'auth.login.success' | translate:'Success' }}</span>
                  } @else {
                    <span>{{ 'auth.login.sign_in' | translate:'Sign In' }}</span>
                    <mat-icon>arrow_forward</mat-icon>
                  }
                </button>

                <!-- Social Login -->
                <div class="pt-4 border-t border-white/10">
                  <p class="text-center text-[9px] text-surface-text-muted font-bold uppercase tracking-widest mb-4">{{ 'auth.login.or_sign_in_with' | translate:'Or sign in with' }}</p>
                  <div class="grid grid-cols-2 gap-4">
                    <button type="button" class="flex items-center justify-center gap-2 py-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all">
                      <svg class="w-4 h-4" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                      </svg>
                      <span class="text-[10px] font-bold text-surface-text uppercase tracking-widest">Google</span>
                    </button>
                    <button type="button" class="flex items-center justify-center gap-2 py-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all">
                      <svg class="w-4 h-4" viewBox="0 0 23 23">
                        <path fill="#f3f3f3" d="M0 0h11v11H0zM12 0h11v11H12zM0 12h11v11H0zM12 12h11v11H12z"/>
                      </svg>
                      <span class="text-[10px] font-bold text-surface-text uppercase tracking-widest">Microsoft</span>
                    </button>
                  </div>
                </div>

                <!-- Action Links -->
                <div class="pt-6 grid grid-cols-1 gap-3">
                  <button 
                    type="button" 
                    (click)="onJoinWithCode()"
                    class="w-full py-3 bg-primary/10 border border-primary/20 rounded-xl text-primary text-[10px] font-black uppercase tracking-widest hover:bg-primary/20 transition-all flex items-center justify-center gap-2"
                  >
                    <mat-icon class="text-sm">qr_code_2</mat-icon>
                    {{ 'auth.login.join_with_code' | translate:'Join with Code #' }}
                  </button>
                  <button 
                    type="button" 
                    (click)="onCreateCompany()"
                    class="w-full py-3 bg-white/5 border border-white/10 rounded-xl text-surface-text-muted text-[10px] font-black uppercase tracking-widest hover:text-primary hover:border-primary/30 transition-all flex items-center justify-center gap-2"
                  >
                    <mat-icon class="text-sm">add_business</mat-icon>
                    {{ 'auth.login.create_company' | translate:'Create New Company' }}
                  </button>
                </div>
              </form>
            } @else {
              <!-- Plant Floor / RFID & QR Mode -->
              <div class="flex flex-col items-center justify-center py-6 space-y-6 animate-fade-in">
                <div class="relative w-full max-w-[280px]">
                  <!-- Scanner Viewport -->
                  <div 
                    id="reader" 
                    class="w-full aspect-square rounded-[2rem] bg-ic-dark/40 border-2 border-primary/30 overflow-hidden relative flex items-center justify-center"
                    [class.border-primary]="scannerActive()"
                  >
                    @if (!scannerActive()) {
                      <div class="flex flex-col items-center gap-4 animate-pulse-hexagon">
                        <mat-icon class="text-primary text-6xl">qr_code_scanner</mat-icon>
                        <div class="absolute -inset-4 border border-primary/20 rounded-[2.5rem] animate-ping opacity-20"></div>
                      </div>
                    }
                  </div>
                  
                  <!-- Scanner Overlay -->
                  @if (scannerActive()) {
                    <div class="absolute inset-0 pointer-events-none border-2 border-primary rounded-[2rem] overflow-hidden">
                      <div class="absolute top-0 left-0 w-full h-0.5 bg-primary shadow-[0_0_15px_rgba(0,229,255,0.8)] animate-scan-line"></div>
                    </div>
                  }
                </div>

                <div class="text-center space-y-2">
                  <h3 class="text-lg font-black text-surface-text uppercase tracking-tighter italic">
                    {{ (scannerActive() ? 'auth.login.scanning' : 'auth.login.waiting_badge') | translate:(scannerActive() ? 'Scanning...' : 'Waiting for Badge/QR...') }}
                  </h3>
                  <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest px-4">
                    {{ (scannerActive() ? 'auth.login.position_qr' : 'auth.login.place_rfid') | translate:(scannerActive() ? 'Position QR...' : 'Place RFID card...') }}
                  </p>
                </div>

                <div class="flex flex-col gap-3 w-full">
                  <button 
                    (click)="toggleCamera()"
                    class="w-full py-3 bg-primary/10 border border-primary/30 rounded-xl text-primary text-[10px] font-black uppercase tracking-widest hover:bg-primary/20 transition-all flex items-center justify-center gap-2"
                  >
                    <mat-icon class="text-sm">{{ scannerActive() ? 'videocam_off' : 'videocam' }}</mat-icon>
                    {{ (scannerActive() ? 'auth.login.stop_camera' : 'auth.login.use_camera') | translate:(scannerActive() ? 'Stop Camera' : 'Use Camera Scanner') }}
                  </button>

                  <button 
                    (click)="mode.set('admin')"
                    class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest hover:text-primary transition-all text-center py-2"
                  >
                    {{ 'auth.login.manual_login' | translate:'Manual Login' }}
                  </button>
                </div>
              </div>
            }
          } @else if (view() === 'pin') {
            <!-- PIN Pad View (Industrial Mode) -->
            <div class="space-y-6 animate-fade-in text-center">
              <div class="mb-2">
                <mat-icon class="text-primary text-4xl mb-2">lock_person</mat-icon>
                <h3 class="text-xl font-black text-surface-text uppercase tracking-tighter italic">
                  {{ 'auth.pin.title' | translate:'Security PIN Required' }}
                </h3>
                <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest">
                  {{ 'auth.pin.subtitle' | translate:'Confirm Identity for' }}: <span class="text-primary">{{ pendingId() }}</span>
                </p>
              </div>

              <!-- PIN Dots -->
              <div class="flex justify-center gap-4 py-8">
                @for (i of [1,2,3,4]; track i) {
                  <div 
                    class="w-4 h-4 rounded-full border-2 transition-all duration-300"
                    [class.bg-primary]="tempPin().length >= i"
                    [class.border-primary]="tempPin().length >= i"
                    [class.border-white/20]="tempPin().length < i"
                    [class.shadow-[0_0_15px_rgba(0,229,255,0.5)]]="tempPin().length >= i"
                  ></div>
                }
              </div>

              <!-- Numeric Keypad -->
              <div class="grid grid-cols-3 gap-3 max-w-[280px] mx-auto">
                @for (num of [1,2,3,4,5,6,7,8,9]; track num) {
                  <button 
                    (click)="onPinKey(num.toString())"
                    class="h-16 rounded-2xl bg-white/5 border border-white/10 text-xl font-black text-surface-text hover:bg-primary/20 hover:border-primary/50 transition-all active:scale-90"
                  >
                    {{ num }}
                  </button>
                }
                <button (click)="onPinKey('clear')" class="h-16 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-500 font-bold text-[10px] uppercase tracking-widest hover:bg-red-500/20 transition-all">
                  {{ 'auth.pin.clear' | translate:'DEL' }}
                </button>
                <button (click)="onPinKey('0')" class="h-16 rounded-2xl bg-white/5 border border-white/10 text-xl font-black text-surface-text hover:bg-primary/20 hover:border-primary/50 transition-all active:scale-90">0</button>
                <button (click)="view.set('login')" class="h-16 rounded-2xl bg-white/5 border border-white/10 text-surface-text-muted font-bold text-[10px] uppercase tracking-widest hover:text-primary transition-all">
                  {{ 'auth.pin.cancel' | translate:'ESC' }}
                </button>
              </div>

              @if (error()) {
                <div class="text-red-400 text-[10px] font-bold uppercase tracking-widest animate-shake">
                  {{ error() }}
                </div>
              }
            </div>
          } @else if (view() === 'forgot') {
            <!-- Forgot Password View -->
            <div class="space-y-6 animate-fade-in">
              <div class="text-center">
                <h3 class="text-lg font-black text-surface-text uppercase tracking-tighter italic">{{ 'auth.forgot.title' | translate:'Recover Password' }}</h3>
                <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">{{ 'auth.forgot.subtitle' | translate:'Enter your email to receive instructions' }}</p>
              </div>

              <div class="relative group">
                <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors text-lg">email</mat-icon>
                <input 
                  type="email" 
                  class="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-4 text-sm text-surface-text outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all" 
                  [placeholder]="'auth.login.email_placeholder' | translate:'Email Address'"
                >
              </div>

              <button 
                class="w-full bg-primary text-ic-dark py-4 rounded-xl font-black text-xs uppercase tracking-[0.2em] transition-all active:scale-95"
                (click)="view.set('login')"
              >
                {{ 'auth.forgot.send_instructions' | translate:'Send Instructions' }}
              </button>

              <button 
                (click)="view.set('login')"
                class="w-full text-[10px] font-black text-surface-text-muted uppercase tracking-widest hover:text-primary transition-all"
              >
                {{ 'auth.forgot.back_to_login' | translate:'Back to Login' }}
              </button>
            </div>
          }
        </div>
        
        <!-- Bottom Links -->
        <div class="mt-8 flex flex-col items-center gap-4">
          <p class="text-surface-text-muted text-[9px] font-mono uppercase tracking-widest">
            &copy; 2026 Interno Core. Industrial SaaS Multitenant v2.1.0
          </p>
        </div>
      </div>
    </div>
  `
})
export class LoginComponent implements OnDestroy {
  private authService = inject(AuthService);
  protected translationService = inject(TranslationService);
  private toastService = inject(ToastService);
  private router = inject(Router);
  
  view = signal<'login' | 'forgot' | 'pin'>('login');
  mode = signal<'admin' | 'plant'>('admin');
  showPassword = signal(false);
  email = '';
  password = '';
  loading = signal(false);
  success = signal(false);
  error = signal<string | null>(null);

  // PIN Flow State
  pendingId = signal('');
  tempPin = signal('');

  // Scanner State
  scannerActive = signal(false);
  private html5QrCode: Html5Qrcode | null = null;
  private scanBuffer = '';
  private lastKeyTime = 0;

  @HostListener('document:keydown', ['$event'])
  handleKeyboardScanner(event: KeyboardEvent) {
    if (this.mode() !== 'plant') return;

    const currentTime = Date.now();
    
    // Hardware scanners typically send keys very fast (< 50ms apart)
    if (currentTime - this.lastKeyTime > 100) {
      this.scanBuffer = '';
    }

    if (event.key === 'Enter') {
      if (this.scanBuffer.length > 2) {
        this.processScan(this.scanBuffer);
        this.scanBuffer = '';
      }
    } else if (event.key.length === 1) {
      this.scanBuffer += event.key;
    }

    this.lastKeyTime = currentTime;
  }

  ngOnDestroy() {
    this.stopCamera();
  }

  async toggleCamera() {
    if (this.scannerActive()) {
      await this.stopCamera();
    } else {
      await this.startCamera();
    }
  }

  private async startCamera() {
    try {
      this.html5QrCode = new Html5Qrcode('reader');
      this.scannerActive.set(true);
      this.toastService.info(this.translationService.translate('auth.login.starting_scanner', 'Starting scanner...'), 'System');
      
      await this.html5QrCode.start(
        { facingMode: 'environment' },
        {
          fps: 10,
          qrbox: { width: 250, height: 250 }
        },
        (decodedText) => {
          this.processScan(decodedText);
          this.stopCamera();
        },
        (errorMessage) => {
          // Optional: handle scan errors silently or log them
          if (errorMessage.includes('NotFound')) return;
          console.debug('Scan error:', errorMessage);
        }
      );
    } catch (err) {
      console.error('Camera start failed:', err);
      this.scannerActive.set(false);
      this.error.set(this.translationService.translate('auth.login.camera_error', 'Could not access camera'));
      this.toastService.error(this.translationService.translate('auth.login.camera_access_error', 'Camera access error'), 'Hardware');
    }
  }

  private async stopCamera() {
    if (this.html5QrCode) {
      try {
        if (this.html5QrCode.isScanning) {
          await this.html5QrCode.stop();
        }
        this.html5QrCode.clear();
      } catch (err) {
        console.error('Camera stop failed:', err);
      }
      this.html5QrCode = null;
    }
    this.scannerActive.set(false);
  }

  /**
   * Fired immediately on Enter key, or triggered by the camera QR decoder.
   * The debounce timer in handleKeyboardScanner acts as a "dirty read" cleaner,
   * not as the primary trigger — Enter fires this immediately for zero-latency UX.
   */
  private processScan(data: string) {
    if (!data || data.trim().length < 3) return;
    const rfid = data.trim();

    // Industrial Intelligence: Differentiate Internal ID vs physical RFID Tag
    // Internal IDs are alphanumeric and short (e.g., 003709A), RFID tags are numeric and long.
    const isInternalId = /[a-zA-Z]/.test(rfid) || rfid.length <= 8;

    if (isInternalId) {
      console.log('[Login] 🔐 Internal ID detected. Switching to PIN Mode.');
      this.pendingId.set(rfid);
      this.tempPin.set('');
      this.view.set('pin');
      this.toastService.info(this.translationService.translate('auth.login.enter_pin', 'Enter security PIN'), 'Security');
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.toastService.info(
      this.translationService.translate('auth.login.validating_credentials', 'Validating credentials...'),
      'Scan'
    );

    this.authService
      .collaboratorLogin({ rfid_tag: rfid })
      .then(() => {
        this.success.set(true);
        this.loading.set(false);
        this.toastService.success(
          this.translationService.translate('auth.login.access_granted', 'Access granted'),
          'System'
        );
      })
      .catch((err) => {
        console.error('Collaborator login failed:', err);
        this.loading.set(false);
        this.error.set(
          this.translationService.translate('auth.login.invalid_credentials', 'Credential not recognized.')
        );
      });
  }

  onPinKey(key: string) {
    if (key === 'clear') {
      this.tempPin.set(this.tempPin().slice(0, -1));
      return;
    }

    if (this.tempPin().length < 4) {
      this.tempPin.set(this.tempPin() + key);
    }

    if (this.tempPin().length === 4) {
      this.submitPinLogin();
    }
  }

  private submitPinLogin() {
    this.loading.set(true);
    this.error.set(null);
    
    this.authService.collaboratorLogin({
      internal_id: this.pendingId(),
      pin_code: this.tempPin()
    }).then(() => {
      this.success.set(true);
      this.loading.set(false);
      this.toastService.success('Login Successful', 'System');
    }).catch(err => {
      console.error('PIN Auth failed:', err);
      this.loading.set(false);
      this.tempPin.set('');
      this.error.set('Invalid PIN');
      this.toastService.error('Check your PIN and try again', 'Security');
    });
  }


  onSubmit(event?: Event) {
    if (event) event.preventDefault();
    
    if (!this.email || !this.password) {
      this.error.set(this.translationService.translate('auth.login.credentials_required', 'Credentials Required'));
      this.toastService.warning(this.translationService.translate('auth.login.please_enter_credentials', 'Please enter your credentials'), 'Validation');
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.toastService.info(this.translationService.translate('auth.login.signing_in', 'Signing in...'), 'Auth');

    // Simulate API call
    setTimeout(async () => {
      if (this.password === 'error') {
        this.error.set(this.translationService.translate('auth.login.invalid_credentials', 'Invalid Credentials'));
        this.loading.set(false);
        this.toastService.error(this.translationService.translate('auth.login.invalid_credentials', 'Invalid Credentials'), 'Error');
        return;
      }

      this.toastService.success(this.translationService.translate('auth.login.welcome', 'Welcome back'), 'Success');

      try {
        console.group('Industrial Form Auth Flow [v2.2-Hardened]');
        await this.authService.login({ email: this.email, password: this.password });
        this.success.set(true);
        this.loading.set(false);
        console.groupEnd();
      } catch (err) {
        console.error('API Login failed:', err);
        this.error.set(this.translationService.translate('auth.login.backend_error', 'Could not establish connection with backend.'));
        this.loading.set(false);
        this.toastService.error(this.translationService.translate('auth.login.network_failure', 'Network failure'), 'Connectivity');
        console.groupEnd();
      }
    }, 1000);
  }

  onJoinWithCode() {
    // Simulated flow
    const code = prompt('Enter Invitation Code:');
    if (code) {
      alert('Validating code: ' + code);
      this.onSubmit();
    }
  }

  onCreateCompany() {
    this.router.navigate(['/onboarding']);
  }
}
