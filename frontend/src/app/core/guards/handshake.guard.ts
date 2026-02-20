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

  // Solo permitir si el estado es exactamente 'handshake'
  if (authService.authStep() === 'handshake') {
    return true;
  }

  // Si no está en handshake, redirigir al login
  console.warn('[HandshakeGuard] Estado no es handshake. Redirigiendo a /login');
  router.navigate(['/login']);
  return false;
};
