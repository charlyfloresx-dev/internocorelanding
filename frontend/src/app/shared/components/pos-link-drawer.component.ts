import { Component, inject, OnInit } from '@angular/core';
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
        <div class="relative bg-white p-4 rounded-3xl shadow-2xl border border-slate-100 overflow-hidden">
          <img [src]="qrUrl" alt="POS Link QR" class="w-64 h-64">
        </div>
      </div>

      <div class="mt-10 w-full space-y-4">
        <div class="p-4 rounded-2xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-white/5 text-left">
          <p class="text-[8px] font-black text-slate-400 uppercase tracking-widest mb-2">Datos de Configuración</p>
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold text-slate-700 dark:text-slate-300">Tenant</span>
            <span class="text-[10px] font-black text-primary">{{ companyName }}</span>
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
  qrUrl: string = '';
  companyName: string = '';

  ngOnInit() {
    this.generateQr();
  }

  generateQr() {
    const session = this.authService.session() as any;
    const companyId = this.authService.activeCompanyId();
    this.companyName = session?.company_name || 'InternoCore';

    // Build the configuration object
    const config = {
      baseUrl: 'http://10.0.2.2:8000/api/v1', // Should be dynamic in production
      accessToken: this.authService.session()?.access_token,
      companyId: companyId,
      warehouseId: 'WH-MAIN-001', // Example
      terminalName: `WEB-LINKED-${new Date().getTime().toString().slice(-4)}`
    };

    const data = encodeURIComponent(JSON.stringify(config));
    this.qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${data}&bgcolor=ffffff&color=000000&qzone=2&margin=0`;
  }
}
