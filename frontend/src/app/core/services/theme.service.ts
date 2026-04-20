import {Injectable, signal, effect, inject, PLATFORM_ID} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private platformId = inject(PLATFORM_ID);
  private isBrowser = isPlatformBrowser(this.platformId);
  
  darkMode = signal<boolean>(true); // Default to dark as per current app style

  constructor() {
    if (this.isBrowser) {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme) {
        this.darkMode.set(savedTheme === 'dark');
      } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        this.darkMode.set(prefersDark);
      }

      // Shock Cure: Immediate DOM Sync
      const initialDark = this.darkMode();
      if (!initialDark) {
        document.documentElement.classList.remove('dark');
        document.body.classList.remove('dark');
      }
      console.log(`[ThemeService] Booting in: ${initialDark ? 'DARK' : 'LIGHT'}`);

      effect(() => {
        const isDark = this.darkMode();
        
        // Redundant cleanup to prevent "sticky" classes
        document.documentElement.classList.remove('dark', 'light');
        document.body.classList.remove('dark', 'light');
        
        if (isDark) {
          document.documentElement.classList.add('dark');
          document.body.classList.add('dark');
          localStorage.setItem('theme', 'dark');
        } else {
          document.documentElement.classList.add('light');
          document.body.classList.add('light');
          localStorage.setItem('theme', 'light');
        }
        
        console.log(`[ThemeService] Sync complete. Mode: ${isDark ? 'DARK' : 'LIGHT'}`);
      });
    }
  }

  toggleDarkMode() {
    this.darkMode.update(v => !v);
  }
}
