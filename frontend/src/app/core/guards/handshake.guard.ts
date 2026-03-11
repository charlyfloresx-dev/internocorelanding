import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '@services/auth.service';

/**
 * HANDSHAKE GUARD
 * Solo permite acceso a /auth/select-company cuando el usuario está en estado 'handshake'
 * (después de login exitoso, antes de seleccionar empresa)
 */
export const handshakeGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router: Router = inject(Router);

  const accessToken = authService.token() || localStorage.getItem('access_token');
  const selectionToken = authService.selectionToken() || sessionStorage.getItem('selection_token');

  // If there's already an access_token, the user is fully authenticated.
  if (accessToken) {
    console.warn('[HandshakeGuard] User is already fully authenticated. Redirecting to /dashboard');
    return router.createUrlTree(['/dashboard']);
  }

  // If there is a selection token and NO access token, they are in the handshake step.
  if (selectionToken && !accessToken) {
    return true;
  }

  // Si no está en handshake, redirigir al login
  console.warn('[HandshakeGuard] Missing selection token. Redirecting to /login');
  return router.createUrlTree(['/login']);
};
