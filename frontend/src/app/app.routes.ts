import {Routes} from '@angular/router';
import {authGuard, handshakeGuard} from './core/guards/auth.guard';
import {permissionGuard} from './core/guards/permission.guard';

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
        loadComponent: () => import('./modules/monitor/resource-selector.component').then(m => m.ResourceSelectorComponent)
      },
      {
        path: 'monitor/resources/:code',
        loadComponent: () => import('./modules/monitor/resource-monitor.component').then(m => m.ResourceMonitorComponent)
      },
      {
        path: 'monitor/tickets',
        canActivate: [permissionGuard],
        data: { requiredPermission: ['tickets:read', 'tickets.view', 'tickets.assign', 'admin.user.manage'] },
        loadComponent: () => import('./modules/monitor/tickets/tickets-dashboard.component').then(m => m.TicketsDashboardComponent)
      },
      {
        path: 'monitor/flows',
        loadComponent: () => import('./modules/monitor/flows/industrial-flows.component').then(m => m.IndustrialFlowsComponent)
      },
      {
        path: 'inventory',
        canActivate: [permissionGuard],
        data: { requiredPermission: ['inventory.stock.read', 'inventory:read', 'inventory.document.create', 'inventory.document.approve', 'inventory.audit.view'] },
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
            path: 'pending-putaway',
            loadComponent: () => import('./modules/inventory/pending-putaway.component').then(m => m.PendingPutawayComponent)
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
          },
          {
            path: 'audit',
            canActivate: [permissionGuard],
            data: { requiredPermission: 'inventory.audit.view' },
            loadComponent: () => import('./modules/inventory/inventory-audit.component').then(m => m.InventoryAuditComponent)
          }
        ]
      },
      {
        path: 'catalog',
        canActivate: [permissionGuard],
        data: { requiredPermission: ['master_data.product.write', 'master_data.product.read'] },
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
          },
          {
            path: 'item-config',
            canActivate: [permissionGuard],
            data: { requiredPermission: ['master_data:write', 'admin.user.manage'] },
            loadComponent: () => import('./modules/production/item-config/mes-item-config.component').then(m => m.MesItemConfigComponent)
          },
          {
            path: 'config',
            children: [
              {
                path: 'resources',
                canActivate: [permissionGuard],
                data: { requiredPermission: ['admin.user.manage', 'master_data:write'] },
                loadComponent: () => import('./modules/production/config/resource-config.component').then(m => m.ResourceConfigComponent)
              },
              {
                path: 'shifts',
                canActivate: [permissionGuard],
                data: { requiredPermission: ['admin.user.manage', 'master_data:write'] },
                loadComponent: () => import('./modules/production/config/shift-config.component').then(m => m.ShiftConfigComponent)
              }
            ]
          }
        ]
      },
      {
        path: 'admin',
        canActivate: [permissionGuard],
        data: { requiredPermission: 'admin.user.manage' },
        children: [
          {
            path: 'users',
            loadComponent: () => import('./modules/admin/user-management.component').then(m => m.UserManagementComponent)
          },
          {
            path: 'staff',
            loadComponent: () => import('./modules/admin/staff-management.component').then(m => m.StaffManagementComponent)
          },
          {
            path: 'forensic',
            loadComponent: () => import('./modules/admin/forensic-dashboard.component').then(m => m.ForensicDashboardComponent)
          },
          {
            path: 'system-control',
            loadComponent: () => import('./modules/admin/system-control.component').then(m => m.SystemControlComponent)
          },
          {
            path: 'whatsapp',
            loadComponent: () => import('./modules/admin/whatsapp-gateway.component').then(m => m.WhatsAppGatewayComponent)
          }
        ]
      },
      {
        path: 'investments',
        children: [
          {
            path: 'asset-manager',
            children: [
              {
                path: '',
                loadComponent: () => import('./modules/investments/asset-manager/pages/kanban-dashboard/kanban-dashboard').then(m => m.KanbanDashboardComponent)
              },
              {
                path: 'price-map',
                loadComponent: () => import('./modules/investments/asset-manager/pages/price-map/price-map').then(m => m.PriceMapComponent)
              },
              {
                path: ':id',
                loadComponent: () => import('./modules/investments/asset-manager/pages/asset-detail/asset-detail').then(m => m.AssetDetailComponent)
              }
            ]
          }
        ]
      },
      {
        path: 'billing',
        loadChildren: () => import('./modules/billing/billing.routes').then(m => m.BILLING_ROUTES)
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
