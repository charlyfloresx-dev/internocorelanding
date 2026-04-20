import { Routes } from '@angular/router';
import { KioskLayoutComponent } from './shared/components/layout/kiosk-layout.component';

export const routes: Routes = [
  {
    path: '',
    component: KioskLayoutComponent,
    children: [
      {
        path: 'approval',
        loadComponent: () => import('./modules/swipe/pages/approval-page.component').then(m => m.ApprovalPageComponent),
        title: 'Interno Core - Aprobación'
      },
      {
        path: 'gallery',
        loadComponent: () => import('./modules/swipe/pages/approval-page.component').then(m => m.ApprovalPageComponent), // Temporal
        title: 'Interno Core - Galería'
      },
      {
        path: 'checkout',
        loadComponent: () => import('./modules/checkout/pages/checkout-page.component').then(m => m.CheckoutPageComponent),
        title: 'Interno Core - Checkout'
      },
      {
        path: 'setup',
        loadComponent: () => import('./modules/setup/pages/setup-page.component').then(m => m.SetupPageComponent),
        title: 'Interno Core - Setup'
      },
      {
        path: 'staff',
        loadComponent: () => import('./modules/staff/pages/staff-dashboard-page.component').then(m => m.StaffDashboardPageComponent),
        title: 'Interno Core - Staff Dashboard'
      },
      {
        path: '',
        redirectTo: 'setup',
        pathMatch: 'full'
      }
    ]
  }
];
