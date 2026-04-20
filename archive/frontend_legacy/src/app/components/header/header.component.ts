
import { Component, inject, output, signal, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '@services/auth.service';
import { TranslationService } from '@services/translation.service';
import { ThemeService } from '@services/theme.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="h-16 bg-surface-card border-b border-surface-border flex items-center justify-between px-8 z-30 relative transition-all duration-300">
      
      <!-- Left: Active Context -->
      <div class="flex flex-col">
        <span class="text-[8px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Contexto Activo</span>
        <h2 class="text-sm font-black text-surface-text italic tracking-tighter glow-text-sm leading-tight uppercase">
          {{ auth.activeCompany()?.name || 'InternoCore - System' }}
        </h2>
      </div>

      <!-- Right: Action Icons -->
      <div class="flex items-center gap-6">
        
        <!-- Language Selector -->
        <div class="relative">
          <button (click)="showLangMenu.set(!showLangMenu())" 
                  class="flex items-center gap-2 text-surface-text-muted hover:text-primary transition-all group">
            <span class="material-icons text-xl group-hover:scale-110 transition-transform">language</span>
            <span class="text-[10px] font-black uppercase tracking-widest">{{ ts.currentLang() === 'es' ? 'ES' : 'EN' }}</span>
          </button>

          @if (showLangMenu()) {
            <div class="absolute right-0 mt-3 w-40 bg-surface-card border border-surface-border rounded-xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-50 py-2 animate-fade-in-up origin-top-right">
              <button (click)="ts.setLanguage('es'); showLangMenu.set(false)"
                      class="w-full px-4 py-2.5 text-left text-[10px] font-bold uppercase tracking-widest hover:bg-primary/10 hover:text-primary transition-colors flex items-center justify-between"
                      [class.text-primary]="ts.currentLang() === 'es'">
                Español
                @if (ts.currentLang() === 'es') { <span class="material-icons text-sm">check</span> }
              </button>
              <button (click)="ts.setLanguage('en'); showLangMenu.set(false)"
                      class="w-full px-4 py-2.5 text-left text-[10px] font-bold uppercase tracking-widest hover:bg-primary/10 hover:text-primary transition-colors flex items-center justify-between"
                      [class.text-primary]="ts.currentLang() === 'en'">
                English
                @if (ts.currentLang() === 'en') { <span class="material-icons text-sm">check</span> }
              </button>
            </div>
          }
        </div>

        <!-- Theme Toggle -->
        <button (click)="theme.toggleTheme()" 
                class="text-surface-text-muted hover:text-primary transition-all group flex items-center justify-center">
          <span class="material-icons text-xl group-hover:rotate-12 transition-transform">
            {{ theme.darkMode() ? 'light_mode' : 'dark_mode' }}
          </span>
        </button>

        <!-- Notifications -->
        <button class="relative text-surface-text-muted hover:text-primary transition-all group flex items-center justify-center">
          <span class="material-icons text-xl group-hover:animate-swing transition-transform">notifications</span>
          <span class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-surface-card animate-pulse"></span>
        </button>

        <div class="h-8 w-px bg-surface-border mx-2"></div>
      </div>
    </header>
  `
})
export class HeaderComponent {
  auth = inject(AuthService);
  ts = inject(TranslationService);
  theme = inject(ThemeService);
  toggleMenu = output<void>();

  showLangMenu = signal(false);

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.relative')) {
      this.showLangMenu.set(false);
    }
  }
}
