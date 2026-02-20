import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '@services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const context = authService.currentContext();

  // Prioridad 1: Token de sesión activa (T2) - access_token guardado en localStorage
  // Prioridad 2: Token temporal de handshake (T1) - selection_token en sessionStorage
  const accessToken = context?.access_token;
  // Usar signal o sessionStorage para el token de selección
  const selectionToken = authService.selectionToken() || sessionStorage.getItem('selection_token');
  const token = accessToken || selectionToken || '';
  const companyId = context?.companyId || authService.activeCompanyId();

  let headersConfig: { [header: string]: string } = {};

  if (token) {
    headersConfig['authorization'] = `Bearer ${token}`;
  }

  // Handshake: Mantener la lógica de X-Selection-Token solo para la ruta de selección
  if (req.url.endsWith('/auth/select-company') && selectionToken) {
    headersConfig['x-selection-token'] = selectionToken;
  }

  // Inyección: Solo añade X-Company-Id si el usuario ya está autenticado y la empresa está seleccionada.
  // Exclusión: Si la URL incluye /auth/login, no debe añadir X-Company-Id.
  const isLogin = req.url.includes('/auth/login');
  if (companyId && !isLogin) {
    headersConfig['x-company-id'] = companyId.toString();
  }

  console.log(`[AuthInterceptor] 🚀 Outgoing: ${req.url} | Tenant: ${headersConfig['x-company-id'] || 'NONE'}`);

  const authReq = req.clone({ setHeaders: headersConfig });

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // 🛡️ KILL SWITCH: 401 (Unauthorized) o 0 (Network Error/Server Down)
      if (error.status === 401 || error.status === 0) {
        console.error('⛔ Acceso denegado o error de red crítico. Cerrando sesión.');
        // Usamos logoutQuiet o logout según la implementación del servicio, 
        // asumiendo logout() para limpieza total
        authService.logout(); 
        router.navigate(['/login']);
      }
      return throwError(() => error);
    })
  );
};