import { Routes } from '@angular/router';

export const PRODUCTION_ROUTES: Routes = [
  // Rutas futuras de producción
  {
    path: '**',
    redirectTo: '/dashboard'
  }
];