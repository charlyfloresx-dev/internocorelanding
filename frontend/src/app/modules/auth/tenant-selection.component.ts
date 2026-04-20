import {Component, inject, PLATFORM_ID, computed} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {CommonModule} from '@angular/common';
import {Router} from '@angular/router';
import {AuthService} from '../../core/services/auth.service';
import {ToastService} from '../../core/services/toast.service';
import {MatIconModule} from '@angular/material/icon';
import {TranslatePipe} from '../../shared/pipes/translate.pipe';
import {FormsModule} from '@angular/forms';

@Component({
  selector: 'app-tenant-selection',
  standalone: true,
  imports: [CommonModule, MatIconModule, TranslatePipe, FormsModule],
  template: `
    <div class="min-h-screen bg-surface-bg flex items-center justify-center p-6 relative overflow-hidden transition-colors duration-300">
      <!-- Background Effects -->
      <div class="absolute top-0 left-0 w-full h-full opacity-30 pointer-events-none">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 blur-[120px] rounded-full animate-pulse-glow"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-ic-blue/10 blur-[120px] rounded-full animate-pulse-glow" style="animation-delay: 1s"></div>
      </div>

      <div class="max-w-5xl w-full relative z-10 animate-slide-in-right">
        <div class="text-center mb-12">
          <h2 class="text-4xl font-black text-surface-text tracking-tighter uppercase italic glow-text">{{ 'auth.tenant_selection_title' | translate:'Selección de Contexto' }}</h2>
          <p class="text-surface-text-muted mt-2 font-mono text-[10px] tracking-widest uppercase">{{ 'auth.tenant_selection_subtitle' | translate:'Seleccione la empresa o planta para iniciar operaciones' }}</p>
        </div>

        <!-- Search Bar -->
        <div class="max-w-md mx-auto mb-10 relative group">
          <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">search</mat-icon>
          <input 
            type="text" 
            [(ngModel)]="searchQuery" 
            placeholder="Filtrar empresas..."
            class="w-full bg-surface-card/50 backdrop-blur-md border border-white/10 rounded-2xl pl-12 pr-4 py-4 text-sm text-surface-text outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
          >
        </div>

        <!-- Company Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          @for (access of filteredAccesses(); track access.company_id) {
            <button 
              (click)="onSelect(access.company_id)"
              class="glass-card p-8 text-left rounded-3xl hover:border-primary/50 hover:shadow-primary/10 hover:scale-[1.02] transition-all group relative animate-fade-in"
            >
              <div class="flex items-start justify-between mb-6">
                <div class="w-16 h-16 bg-surface-bg/50 rounded-2xl flex items-center justify-center border border-white/10 group-hover:border-primary/30 group-hover:shadow-[0_0_20px_rgba(0,229,255,0.1)] transition-all duration-500">
                  <mat-icon class="text-surface-text-muted group-hover:text-primary transition-colors text-3xl w-8 h-8">business</mat-icon>
                </div>
                @if (access.is_new) {
                  <span class="bg-primary/20 text-primary text-[10px] font-black px-3 py-1 rounded-full border border-primary/30 uppercase tracking-widest">
                    Nueva
                  </span>
                }
              </div>
              
              <h3 class="text-xl font-black text-surface-text mb-2 uppercase tracking-tighter group-hover:text-primary transition-colors">{{ access.company_name }}</h3>
              
              <div class="flex flex-wrap gap-2 mt-6">
                @for (role of access.role_names; track role) {
                  <span class="text-[9px] font-black bg-white/5 text-surface-text-muted px-3 py-1.5 rounded-lg border border-white/5 uppercase tracking-[0.2em] group-hover:border-primary/20 group-hover:text-primary/80 transition-all">
                    {{ role }}
                  </span>
                }
              </div>

              <!-- Hover Glow Effect -->
              <div class="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
              <div class="absolute bottom-0 left-0 w-full h-1 bg-primary transform scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500"></div>
            </button>
          }
        </div>

        <!-- Back to Login -->
        <div class="mt-16 flex flex-col items-center gap-6">
          <div class="flex items-center gap-8">
            <button (click)="onJoinWithCode()" class="text-[10px] font-black text-primary uppercase tracking-widest hover:underline transition-all">
              Join with Code
            </button>
            <div class="w-1 h-1 bg-white/20 rounded-full"></div>
            <button (click)="onCreateCompany()" class="text-[10px] font-black text-primary uppercase tracking-widest hover:underline transition-all">
              Create New Company
            </button>
          </div>

          <button 
            (click)="logout()" 
            class="px-8 py-3 bg-white/5 border border-white/10 rounded-full text-surface-text-muted hover:text-primary hover:border-primary/30 flex items-center gap-3 mx-auto transition-all font-black text-[10px] uppercase tracking-[0.2em]"
          >
            <mat-icon class="text-sm">logout</mat-icon>
            Cerrar sesión y volver
          </button>
        </div>
      </div>
    </div>
  `
})
export class TenantSelectionComponent {
  authService = inject(AuthService);
  private toastService = inject(ToastService);
  private router = inject(Router);
  private platformId = inject(PLATFORM_ID);
  private isBrowser = isPlatformBrowser(this.platformId);

  searchQuery = '';

  filteredAccesses = computed(() => {
    const query = this.searchQuery.toLowerCase();
    const all = this.authService.availableAccesses();
    console.log('[TenantSelector] 🔍 Filtering companies:', { count: all.length, query });
    return all.filter(a => 
      a.company_name.toLowerCase().includes(query)
    );
  });

  onJoinWithCode() {
    const code = prompt('Enter Invitation Code:');
    if (code) {
      this.toastService.info('Validando código...', 'Invitación');
      this.router.navigate(['/dashboard']);
    }
  }

  onCreateCompany() {
    this.router.navigate(['/onboarding']);
  }

  async onSelect(id: string) {
    console.group('Tenant Selection Flow');
    const access = this.authService.availableAccesses().find(a => a.company_id === id);
    console.log('[TenantSelector] 🏢 Company Selected:', { id, name: access?.company_name });
    
    this.toastService.info(`Cargando entorno: ${access?.company_name}`, 'Sistema');
    
    try {
      await this.authService.selectCompany(id);
      this.toastService.success('Entorno cargado correctamente', 'Éxito');
      console.groupEnd();
    } catch (err) {
      console.error('[TenantSelector] ❌ API selectCompany failed:', err);
      this.toastService.error('No se pudo establecer conexión con el backend. Verifique su red.', 'Fallo de conectividad');
      console.groupEnd();
    }
  }

  logout() {
    this.toastService.info('Cerrando sesión...', 'Sistema');
    this.authService.logout();
  }
}
