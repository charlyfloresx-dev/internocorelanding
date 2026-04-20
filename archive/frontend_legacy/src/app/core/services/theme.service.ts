import { Injectable, signal, effect, PLATFORM_ID, inject, Injector } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Injectable({
    providedIn: 'root'
})
export class ThemeService {
    darkMode = signal<boolean>(true);
    private platformId = inject(PLATFORM_ID);
    private injector = inject(Injector);

    constructor() {
        if (isPlatformBrowser(this.platformId)) {
            (window as any).__themeService = this;
            console.log('[ThemeService] ✅ Constructor running in browser');
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                this.darkMode.set(savedTheme === 'dark');
            } else {
                const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
                this.darkMode.set(prefersDark);
            }

            // Sync initial state to DOM immediately
            this.updateDom(this.darkMode());
        }

        // Register effect with explicit injector to ensure it survives and runs
        effect(() => {
            const isDark = this.darkMode();
            console.log('[ThemeService] 🌓 Signal changed:', isDark);
            this.updateDom(isDark);
        }, { injector: this.injector });
    }

    private updateDom(isDark: boolean) {
        if (!isPlatformBrowser(this.platformId)) return;

        const html = document.documentElement;
        if (isDark) {
            html.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            console.log('[ThemeService] ✅ Added .dark class to HTML');
        } else {
            html.classList.remove('dark');
            localStorage.setItem('theme', 'light');
            console.log('[ThemeService] ☀️ Removed .dark class from HTML');
        }
    }

    toggleTheme() {
        this.darkMode.update(isDark => !isDark);
    }
}
