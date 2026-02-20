import '@angular/compiler';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideExperimentalZonelessChangeDetection } from '@angular/core';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';

// Combinamos la config sin duplicar proveedores de detección de cambios
bootstrapApplication(AppComponent, {
  ...appConfig,
  providers: [
    ...(appConfig.providers || []),
    provideExperimentalZonelessChangeDetection()
  ]
}).catch((err) => console.error(err));