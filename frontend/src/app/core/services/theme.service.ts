import { Injectable, signal, computed } from '@angular/core';

/**
 * Theme Service (Phase 0 — prefers-color-scheme support)
 *
 * Respects OS color scheme preference via CSS media query.
 * No manual classes, no localStorage, no UI toggle effects.
 * Browser automatically switches via @media (prefers-color-scheme: dark).
 *
 * This service is kept for backward compatibility only:
 * - darkMode() signal returns true if OS prefers dark
 * - toggleDarkMode() no-op (does not persist or apply .dark class)
 * - All theme switching is CSS-driven
 *
 * OS Control:
 * - macOS: System Preferences > General > Appearance
 * - Windows: Settings > Colors > Mode
 * - Linux: GTK theme or app-specific
 */
@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private prefersSystemDark = signal(
    typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches
  );

  darkMode = computed(() => this.prefersSystemDark());

  constructor() {
    if (typeof window !== 'undefined') {
      // Listen for OS theme changes and update signal
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handler = (e: MediaQueryListEvent) => this.prefersSystemDark.set(e.matches);

      // Modern API
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handler);
      }
      // Fallback for older browsers
      else if (mediaQuery.addListener) {
        mediaQuery.addListener(handler);
      }

      console.log(`[ThemeService] Theme: prefers-color-scheme (${this.darkMode() ? 'dark' : 'light'})`);
    }
  }

  toggleDarkMode(): void {
    // No-op: theming is now purely OS-controlled via prefers-color-scheme
    // This method is kept for backward compatibility with navbar button
  }
}
