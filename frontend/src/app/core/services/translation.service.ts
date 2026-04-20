import {Injectable, signal, inject, PLATFORM_ID} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';

@Injectable({
  providedIn: 'root'
})
export class TranslationService {
  private platformId = inject(PLATFORM_ID);
  private isBrowser = isPlatformBrowser(this.platformId);
  
  // Current language state
  currentLang = signal<string>('es');
  // Current dictionary
  private dictionary = signal<Record<string, unknown>>({});
  // Loading state
  isLoading = signal<boolean>(false);
  
  constructor() {
    if (this.isBrowser) {
      const savedLang = localStorage.getItem('ic_lang') || 'es';
      this.setLanguage(savedLang);
    }
  }

  async setLanguage(lang: string) {
    this.isLoading.set(true);
    this.currentLang.set(lang);
    if (this.isBrowser) {
      localStorage.setItem('ic_lang', lang);
    }
    await this.loadLocale(lang);
    this.isLoading.set(false);
  }

  private async loadLocale(lang: string) {
    try {
      const response = await fetch(`/locales/${lang}.json`);
      if (response.ok) {
        const data = await response.json();
        this.dictionary.set(data);
      } else {
        console.warn(`Locale ${lang} not found, falling back to empty dictionary`);
        this.dictionary.set({});
      }
    } catch (error) {
      console.error('Failed to load locale', error);
      this.dictionary.set({});
    }
  }

  /**
   * Translates a key using the local dictionary.
   * @param key The translation key (e.g., 'menu.dashboard')
   * @param fallback The fallback string (usually the 'name' field from API)
   */
  translate(key: string | undefined, fallback = ''): string {
    if (!key) return fallback;
    
    const parts = key.split('.');
    let current: unknown = this.dictionary();
    
    for (const part of parts) {
      if (current && typeof current === 'object' && part in (current as Record<string, unknown>)) {
        current = (current as Record<string, unknown>)[part];
      } else {
        return fallback;
      }
    }
    
    return typeof current === 'string' ? current : fallback;
  }
}
