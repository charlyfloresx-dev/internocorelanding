import {HttpInterceptorFn} from '@angular/common/http';

/**
 * DEPRECATED: Consolidated into multi-tenant.interceptor.ts
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req);
};
