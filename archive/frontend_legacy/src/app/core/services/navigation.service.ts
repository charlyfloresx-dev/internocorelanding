import { Injectable, signal, computed, inject } from '@angular/core';
import { AuthService } from './auth.service';
import { TranslationService } from './translation.service';

export interface SubMenuItem {
  id: string;
  label: string;
  translation_key?: string;
  route: string;
  requiredRoles?: string[];
}

export interface MenuItem {
  id: string;
  label: string;
  translation_key?: string;
  icon: string;
  route?: string;
  requiredRoles?: string[];
  subItems?: SubMenuItem[];
}

@Injectable({
  providedIn: 'root'
})
export class NavigationService {
  private auth = inject(AuthService);
  private ts = inject(TranslationService);

  // State for active submenu (Fly-out)
  activeSubMenuId = signal<string | null>(null);

  // Blueprint (All possible items)
  private readonly blueprint: MenuItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      translation_key: 'menu.dashboard',
      icon: 'show_chart', // Industrial style
      route: '/dashboard',
      requiredRoles: ['admin', 'Admin Enterprise', 'operator', 'Operador de Inventario', 'inventory:admin', 'catalog:admin', 'production_mes:admin']
    },
    {
      id: 'production',
      label: 'Producción',
      translation_key: 'menu.production',
      icon: 'precision_manufacturing',
      requiredRoles: ['admin', 'Admin Enterprise', 'production_mes:admin'],
      subItems: [
        { id: 'prod-orders', label: 'Órdenes de Trabajo', translation_key: 'menu.production_lines', route: '/production/orders' }
      ]
    },
    {
      id: 'inventory',
      label: 'Inventarios',
      translation_key: 'menu.inventory',
      icon: 'inventory_2',
      requiredRoles: ['admin', 'Admin Enterprise', 'operator', 'Operador de Inventario', 'inventory:admin', 'inventory:read'],
      subItems: [
        { id: 'inv-dash', label: 'Resumen', translation_key: 'menu.inventory_dashboard', route: '/inventory' },
        { id: 'inv-docs', label: 'Documentos', translation_key: 'menu.inventory_documents', route: '/inventory/documents', requiredRoles: ['admin', 'Admin Enterprise', 'inventory:admin'] },
        { id: 'inv-warehouses', label: 'Almacenes', translation_key: 'menu.inventory_reports', route: '/inventory/warehouses', requiredRoles: ['admin', 'Admin Enterprise', 'inventory:admin'] },
        { id: 'inv-partners', label: 'Socios', translation_key: 'menu.inventory_reports', route: '/inventory/partners', requiredRoles: ['admin', 'Admin Enterprise', 'inventory:admin'] }
      ]
    },
    {
      id: 'catalog',
      label: 'Catálogo',
      translation_key: 'menu.catalog',
      icon: 'apps',
      requiredRoles: ['admin', 'Admin Enterprise', 'operator', 'catalog:admin'],
      subItems: [
        { id: 'cat-products', label: 'Productos', translation_key: 'menu.catalog_products', route: '/catalog/products' },
        { id: 'cat-uoms', label: 'Unidades de Medida', translation_key: 'menu.catalog_uoms', route: '/catalog/uoms', requiredRoles: ['admin', 'Admin Enterprise', 'catalog:admin'] },
        { id: 'cat-categories', label: 'Categorías', translation_key: 'menu.catalog_categories', route: '/catalog/categories', requiredRoles: ['admin', 'Admin Enterprise', 'catalog:admin'] },
        { id: 'cat-brands', label: 'Marcas', translation_key: 'menu.catalog_brands', route: '/catalog/brands', requiredRoles: ['admin', 'Admin Enterprise', 'catalog:admin'] }
      ]
    },
    {
      id: 'system',
      label: 'Sistema',
      translation_key: 'menu.settings',
      icon: 'settings',
      requiredRoles: ['admin', 'Admin Enterprise'],
      subItems: [
        { id: 'sys-snapshots', label: 'Snapshots', translation_key: 'menu.settings_system', route: '/system/snapshots' }
      ]
    }
  ];

  // Computed signal for filtered menu items
  menuItems = computed(() => {
    const permissions = this.auth.currentContext()?.permissions || [];
    const roleNames = permissions.length > 0 ? permissions : ['viewer'];

    return this.filterMenu(this.blueprint, roleNames);
  });

  private filterMenu(items: MenuItem[], roleNames: string[]): MenuItem[] {
    const isGlobalAdmin = roleNames.includes('admin') || roleNames.includes('Admin Enterprise');

    return items
      .filter(item => {
        if (isGlobalAdmin) return true;
        if (!item.requiredRoles || item.requiredRoles.length === 0) return true;
        return roleNames.some(role => item.requiredRoles?.includes(role));
      })
      .map(item => {
        if (item.subItems) {
          const filteredSub = item.subItems.filter(sub => {
            if (isGlobalAdmin) return true;
            if (!sub.requiredRoles || sub.requiredRoles.length === 0) return true;
            return roleNames.some(role => sub.requiredRoles?.includes(role));
          });
          if (filteredSub.length > 0 || item.route) {
            return { ...item, subItems: filteredSub };
          }
          return null;
        }
        return item;
      })
      .filter((item): item is MenuItem => item !== null);
  }

  // Legacy method for compatibility during transition
  generateMenu(roles: string[] = []) {
    // This is now handled by the menuItems computed signal
    console.log('[NavigationService] generateMenu called (legacy), using computed signal instead.');
  }

  toggleSubMenu(id: string) {
    if (this.activeSubMenuId() === id) {
      this.activeSubMenuId.set(null);
    } else {
      this.activeSubMenuId.set(id);
    }
  }

  closeSubMenu() {
    this.activeSubMenuId.set(null);
  }

  translateLabel(item: MenuItem | SubMenuItem): string {
    return this.ts.translate(item.translation_key || '', item.label);
  }
}
