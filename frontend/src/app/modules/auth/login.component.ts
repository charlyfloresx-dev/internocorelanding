import { Component, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '@services/auth.service';
import { TenantSelectionComponent } from './tenant-selection.component';

// Definición del tipo para el control de vistas internas
type AccessView = 'hub' | 'login' | 'join' | 'register';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, TenantSelectionComponent],
  template: `
    <div class="min-h-screen flex items-center justify-center bg-slate-950 relative overflow-hidden p-6">
      <div class="absolute inset-0 pointer-events-none opacity-20" 
           style="background-image: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%);"></div>
      
      @if (auth.isLoading()) {
        <div class="absolute inset-0 bg-slate-900/90 z-50 flex flex-col items-center justify-center backdrop-blur-sm animate-fade-in">
          <i class="fa-solid fa-circle-notch fa-spin text-5xl text-sky-500 mb-6"></i>
          <p class="text-slate-300 font-mono text-lg animate-pulse tracking-widest">PROCESSING REQUEST...</p>
        </div>
      }

      <div class="w-full max-w-4xl z-10 relative transition-all duration-300">
        <div class="text-center mb-12 animate-fade-in-down">
          <div class="inline-flex items-center gap-3 mb-2">
            <i class="fa-solid fa-layer-group text-3xl text-slate-200"></i>
            <h1 class="text-3xl font-bold text-white tracking-tight">Interno Core</h1>
          </div>
          <p class="text-slate-500 text-sm font-medium tracking-widest uppercase">Industrial Manufacturing Execution System</p>
        </div>

        @if (auth.authStep() === 'handshake') {
          <div class="animate-fade-in">
            <app-tenant-selection (logout)="onCancelHandshake()"></app-tenant-selection>
          </div>
        } @else {
          @switch (view()) {
            
            @case ('hub') {
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in-up">
                <div (click)="setView('login')" class="group cursor-pointer bg-slate-800 border border-slate-700 rounded-xl p-8 flex flex-col items-center text-center transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:border-sky-500 hover:bg-slate-800/80">
                  <div class="w-20 h-20 rounded-full bg-slate-900 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 border border-slate-700 group-hover:border-sky-500/50">
                    <i class="fa-solid fa-right-to-bracket text-3xl text-slate-400 group-hover:text-sky-400 transition-colors"></i>
                  </div>
                  <h3 class="text-xl font-bold text-white mb-2 group-hover:text-sky-400 transition-colors">Iniciar Sesión</h3>
                  <p class="text-sm text-slate-400 leading-relaxed">Acceso para operarios, supervisores y administradores existentes.</p>
                </div>

                <div (click)="setView('join')" class="group cursor-pointer bg-slate-800 border border-slate-700 rounded-xl p-8 flex flex-col items-center text-center transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:border-yellow-500 hover:bg-slate-800/80">
                  <div class="w-20 h-20 rounded-full bg-slate-900 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 border border-slate-700 group-hover:border-yellow-500/50">
                    <i class="fa-solid fa-people-group text-3xl text-slate-400 group-hover:text-yellow-400 transition-colors"></i>
                  </div>
                  <h3 class="text-xl font-bold text-white mb-2 group-hover:text-yellow-400 transition-colors">Unirse a Empresa</h3>
                  <p class="text-sm text-slate-400 leading-relaxed">¿Tienes un código de invitación? Únete a tu equipo aquí.</p>
                </div>

                <div (click)="setView('register')" class="group cursor-pointer bg-slate-800 border border-slate-700 rounded-xl p-8 flex flex-col items-center text-center transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:border-green-500 hover:bg-slate-800/80">
                  <div class="w-20 h-20 rounded-full bg-slate-900 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 border border-slate-700 group-hover:border-green-500/50">
                    <i class="fa-solid fa-plus-square text-3xl text-slate-400 group-hover:text-green-400 transition-colors"></i>
                  </div>
                  <h3 class="text-xl font-bold text-white mb-2 group-hover:text-green-400 transition-colors">Crear Empresa</h3>
                  <p class="text-sm text-slate-400 leading-relaxed">Configura un nuevo entorno de manufactura desde cero.</p>
                </div>
              </div>
            }

            @case ('login') {
              <div class="max-w-md mx-auto bg-slate-800 rounded-2xl border border-slate-700 p-8 shadow-2xl animate-fade-in">
                <div class="text-center mb-6">
                  <h2 class="text-2xl font-bold text-sky-400">Bienvenido de nuevo</h2>
                  <p class="text-slate-400 text-sm mt-1">Ingresa tus credenciales corporativas</p>
                </div>
                <form (ngSubmit)="onLogin()" class="space-y-4">
                  <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Email Corporativo</label>
                    <input type="email" name="email" [(ngModel)]="loginData.email" 
                           class="w-full h-12 bg-slate-900 border border-slate-700 rounded-lg px-4 text-white focus:border-sky-500 focus:ring-1 focus:ring-sky-500 outline-none transition-all" 
                           placeholder="admin&#64;interno.com" required>
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Contraseña</label>
                    <input type="password" name="password" [(ngModel)]="loginData.password"
                           class="w-full h-12 bg-slate-900 border border-slate-700 rounded-lg px-4 text-white focus:border-sky-500 focus:ring-1 focus:ring-sky-500 outline-none transition-all" 
                           placeholder="••••••••" required>
                  </div>
                  <div class="flex gap-4 mt-8">
                    <button type="button" (click)="setView('hub')" class="w-1/3 h-12 rounded-lg bg-slate-700 text-white font-medium hover:bg-slate-600 transition-colors">Volver</button>
                    <button type="submit" class="w-2/3 h-12 rounded-lg bg-sky-600 text-white font-bold hover:bg-sky-500 shadow-lg shadow-sky-900/20 transition-all">Acceder</button>
                  </div>
                </form>
              </div>
            }

            @case ('join') {
              <div class="max-w-md mx-auto bg-slate-800 rounded-2xl border border-slate-700 p-8 shadow-2xl animate-fade-in">
                <div class="text-center mb-6">
                  <h2 class="text-2xl font-bold text-yellow-400">Unirse a Empresa</h2>
                  <p class="text-slate-400 text-sm mt-1">Ingresa el código de invitación de tu equipo</p>
                </div>
                <form class="space-y-4">
                  <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Código de Invitación</label>
                    <input type="text" name="inviteCode" class="w-full h-12 bg-slate-900 border border-slate-700 rounded-lg px-4 text-white focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 outline-none transition-all" placeholder="XXXX-XXXX-XXXX" required>
                  </div>
                  <div class="flex gap-4 mt-8">
                    <button type="button" (click)="setView('hub')" class="w-1/3 h-12 rounded-lg bg-slate-700 text-white font-medium hover:bg-slate-600 transition-colors">Volver</button>
                    <button type="submit" class="w-2/3 h-12 rounded-lg bg-yellow-600 text-white font-bold hover:bg-yellow-500 transition-all">Validar Código</button>
                  </div>
                </form>
              </div>
            }

            @case ('register') {
              <div class="max-w-md mx-auto bg-slate-800 rounded-2xl border border-slate-700 p-8 shadow-2xl animate-fade-in">
                <div class="text-center mb-6">
                  <h2 class="text-2xl font-bold text-green-400">Crear Empresa</h2>
                  <p class="text-slate-400 text-sm mt-1">Configura un nuevo entorno industrial</p>
                </div>
                <form class="space-y-4">
                  <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Nombre de la Empresa</label>
                    <input type="text" name="companyName" class="w-full h-12 bg-slate-900 border border-slate-700 rounded-lg px-4 text-white focus:border-green-500 focus:ring-1 focus:ring-green-500 outline-none transition-all" placeholder="Manufacturas Industriales S.A." required>
                  </div>
                  <div class="flex gap-4 mt-8">
                    <button type="button" (click)="setView('hub')" class="w-1/3 h-12 rounded-lg bg-slate-700 text-white font-medium hover:bg-slate-600 transition-colors">Volver</button>
                    <button type="submit" class="w-2/3 h-12 rounded-lg bg-green-600 text-white font-bold hover:bg-green-500 transition-all">Crear Empresa</button>
                  </div>
                </form>
              </div>
            }

          }
        }

        <div class="mt-12 text-center opacity-50">
            <p class="text-[10px] text-slate-500 font-mono">SECURE CONNECTION &bull; TLS 1.3 &bull; INTERNO CORE v2.4</p>
        </div>
      </div>
    </div>
  `
})
export class LoginComponent {
  public auth = inject(AuthService);
  private router = inject(Router);

  public view = signal<AccessView>('hub');
  public loginData = { email: '', password: '' };

  constructor() {
    // Escucha cambios en el estado de autenticación para redirigir
    effect(() => {
      if (this.auth.authStep() === 'authenticated') {
        console.log('[LoginComponent] ✅ Sesión confirmada. Navegando...');
        this.router.navigate(['/dashboard']);
      }
    });
  }

  setView(v: AccessView) {
    this.view.set(v);
  }

  onLogin() {
    if (!this.loginData.email || !this.loginData.password) return;

    this.auth.login(this.loginData).subscribe({
      next: () => {
        console.log('[LoginComponent] Handshake (T1) exitoso.');
      },
      error: (err) => {
        console.error('[LoginComponent] Error en autenticación:', err);
      }
    });
  }

  onCancelHandshake() {
    this.auth.logout();
    this.view.set('hub');
  }
}