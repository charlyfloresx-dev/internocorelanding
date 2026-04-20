import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '@services/auth.service';
import { AdminAuthService } from '@services/admin-auth.service';
import { environment } from '../../../environments/environment';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const adminAuthService = inject(AdminAuthService);
  const router = inject(Router);
  const context = authService.currentContext();
  const masterKey = adminAuthService.getMasterKey();

  // Prioridad 1: Token de sesión activa (T2) - access_token guardado en localStorage
  // Prioridad 2: Token temporal de handshake (T1) - selection_token en sessionStorage
  const accessToken = context?.access_token;
  // Usar signal o sessionStorage para el token de selección
  const selectionToken = authService.selectionToken() || sessionStorage.getItem('selection_token');
  const token = accessToken || selectionToken || '';
  const companyId = context?.companyId || authService.activeCompanyId();

  const traceId = crypto.randomUUID();
  let headersConfig: { [header: string]: string } = {
    'x-trace-id': traceId,
    'x-correlation-id': traceId
  };

  if (token) {
    headersConfig['authorization'] = `Bearer ${token}`;
  }

  if (masterKey) {
    headersConfig['x-admin-master-key'] = masterKey;
  }

  // Handshake: Mantener la lógica de X-Selection-Token solo para la ruta de selección
  if (req.url.endsWith('/auth/select-company') && selectionToken) {
    headersConfig['x-selection-token'] = selectionToken;
  }

  // Inyección de X-Company-Id movida a multi-tenant.interceptor.ts


  console.log(`[AuthInterceptor] 🚀 Outgoing: ${req.url} | Trace: ${traceId} | Tenant: ${headersConfig['x-company-id'] || 'NONE'}`);

  const authReq = req.clone({ setHeaders: headersConfig });

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // CORRECCIÓN DE AUDITORÍA: Si la selección de empresa falla con 400 (Bad Request),
      // no se debe hacer logout. Se debe dejar que el componente que hizo la llamada
      // maneje el error y muestre un mensaje al usuario, evitando el "rebote".
      if (req.url.includes('/auth/select-company') && error.status === 400) {
        return throwError(() => error);
      }

      // 🛡️ RESILIENCIA DE DATOS: Aislamiento de fallos en microservicios
      // Si falla Master Data o WMS (500 o 0), NO cerrar sesión.
      const isDataService = req.url.includes(environment.masterDataUrl) || req.url.includes(environment.wmsUrl);

      if (isDataService && (error.status === 0 || error.status === 500)) {
        console.warn(`[Service Unavailable]: ${req.url}`);
        return throwError(() => error);
      }

      // 🛡️ KILL SWITCH: Solo cerrar sesión si es un fallo de identidad (401)
      if (error.status === 401) {
        console.error('⛔ Acceso denegado (Token inválido o expirado). Cerrando sesión.');
        authService.logout();
        router.navigate(['/login']);
      }
      return throwError(() => error);
    })
  );
};