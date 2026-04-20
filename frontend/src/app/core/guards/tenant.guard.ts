// temp_future/src/app/core/guards/tenant.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * TenantGuard: Ensures a company is active and authorized.
 */
export const tenantGuard: CanActivateFn = (route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  
  const activeCompanyId = auth.activeCompanyId();
  const availableCompanies = auth.availableCompanies();

  if (!auth.isAuthenticated()) {
    router.navigate(['/auth/login']);
    return false;
  }

  if (!activeCompanyId) {
    // If authenticated but no company, send to selection
    router.navigate(['/auth/select-company']);
    return false;
  }

  // Double Check: Is the active company still in the allowed list?
  const isAuthorized = availableCompanies.some(c => c.company_id === activeCompanyId);
  if (!isAuthorized && availableCompanies.length > 0) {
    console.error('[Security] Active company is not in the authorized list.');
    router.navigate(['/auth/select-company']);
    return false;
  }

  return true;
};
