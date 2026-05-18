import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Enforces granular Permission slug requirements on protected routes.
 *
 * Configure via route data:
 *   data: { requiredPermission: 'admin.user.manage' }           // single slug
 *   data: { requiredPermission: ['master_data.product.read',    // any-of (OR)
 *                                'master_data.product.write'] }
 *
 * Bypass: scopes=["*"] (admin/owner roles) always pass through.
 * Redirect: unauthorized users are sent to /dashboard.
 */
export const permissionGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const required: string | string[] | undefined = route.data['requiredPermission'];

  // No restriction declared on this route — pass through
  if (!required) return true;

  const permissions = authService.permissions();

  // Wildcard bypass — admin/owner receive scopes=["*"]
  if (permissions.includes('*')) return true;

  // OR semantics: any matching slug grants access
  const slugs = Array.isArray(required) ? required : [required];
  if (slugs.some(slug => permissions.includes(slug))) return true;

  console.warn(
    `[PermissionGuard] 🚫 Denied → required: [${slugs.join(' | ')}] | has: [${permissions.slice(0, 8).join(', ')}]`
  );
  return router.parseUrl('/dashboard');
};
