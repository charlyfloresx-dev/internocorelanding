import { HttpInterceptorFn, HttpRequest, HttpHandlerFn, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

export const idempotencyInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn
): Observable<HttpEvent<unknown>> => {
  
  // Only apply Idempotency to POST, PUT, DELETE methods
  const isMutatingMethod = ['POST', 'PUT', 'DELETE'].includes(req.method.toUpperCase());
  
  // Specific critical endpoints that require strict idempotency (e.g. transfers, checkouts)
  const isCriticalPath = req.url.includes('/checkout') || 
                         req.url.includes('/transfer') || 
                         req.url.includes('/pos_checkout') ||
                         req.url.includes('/wms/') ||
                         req.url.includes('/receive');

  if (isMutatingMethod && isCriticalPath && !req.headers.has('Idempotency-Key')) {
    const idempotencyKey = crypto.randomUUID();
    
    const clonedReq = req.clone({
      headers: req.headers.set('Idempotency-Key', idempotencyKey)
    });
    
    return next(clonedReq);
  }

  return next(req);
};
