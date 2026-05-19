import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { GodModeStore } from '../stores/god-mode.store';

// Runs LAST in the interceptor chain so it has the final say on Authorization.
// multiTenantInterceptor always overwrites Authorization — if this ran first, the
// session token would win. Being last guarantees the god-mode token reaches the backend.
export const godModeInterceptor: HttpInterceptorFn = (req, next) => {
  const store = inject(GodModeStore);

  if (!store.isActive() || !store.token()) {
    return next(req);
  }

  const godReq = req.clone({
    setHeaders: { Authorization: `Bearer ${store.token()}` },
  });
  return next(godReq);
};