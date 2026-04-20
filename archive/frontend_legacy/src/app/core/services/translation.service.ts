import { Injectable, signal, effect, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class TranslationService {
    private http = inject(HttpClient);

    // Señal para el idioma actual
    currentLang = signal<string>(localStorage.getItem('ic_lang') || 'es');

    // Señal para el diccionario de traducciones
    private translations = signal<any>({});

    constructor() {
        // Cargar traducciones iniciales
        this.loadTranslations(this.currentLang());

        // Persistir cambio de idioma
        effect(() => {
            localStorage.setItem('ic_lang', this.currentLang());
        });
    }

    async loadTranslations(lang: string) {
        try {
            const data = await firstValueFrom(
                this.http.get(`assets/locales/${lang}.json`)
            );
            this.translations.set(data);
        } catch (error) {
            console.error(`Could not load translations for ${lang}`, error);
        }
    }

    async setLanguage(lang: string) {
        await this.loadTranslations(lang);
        this.currentLang.set(lang);
    }

    /**
     * Obtiene una traducción por su path (ej: 'menu.dashboard')
     * @param path El path de la clave (ej: 'menu.dashboard')
     * @param defaultValue Valor por defecto si no se encuentra la clave
     */
    translate(path: string, defaultValue?: string): string {
        if (!path) return defaultValue || '';
        const keys = path.split('.');
        let result = this.translations();

        for (const key of keys) {
            if (result && result[key]) {
                result = result[key];
            } else {
                return defaultValue || path; // Fallback al default o al path
            }
        }

        return result;
    }
}
