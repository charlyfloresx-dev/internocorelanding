import { inject } from '@angular/core';
import { CanActivateFn, Router, RouterStateSnapshot } from '@angular/router';
import { AuthService } from '@services/auth.service';

export const tenantGuard: CanActivateFn = (route, state: RouterStateSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const activeCompany = authService.activeCompany();

  // The authGuard should run first, ensuring we are authenticated and have a context.
  // This guard handles the business logic redirection based on tenant status.
  if (!activeCompany) {
    // This is a fallback. authGuard should prevent this state.
    return router.parseUrl('/login');
  }

  const isNew = activeCompany.is_new;
  const isGoingToOnboarding = state.url.startsWith('/onboarding/setup-warehouse');

  if (isNew && !isGoingToOnboarding) {
    console.log('[TenantGuard] 🚧 New company detected. Redirecting to onboarding.');
    return router.parseUrl('/onboarding/setup-warehouse');
  }

  if (!isNew && isGoingToOnboarding) {
    console.log('[TenantGuard] ⛔️ Company already configured. Redirecting to dashboard.');
    return router.parseUrl('/dashboard');
  }

  return true;
};