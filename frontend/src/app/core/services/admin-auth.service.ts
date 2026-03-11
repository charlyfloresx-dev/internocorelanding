import { Injectable, signal, computed } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class AdminAuthService {
    /**
     * Llave Maestra de God Mode (Memory-Only).
     * NO se persiste en localStorage para evitar fugas de seguridad.
     */
    private adminMasterKey = signal<string | null>(null);

    /**
     * Indica si el Modo Dios está activo.
     */
    isGodModeEnabled = computed(() => !!this.adminMasterKey());

    constructor() { }

    /**
     * Habilita el Modo Dios con la llave proporcionada.
     * @param key La llave maestra INT_ADMIN_MASTER_KEY.
     */
    enableGodMode(key: string): void {
        if (key && key.trim().length > 0) {
            this.adminMasterKey.set(key);
            console.log('🛡️ [AdminAuthService] God Mode Activado.');
        }
    }

    /**
     * Deshabilita el Modo Dios y limpia la llave de memoria.
     */
    disableGodMode(): void {
        this.adminMasterKey.set(null);
        console.log('🛡️ [AdminAuthService] God Mode Desactivado y llave limpiada.');
    }

    /**
     * Retorna la llave maestra actual.
     * Usado principalmente por el interceptor HTTP.
     */
    getMasterKey(): string | null {
        return this.adminMasterKey();
    }
}
