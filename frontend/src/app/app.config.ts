import {ApplicationConfig, provideZonelessChangeDetection, APP_INITIALIZER} from '@angular/core';
import {provideRouter} from '@angular/router';
import {provideHttpClient, withInterceptors, withFetch} from '@angular/common/http';

import {routes} from './app.routes';
import {AuthService} from './core/services/auth.service';
import { multiTenantInterceptor } from './core/interceptors/multi-tenant.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';
import { imageInterceptor } from './core/interceptors/image.interceptor';

export function initializeApp(authService: AuthService) {
  return () => authService.restoreSession();
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([multiTenantInterceptor, errorInterceptor, imageInterceptor]),
      withFetch()
    ),
    {
      provide: APP_INITIALIZER,
      useFactory: initializeApp,
      deps: [AuthService],
      multi: true
    }
  ],
};

