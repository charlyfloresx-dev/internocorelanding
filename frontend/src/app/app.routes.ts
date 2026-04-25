import {Routes} from '@angular/router';
import {authGuard, handshakeGuard} from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./modules/auth/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'onboarding',
    loadComponent: () => import('./modules/auth/onboarding.component').then(m => m.OnboardingComponent)
  },
  {
    path: 'auth/select-company',
    canActivate: [handshakeGuard],
    loadComponent: () => import('./modules/auth/tenant-selection.component').then(m => m.TenantSelectionComponent)
  },
  {
    path: 'select-company',
    canActivate: [handshakeGuard],
    loadComponent: () => import('./modules/auth/tenant-selection.component').then(m => m.TenantSelectionComponent)
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./shared/layouts/main-layout.component').then(m => m.MainLayoutComponent),
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./modules/dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'monitor/resources',
        loadComponent: () => import('./modules/monitor/resource-monitor.component').then(m => m.ResourceMonitorComponent)
      },
      {
        path: 'inventory',
        children: [
          {
            path: 'dashboard',
            loadComponent: () => import('./modules/inventory/inventory-dashboard.component').then(m => m.InventoryDashboardComponent)
          },
          {
            path: 'documents',
            children: [
              {
                path: '',
                loadComponent: () => import('./modules/inventory/inventory-documents.component').then(m => m.InventoryDocumentsComponent)
              },
              {
                path: 'new',
                loadComponent: () => import('./modules/inventory/components/inventory-document/inventory-document.component').then(m => m.InventoryDocumentComponent)
              },
              {
                path: ':id',
                loadComponent: () => import('./modules/inventory/components/inventory-document/inventory-document.component').then(m => m.InventoryDocumentComponent)
              }
            ]
          },
          {
            path: 'transfers',
            loadComponent: () => import('./modules/inventory/inventory-transfer.component').then(m => m.InventoryTransferComponent)
          },
          {
            path: 'inbound',
            loadComponent: () => import('./modules/inventory/inventory-inbound.component').then(m => m.InventoryInboundComponent)
          },
          {
            path: 'picking',
            loadComponent: () => import('./modules/inventory/inventory-picking.component').then(m => m.InventoryPickingComponent)
          },
          {
            path: 'shipping',
            loadComponent: () => import('./modules/inventory/inventory-shipping.component').then(m => m.InventoryShippingComponent)
          },
          {
            path: 'put-away', // Phase 42.8: Relocation Handheld
            loadComponent: () => import('./modules/inventory/inventory-put-away.component').then(m => m.InventoryPutAwayComponent)
          },
          {
            path: 'cycle-count', // Phase 49: Auditoría Spot
            loadComponent: () => import('./modules/inventory/cycle-count.component').then(m => m.CycleCountComponent)
          },
          {
            path: 'stock',
            loadComponent: () => import('./modules/inventory/stock-level.component').then(m => m.StockLevelComponent)
          },
          {
            path: 'receive',
            loadComponent: () => import('./modules/inventory/components/receive-material/receive-material.component').then(m => m.ReceiveMaterialComponent)
          }
        ]
      },
      {
        path: 'catalog',
        children: [
          {
            path: '',
            loadComponent: () => import('./modules/catalog/product-catalog.component').then(m => m.ProductCatalogComponent)
          },
          {
            path: 'uom',
            loadComponent: () => import('./modules/catalog/uom-catalog.component').then(m => m.UomCatalogComponent)
          },
          {
            path: 'categories',
            loadComponent: () => import('./modules/catalog/category-brand-catalog.component').then(m => m.CategoryBrandCatalogComponent)
          },
          {
            path: 'warehouses',
            loadComponent: () => import('./modules/catalog/warehouse-catalog.component').then(m => m.WarehouseCatalogComponent)
          },
          {
            path: 'concepts',
            loadComponent: () => import('./modules/catalog/concept-catalog.component').then(m => m.ConceptCatalogComponent)
          },
          {
            path: 'partners',
            loadComponent: () => import('./modules/catalog/partner-catalog.component').then(m => m.PartnerCatalogComponent)
          }
        ]
      },
      {
        path: 'production',
        children: [
          {
            path: 'dashboard',
            loadComponent: () => import('./modules/production/dashboard/production-dashboard.component').then(m => m.ProductionDashboardComponent)
          }
        ]
      },
      {
        path: 'admin',
        children: [
          {
            path: 'users',
            loadComponent: () => import('./modules/admin/user-management.component').then(m => m.UserManagementComponent)
          },
          {
            path: 'staff',
            loadComponent: () => import('./modules/admin/staff-management.component').then(m => m.StaffManagementComponent)
          }
        ]
      },
      {
        path: 'investments',
        children: [
          {
            path: 'asset-manager',
            loadComponent: () => import('./modules/investments/asset-manager/pages/kanban-dashboard/kanban-dashboard').then(m => m.KanbanDashboardComponent)
          }
        ]
      },
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      }
    ]
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];
