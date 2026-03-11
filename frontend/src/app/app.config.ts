import { ApplicationConfig, provideExperimentalZonelessChangeDetection } from '@angular/core';
import { provideRouter, withHashLocation } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';

import { authInterceptor } from '@core/interceptors/auth.interceptor';
import { multiTenantInterceptor } from '@core/interceptors/multi-tenant.interceptor';
import { apiInterceptor } from '@core/interceptors/api.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideExperimentalZonelessChangeDetection(),
    provideRouter(routes, withHashLocation()),
    provideHttpClient(
      withInterceptors([
        authInterceptor,
        multiTenantInterceptor,
        apiInterceptor
      ])
    )
  ]
};