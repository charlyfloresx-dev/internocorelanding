import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AdminAuthService } from '@services/admin-auth.service';

/**
 * Guard para proteger rutas de Modo Dios (Administración Técnica).
 * Verifica si el AdminAuthService tiene una llave maestra en memoria.
 */
export const godModeGuard: CanActivateFn = (route, state) => {
    const adminAuthService = inject(AdminAuthService);
    const router = inject(Router);

    if (adminAuthService.isGodModeEnabled()) {
        return true;
    }

    console.warn('⛔ [GodModeGuard] Intento de acceso administrativo sin llave maestra. Redirigiendo...');

    // Redirigir al dashboard general si no tiene acceso a God Mode
    router.navigate(['/dashboard']);
    return false;
};
