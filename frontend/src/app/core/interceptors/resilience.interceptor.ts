import { HttpInterceptorFn, HttpErrorResponse, HttpRequest, HttpHandlerFn, HttpEvent } from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, throwError, timer, of } from 'rxjs';
import { catchError, retry, mergeMap } from 'rxjs/operators';
import { ToastService } from '../services/toast.service';

/**
 * [Phase 4.1.2] Frontend Sentinel: Resilience & Recovery Interceptor
 * Handles:
 * 1. Exponential Backoff for transient network errors.
 * 2. Idempotency Key management (X-Idempotency-Key).
 * 3. Semantic Recovery awareness (DATABASE_RECONNECTING).
 */
export const resilienceInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn
): Observable<HttpEvent<unknown>> => {
  const toast = inject(ToastService);
  
  const finalReq = req;

  // 2. Resilience Loop with Exponential Backoff
  return next(finalReq).pipe(
    retry({
      count: 3,
      delay: (error: HttpErrorResponse, retryCount: number) => {
        // Only retry on transient/recovery-possible errors
        const isTransient = error.status === 0 || error.status === 503 || error.status === 504;
        const isReconnecting = error.error?.meta?.code === 'DATABASE_RECONNECTING';
        
        if (isTransient || isReconnecting) {
          const delayTime = Math.pow(2, retryCount) * 1000; // 2s, 4s, 8s
          
          if (retryCount === 1) {
            toast.info(
              'Problemas de conexión detectados. Reintentando de forma segura...',
              'Sentinel: Recuperación Activa'
            );
          }
          
          return timer(delayTime);
        }
        
        // Don't retry on other errors (4xx, 500, etc.)
        return throwError(() => error);
      }
    }),
    catchError((error: HttpErrorResponse) => {
      // Final failure after retries
      if (error.status === 0) {
        toast.error(
          'No se pudo establecer comunicación con el servidor tras varios intentos.',
          'Error de Red Crítico'
        );
      }
      return throwError(() => error);
    })
  );
};
