// temp_future/src/app/modules/billing/billing.routes.ts
import { Routes } from '@angular/router';

export const BILLING_ROUTES: Routes = [
  {
    path: 'subscription',
    loadComponent: () => import('./pages/subscription/subscription.component').then(m => m.SubscriptionComponent)
  }
];
