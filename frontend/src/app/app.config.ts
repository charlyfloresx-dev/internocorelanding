import { ApplicationConfig, provideExperimentalZonelessChangeDetection } from '@angular/core';
import { provideRouter, withHashLocation } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';

import { authInterceptor } from '@core/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideExperimentalZonelessChangeDetection(),
    provideRouter(routes, withHashLocation()),
    provideHttpClient(
      withInterceptors([
        authInterceptor
      ])
    )
  ]
};