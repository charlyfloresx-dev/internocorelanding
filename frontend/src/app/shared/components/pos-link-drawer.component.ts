import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-pos-link-drawer',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="p-8 flex flex-col items-center text-center">
      <div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-6">
        <mat-icon class="text-3xl">phonelink_setup</mat-icon>
      </div>
      
      <h2 class="text-xl font-black text-slate-900 dark:text-white uppercase tracking-wider mb-2">
        Vincular Dispositivo POS
      </h2>
      <p class="text-xs text-slate-500 dark:text-slate-400 mb-8 max-w-xs">
        Escanea este código desde la aplicación móvil de InternoCore para iniciar sesión automáticamente y configurar el servidor.
      </p>

      <div class="relative group">
        <!-- Glow Effect -->
        <div class="absolute -inset-4 bg-primary/20 blur-2xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
        
        <!-- QR Container -->
        <div class="relative bg-white p-4 rounded-3xl shadow-2xl border border-slate-100 overflow-hidden min-w-[256px] min-h-[256px] flex items-center justify-center">
          <ng-container *ngIf="qrUrl(); else loading">
            <img [src]="qrUrl()" alt="POS Link QR" class="w-64 h-64 transition-opacity duration-500" [class.opacity-0]="!qrUrl()">
          </ng-container>
          <ng-template #loading>
            <div class="w-64 h-64 bg-slate-100 animate-pulse rounded-2xl flex items-center justify-center">
               <mat-icon class="text-slate-300 scale-[2]">qr_code_2</mat-icon>
            </div>
          </ng-template>
        </div>
      </div>

      <div class="mt-10 w-full space-y-4">
        <div class="p-4 rounded-2xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-white/5 text-left">
          <p class="text-[8px] font-black text-slate-400 uppercase tracking-widest mb-2">Datos de Configuración</p>
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold text-slate-700 dark:text-slate-300">Tenant</span>
            <span class="text-[10px] font-black text-primary">{{ companyName() }}</span>
          </div>
          <div class="flex items-center justify-between mt-1">
            <span class="text-[10px] font-bold text-slate-700 dark:text-slate-300">Servidor</span>
            <span class="text-[10px] font-black text-primary">API v1 Production</span>
          </div>
        </div>
        
        <p class="text-[9px] text-slate-400 italic">
          * El código expira al cerrar la sesión actual o después de 15 minutos.
        </p>
      </div>
    </div>
  `
})
export class PosLinkDrawerComponent implements OnInit {
  authService = inject(AuthService);

  // Use signals for reactive updates
  qrUrl = signal<string>('');
  companyName = signal<string>('');

  async ngOnInit() {
    await this.loadDelegateQr();
  }

  async loadDelegateQr() {
    try {
      const handshake = await this.authService.getDelegateToken();
      const session = this.authService.session() as any;

      this.companyName.set(session?.company_name || 'InternoCore');

      // CASE: Backend generated local QR [Phase 94]
      if (handshake.qr_b64) {
        this.qrUrl.set(handshake.qr_b64);
        console.log('[PosLinkDrawer] ✅ Local QR loaded from backend');
      } else {
        console.warn('[PosLinkDrawer] ⚠️ Backend did not return qr_b64. Falling back to frontend generator.');
        // Minimalist fallback logic could go here if needed
      }
    } catch (err) {
      console.error('[PosLinkDrawer] ❌ Failed to load delegation QR:', err);
    }
  }
}
