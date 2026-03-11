import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { tenantGuard } from './core/guards/tenant.guard';
import { godModeGuard } from './core/guards/god-mode.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./modules/auth/login.component').then(m => m.LoginComponent)
  },
  // RUTAS PROTEGIDAS CON LAYOUT (Sidebar + Header)
  {
    path: '',
    // VERIFICACIÓN: Asegúrate que el archivo esté en src/app/layout/main-layout.component.ts
    loadComponent: () => import('./layout/main-layout.component').then(m => m.MainLayoutComponent),
    canActivate: [authGuard, tenantGuard],
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
      {
        path: 'dashboard',
        loadComponent: () => import('./modules/home/general-dashboard.component').then(m => m.GeneralDashboardComponent)
      },
      {
        path: 'inventory',
        loadChildren: () => import('./modules/inventory/inventory.routes').then(m => m.INVENTORY_ROUTES)
      },
      {
        path: 'production',
        loadChildren: () => import('./modules/production/production.routes').then(m => m.PRODUCTION_ROUTES)
      },
      {
        path: 'catalog',
        loadChildren: () => import('./modules/catalog/catalog.routes').then(m => m.CATALOG_ROUTES)
      },
      {
        path: 'tickets',
        loadChildren: () => import('./modules/tickets/tickets.routes').then(m => m.TICKETS_ROUTES)
      },
      {
        path: 'admin/god-mode',
        loadComponent: () => import('./modules/admin/admin-god-mode.component').then(m => m.AdminGodModeComponent),
        canActivate: [godModeGuard]
      }
    ]
  },
  {
    path: 'setup-wizard',
    loadComponent: () => import('./modules/onboarding/onboarding-wizard.component').then(m => m.OnboardingWizardComponent),
    canActivate: [authGuard, tenantGuard]
  },
  {
    path: 'onboarding/setup-warehouse',
    loadComponent: () => import('./modules/onboarding/setup-warehouse.component').then(m => m.SetupWarehouseComponent),
    canActivate: [authGuard, tenantGuard]
  },
  {
    path: '**',
    redirectTo: 'login'
  }
];