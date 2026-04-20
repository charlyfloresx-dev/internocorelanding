import {inject, PLATFORM_ID} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {CanActivateFn, Router} from '@angular/router';
import {AuthService} from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const platformId = inject(PLATFORM_ID);
  const isBrowser = isPlatformBrowser(platformId);

  // 1. In-memory check (Fast Path)
  const isAuth = authService.isAuthenticated();

  // 2. Zero Trust Validation (Direct Storage Check)
  if (isBrowser) {
    const savedSession = localStorage.getItem('auth_session');
    const savedCtx = localStorage.getItem('_ic_auth_ctx');
    
    // If memory says YES but Storage says NO -> Zero Trust Violation
    if (!savedSession || !savedCtx) {
      console.warn('[AuthGuard] 🚫 Zero Trust Violation: Storage missing. Redirecting to login.');
      authService.logout(); // Cleanup signals and redirect
      return router.parseUrl('/login');
    }

    try {
      const session = JSON.parse(savedSession);
      const ctx = JSON.parse(savedCtx);
      
      if (!session.access_token || !ctx.access_token) {
        console.warn('[AuthGuard] 🚫 Zero Trust Violation: Tokens missing. Redirecting to login.');
        authService.logout();
        return router.parseUrl('/login');
      }
    } catch (e) {
      console.error('[AuthGuard] 🚫 Zero Trust Violation: Corrupted legacy storage.');
      authService.logout();
      return router.parseUrl('/login');
    }
  }

  // 3. Final safety check on signals
  if (isAuth) {
    return true;
  }

  // FAIL-SAFE: If authentication service is in a partial state, force login
  return router.parseUrl('/login');
};

export const handshakeGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const platformId = inject(PLATFORM_ID);
  const isBrowser = isPlatformBrowser(platformId);

  if (authService.authStep() === 'handshake' || (isBrowser && sessionStorage.getItem('_ic_selection_token'))) {
    return true;
  }

  return router.parseUrl('/login');
};
