import {ChangeDetectionStrategy, Component, inject} from '@angular/core';
import {RouterOutlet} from '@angular/router';
import {ToastContainerComponent} from './shared/components/toast-container.component';

import {MatIconModule} from '@angular/material/icon';
import {AuthService} from './core/services/auth.service';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ToastContainerComponent, MatIconModule],
  template: `
    <router-outlet></router-outlet>
    <app-toast-container></app-toast-container>

    <!-- 💳 GLOBAL PAYWALL (Phase 19) -->
    @if (authService.isUnpaid()) {
      <div class="fixed inset-0 z-[9999] bg-slate-950/95 backdrop-blur-xl flex items-center justify-center p-6 animate-in fade-in duration-500">
        <div class="max-w-md w-full text-center space-y-8 industrial-card p-12 border-2 border-rose-500/30 shadow-2xl shadow-rose-500/20">
          <div class="flex justify-center">
            <div class="w-24 h-24 bg-rose-500/20 rounded-full flex items-center justify-center text-rose-500 animate-pulse">
              <mat-icon class="text-6xl">credit_card_off</mat-icon>
            </div>
          </div>
          
          <div class="space-y-4">
            <h1 class="text-3xl font-black text-white uppercase tracking-tighter italic">Acceso Restringido</h1>
            <p class="text-sm text-slate-400 font-bold uppercase tracking-widest leading-relaxed">
              Su suscripción ha sido suspendida por falta de pago. Por favor, regularice su situación para recuperar el acceso a sus datos industriales.
            </p>
          </div>

          <div class="pt-6">
            <button class="w-full py-5 bg-rose-500 text-white font-black uppercase tracking-[0.2em] rounded-2xl hover:bg-rose-600 transition-all shadow-xl shadow-rose-500/20 active:scale-95">
              Pagar Factura Pendiente
            </button>
            <button (click)="authService.logout()" class="mt-4 w-full py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest hover:text-white transition-colors">
              Cerrar Sesión
            </button>
          </div>
          
          <div class="pt-8 border-t border-white/5 text-[9px] text-slate-600 font-black uppercase tracking-[0.3em]">
            InternoCore v2.0 • Billing Guard Active
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    :host {
      display: block;
      height: 100vh;
    }
  `]
})
export class App {
  authService = inject(AuthService);
}
