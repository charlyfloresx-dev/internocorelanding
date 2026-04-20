import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '@services/auth.service';

/**
 * AUTH GUARD - FLUJO V2.1 + ZERO TRUST
 * 
 * CRITICAL: Zero Trust modelo - NO confiar solo en signals en memoria
 * Validar localStorage DIRECTAMENTE para eliminar race conditions
 * 
 * Reglas:
 * 1. authStep === 'authenticated' → Acceso a /dashboard y rutas protegidas (PERO verificar localStorage)
 * 2. authStep === 'guest' → Solo acceso a /login
 * 3. authStep === 'handshake' → Se queda en /login viendo tenant-selection
 * 4. Zero Trust: Si localStorage.interno_auth_ctx NO existe → DENY (incluso si signal dice autenticado)
 */
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router: Router = inject(Router);

  // Rutas públicas que NO requieren autenticación
  const publicRoutes = ['/login'];
  const isPublicRoute = publicRoutes.some(publicRoute => state.url.startsWith(publicRoute));

  // Permitir acceso explícito al selector de empresa durante el 'handshake'
  if (state.url.startsWith('/auth/select-company') && authService.authStep() === 'handshake') {
    return true;
  }

  // Si la ruta es pública, permitir acceso sin importar authStep
  if (isPublicRoute) {
    return true;
  }

  // 1. In-Memory Check (Prioridad Alta: Fast Path & Login Transition)
  // Si el servicio ya tiene la sesión en memoria (acabamos de loguearnos), permitir paso.
  if (authService.isAuthenticated()) {
    console.log('[AuthGuard] ✅ Acceso permitido por estado en memoria (Login Transition).');
    return true;
  }

  // ============================================
  // ZERO TRUST VALIDATION
  // Validar localStorage DIRECTAMENTE primero
  // Si fue borrado, NEGAR acceso inmediatamente
  // ============================================
  const savedCtx = localStorage.getItem('interno_auth_ctx');
  if (!savedCtx) {
    console.log('[AuthGuard] 🚫 ZERO TRUST VIOLATION: localStorage.interno_auth_ctx es NULL. Requiriendo login.');
    router.navigate(['/login']);
    return false;
  }

  // Validar que el access_token exista en localStorage
  try {
    const parsedCtx = JSON.parse(savedCtx);
    if (!parsedCtx.access_token) {
      console.log('[AuthGuard] 🚫 ZERO TRUST VIOLATION: access_token es NULL en localStorage. Requiriendo login.');
      router.navigate(['/login']);
      return false;
    }
  } catch (e) {
    console.log('[AuthGuard] 🚫 ZERO TRUST VIOLATION: localStorage.interno_auth_ctx es JSON inválido. Error:', e);
    router.navigate(['/login']);
    return false;
  }

  // Si no está autenticado, redirigir a /login
  console.log('[AuthGuard] ❌ Acceso denegado. Redirigiendo a /login');
  router.navigate(['/login']);
  return false;
};