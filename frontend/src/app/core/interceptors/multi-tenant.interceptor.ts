// temp_future/src/app/core/interceptors/multi-tenant.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { DashboardService } from '../services/dashboard.service';
import { catchError, throwError, tap, filter, take, switchMap } from 'rxjs';
import { ToastService } from '../services/toast.service';

// Emitted to refreshTokenSubject when refresh fails — unblocks waiting requests
// so they don't hang on filter(token !== null) when the primary refresh errors out.
const REFRESH_ABORT = '__ABORT__';

/**
 * Strict Multi-tenant Interceptor
 * Injects X-Company-ID and handles unauthorized access.
 */
export const multiTenantInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const dashboard = inject(DashboardService);
  const toast = inject(ToastService);

  // 1. Resolve Access Token
  let token = auth.session()?.access_token;
  if (!token && auth.isBrowser) {
    const storedCtx = localStorage.getItem('_ic_auth_ctx');
    if (storedCtx) {
      try {
        const ctx = JSON.parse(storedCtx);
        token = ctx.access_token;
      } catch {}
    }
  }

  // 2. Resolve Company ID
  let companyId = auth.activeCompanyId();
  let userId = auth.currentUser()?.id;
  
  if ((!companyId || !userId) && auth.isBrowser) {
    const storedCtx = localStorage.getItem('_ic_auth_ctx');
    if (storedCtx) {
      try {
        const ctx = JSON.parse(storedCtx);
        if (!companyId) companyId = ctx.company_id;
        if (!userId) userId = ctx.user_id;
      } catch {}
    }
  }

  // UUID Validation Helper
  const isValidUUID = (id: string | null): boolean => 
    !!id && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);

  let headers = req.headers;

  // Exclude auth routes from context injection to prevent handshake interference
  const url = req.url.toLowerCase();
  const isHandshake = url.includes('/login') || url.includes('/handshake');
  const isSelection = url.includes('/select-company');
  const isMeValidation = url.includes('/auth/me'); // Core validation point
  const isDelegate = url.includes('/auth/delegate-selection');
  const isAuthRoute = (isHandshake || isSelection || url.includes('/auth/')) && !isMeValidation && !isDelegate;

  // 3. Inject Authorization
  if (isHandshake) {
    // SECURITY: Fresh login/handshake MUST have no headers to avoid stale context rejection
    headers = headers.delete('Authorization');
    headers = headers.delete('authorization');
    headers = headers.delete('X-Selection-Token');
    headers = headers.delete('X-Company-ID');
    headers = headers.delete('x-company-id');
    headers = headers.delete('X-User-ID');
    headers = headers.delete('x-user-id');
  } else if (!isAuthRoute && token) {
    // Business routes: Inject current session token if not in an auth context
    headers = headers.set('Authorization', `Bearer ${token}`);
  }

  // 4. Inject Company Context (Strict UUID check)
  if (isAuthRoute) {
    // SECURITY: Never leak company context into auth/handshake/selection endpoints
    headers = headers.delete('X-Company-ID');
    headers = headers.delete('x-company-id');
    headers = headers.delete('X-User-ID');
    headers = headers.delete('x-user-id');
  } else {
    // Inject Company
    if (isValidUUID(companyId)) {
      headers = headers.set('X-Company-ID', companyId!);
    } else if (!req.url.includes('/public/')) {
      if (companyId) {
        console.warn(`[Security] Interceptor suppressed invalid/malformed Company ID: ${companyId}`);
      }
      headers = headers.delete('X-Company-ID');
      headers = headers.delete('x-company-id');
    }
    
    // Inject User ID
    if (isValidUUID(userId || null)) {
      headers = headers.set('X-User-ID', userId!);
    }
  }

  const authReq = req.clone({ headers });
  const startTime = Date.now();

  return next(authReq).pipe(
    tap(() => {
      const elapsed = Date.now() - startTime;
      dashboard.addLatencyPoint(elapsed);
      
      // Calculate approximate payload size
      const bodySize = req.body ? JSON.stringify(req.body).length : 0;
      dashboard.recordRequest(bodySize);
    }),
    catchError((error: HttpErrorResponse) => {
      // --- 🌍 BINATIONAL HARDENING (Phase 36.5) ---
      // Detect if customs documentation is required for the transaction
      const isCustomsRequired = error.status === 400 && 
        (error.error?.message?.toLowerCase().includes('customs') || 
         error.error?.meta?.error_code === 'CUSTOMS_REQUIRED');

      if (isCustomsRequired) {
        toast.error(
          'Documentación aduanera/pedimento faltante para esta operación binacional.', 
          'Error de Cumplimiento'
        );
      }

      // --- 💳 GRACE PERIOD & PAYMENT REQUIRED (Phase 19) ---
      if (error.status === 402) {
        toast.warning(
          error.error?.message || 'Suscripción restringida por falta de pago.',
          'Pago Requerido'
        );
      }

      // Logic for connectivity and auxiliary service failure resilience
      const isAuxiliaryService = req.url.includes('/currencies/') || req.url.includes('/health');
      
      if (isAuxiliaryService && error.status >= 500) {
        console.warn(`[Interceptor] Suppressed error from auxiliary service: ${req.url}`);
        // Return an empty data structure or a dummy response to keep the app flow alive
        // For GET requests, we can often just return an empty ApiResponse structure
        const dummyResponse = { status: 'success', data: null, message: 'Auxiliary service offline (Fail-Safe)' };
        return throwError(() => error); // Still throw, but we will catch in services
      }

      const isMockSession = auth.session()?.access_token?.includes('mock') || auth.session()?.user?.email?.includes('demo');
      const isAdminRoute = req.url.toLowerCase().includes('/admin/');
      
      // --- 🔄 TOKEN REFRESH FLOW (RTR) — 401 only ---
      // Semaphore pattern: only one refresh call fires at a time.
      // Concurrent 401s queue on refreshTokenSubject and get the new token when ready.
      // On refresh failure, REFRESH_ABORT is emitted so queued requests don't hang.
      if (error.status === 401 && !isMockSession && !isAuthRoute && !isAdminRoute) {
        if (!url.includes('/auth/refresh')) {
          if (auth.isRefreshing()) {
            // Queued branch: wait for the ongoing refresh to complete
            return auth.refreshTokenSubject.pipe(
              filter(t => t !== null),
              take(1),
              switchMap(t => {
                if (t === REFRESH_ABORT) {
                  return throwError(() => error);
                }
                // FIX: use authReq (has X-Company-ID, X-User-ID) not req
                const retryReq = authReq.clone({
                  headers: authReq.headers.set('Authorization', `Bearer ${t}`)
                });
                return next(retryReq);
              })
            );
          } else {
            // Primary branch: start the refresh
            auth.isRefreshing.set(true);
            auth.refreshTokenSubject.next(null);

            return auth.refreshToken().pipe(
              switchMap(resp => {
                auth.isRefreshing.set(false);
                if (resp.status === 'success' && resp.data) {
                  auth.setSession(resp.data);
                  auth.refreshTokenSubject.next(resp.data.access_token);
                  // FIX: use authReq to preserve X-Company-ID and X-User-ID headers
                  const retryReq = authReq.clone({
                    headers: authReq.headers.set('Authorization', `Bearer ${resp.data.access_token}`)
                  });
                  return next(retryReq);
                } else {
                  // Refresh returned non-success: unblock queue then logout
                  auth.refreshTokenSubject.next(REFRESH_ABORT);
                  auth.logout();
                  return throwError(() => error);
                }
              }),
              catchError((refreshErr) => {
                auth.isRefreshing.set(false);
                // FIX: emit REFRESH_ABORT so queued requests don't hang indefinitely
                auth.refreshTokenSubject.next(REFRESH_ABORT);
                auth.logout();
                return throwError(() => refreshErr);
              })
            );
          }
        } else {
          // /auth/refresh itself returned 401 — RTR family expired/revoked — full logout
          auth.logout();
        }
      }

      // --- 🚫 PERMISSION DENIED — 403: toast only, no logout ---
      if (error.status === 403 && !isAuthRoute) {
        toast.error('Acceso denegado. Permisos insuficientes para esta operación.', 'Sin Permisos');
      }
      return throwError(() => error);
    })
  );
};
