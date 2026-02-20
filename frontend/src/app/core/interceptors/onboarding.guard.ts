import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '@services/auth.service';

export const onboardingGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isNewUser()) {
    // Bloqueo de seguridad: Usuario nuevo debe ir al wizard
    return router.createUrlTree(['/onboarding']);
  }

  return true;
};