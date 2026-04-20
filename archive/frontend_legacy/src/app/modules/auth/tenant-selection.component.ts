import { Component, inject, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '@services/auth.service';
import { ToastService } from '@services/toast.service';
import { TranslationService } from '@services/translation.service';

@Component({
  selector: 'app-tenant-selection',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="min-h-screen bg-surface-bg flex items-center justify-center p-6 relative overflow-hidden transition-colors duration-300">
      <!-- Background Effects -->
      <div class="absolute top-0 left-0 w-full h-full opacity-30 pointer-events-none">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 blur-[120px] rounded-full animate-pulse-glow"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-ic-blue/10 blur-[120px] rounded-full animate-pulse-glow" style="animation-delay: 1s"></div>
      </div>

      <div class="max-w-5xl w-full relative z-10 animate-slide-in-right">
        <div class="text-center mb-12">
          <h2 class="text-4xl font-black text-surface-text tracking-tighter uppercase italic glow-text">
            {{ ts.translate('auth.tenant_selection_title', 'Selección de Contexto') }}
          </h2>
          <p class="text-surface-text-muted mt-2 font-mono text-[10px] tracking-widest uppercase">
            {{ ts.translate('auth.tenant_selection_subtitle', 'Seleccione la empresa o planta para iniciar operaciones') }}
          </p>
        </div>

        <!-- Search Bar -->
        <div class="max-w-md mx-auto mb-10 relative group">
          <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">search</mat-icon>
          <input 
            type="text" 
            [(ngModel)]="searchQuery" 
            placeholder="Filtrar empresas..."
            class="w-full bg-surface-card/50 backdrop-blur-md border border-surface-border/[0.1] rounded-2xl pl-12 pr-4 py-4 text-sm text-surface-text outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all font-sans"
          >
        </div>

        <!-- Company List (Vertical Command Console) -->
        <div class="flex flex-col gap-3 w-full max-w-lg mx-auto p-4 custom-scrollbar max-h-[60vh] overflow-y-auto">
          @for (item of filteredAccesses(); track item.company.id) {
            <button 
              (click)="onSelect(item.company.id)"
              [disabled]="isLoading() && selectedId() !== item.company.id"
              class="industrial-card flex items-center p-4 hover:border-primary/50 transition-all group relative animate-fade-in disabled:opacity-50 min-h-[72px]"
            >
              <!-- Icon/Logo Section -->
              <div class="w-12 h-12 bg-surface-bg/50 rounded-xl flex items-center justify-center border border-surface-border/[0.1] group-hover:border-primary/30 group-hover:shadow-[0_0_15px_rgba(var(--color-primary),0.1)] transition-all overflow-hidden shrink-0 mr-4">
                @if (item.company.logo) {
                  <img [src]="item.company.logo" class="w-full h-full object-contain p-2" [alt]="item.company.name">
                } @else {
                  <mat-icon class="text-surface-text-muted group-hover:text-primary transition-colors text-2xl">factory</mat-icon>
                }
              </div>

              <!-- Content Section -->
              <div class="flex flex-col text-left min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <h3 class="text-sm font-black text-surface-text uppercase tracking-tight group-hover:text-primary transition-colors truncate italic">
                    {{ item.company.name }}
                  </h3>
                  @if (item.company.is_new) {
                    <span class="bg-primary/20 text-primary text-[7px] font-black px-1.5 py-0.5 rounded border border-primary/30 uppercase tracking-widest shrink-0">
                      NEW
                    </span>
                  }
                </div>
                <div class="flex items-center gap-2 mt-0.5">
                  <span class="text-[9px] font-bold text-primary/80 uppercase tracking-wider">{{ item.role.name }}</span>
                  <span class="w-1 h-1 bg-white/20 rounded-full"></span>
                  <span class="text-[8px] text-surface-text-muted uppercase tracking-widest truncate">{{ item.company.group_name || 'Operaciones' }}</span>
                </div>
              </div>

              <!-- Action Icon -->
              <mat-icon class="ml-auto text-primary opacity-0 group-hover:opacity-100 transition-all transform group-hover:translate-x-1">chevron_right</mat-icon>
              
              <!-- Loading Overlay -->
              @if (isLoading() && selectedId() === item.company.id) {
                <div class="absolute inset-0 bg-ic-dark/40 backdrop-blur-[2px] flex items-center justify-center rounded-xl z-20">
                   <mat-icon class="animate-gear-spin text-primary text-2xl">settings</mat-icon>
                </div>
              }
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
            class="px-8 py-3 bg-surface-card/10 border border-surface-border/[0.1] rounded-full text-surface-text-muted hover:text-primary hover:border-primary/30 flex items-center gap-3 mx-auto transition-all font-black text-[10px] uppercase tracking-[0.2em]"
          >
            <mat-icon class="text-sm">logout</mat-icon>
            {{ ts.translate('auth.logout_and_back', 'Cerrar sesión y volver') }}
          </button>
        </div>
      </div>
    </div>
  `
})
export class TenantSelectionComponent {
  auth = inject(AuthService);
  ts = inject(TranslationService);
  private toast = inject(ToastService);
  private router = inject(Router);

  searchQuery = '';
  selectedId = signal<string | null>(null);
  isLoading = computed(() => this.auth.isLoading());

  filteredAccesses = computed(() => {
    const query = this.searchQuery.toLowerCase();
    return this.auth.availableAccesses().filter(a =>
      a.company.name.toLowerCase().includes(query)
    );
  });

  onSelect(id: string) {
    this.selectedId.set(id);
    const access = this.auth.availableAccesses().find(a => a.company.id === id);
    this.toast.info(`Cargando entorno: ${access?.company.name}`, 'InternoCore');

    this.auth.selectCompany(id);
  }

  logout() {
    this.auth.logout();
  }

  onJoinWithCode() {
    const code = prompt('Enter Invitation Code:');
    if (code) {
      this.toast.info('Feature coming soon...', 'Invitación');
    }
  }

  onCreateCompany() {
    this.router.navigate(['/onboarding']);
  }
}
