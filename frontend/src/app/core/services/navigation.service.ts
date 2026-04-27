import {Injectable, signal, computed, inject, PLATFORM_ID} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {AuthService} from './auth.service';
import {TranslationService} from './translation.service';

export interface SubMenuItem {
  id: string;
  label: string;
  translation_key?: string;
  route: string;
  permissions?: string[];
}

export interface MenuItem {
  id: string;
  label: string;
  translation_key?: string;
  icon: string;
  route?: string;
  permissions?: string[];
  subItems?: SubMenuItem[];
}

@Injectable({
  providedIn: 'root'
})
export class NavigationService {
  private authService = inject(AuthService);
  private translationService = inject(TranslationService);
  private platformId = inject(PLATFORM_ID);
  private isBrowser = isPlatformBrowser(this.platformId);

  // Master Blueprint
  private readonly blueprint: MenuItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      translation_key: 'menu.dashboard',
      icon: 'show_chart',
      route: '/dashboard'
    },
    {
      id: 'production',
      label: 'Producción',
      translation_key: 'menu.production',
      icon: 'precision_manufacturing',
      permissions: ['mes:admin', 'production:manage'],
      subItems: [
        { id: 'prod-dash', label: 'Dashboard Producción', translation_key: 'menu.production_dashboard', route: '/production/dashboard' },
        { id: 'prod-monitor', label: 'Monitor de Línea', translation_key: 'menu.production_monitor', route: '/monitor/resources' },
        { id: 'prod-orders', label: 'Órdenes de Trabajo', translation_key: 'menu.production_lines', route: '/production/orders' }
      ]
    },
    {
      id: 'inventory',
      label: 'Inventarios',
      translation_key: 'menu.inventory',
      icon: 'inventory_2',
      permissions: ['inv:movements:manage', 'inv:warehouse:manage', 'inventory:admin'],
      subItems: [
        { id: 'inv-dash', label: 'Dashboard Global', translation_key: 'menu.inventory_dashboard', route: '/inventory/dashboard' },
        { id: 'inv-stock', label: 'Stock por Almacén', translation_key: 'menu.inventory_stock', route: '/inventory/stock' },
        { id: 'inv-receive', label: 'Recibir Materiales', translation_key: 'menu.inventory_receive', route: '/inventory/receive' },
        { id: 'inv-docs', label: 'Movimientos', translation_key: 'menu.inventory_documents', route: '/inventory/documents' },
        { id: 'inv-trans', label: 'Transferencias ICT', translation_key: 'menu.inventory_transfers', route: '/inventory/transfers' },
        { id: 'inv-cycle', label: 'Auditoría Spot', translation_key: 'menu.inventory_cycle_count', route: '/inventory/cycle-count' },
        { id: 'inv-audit', label: 'Forensic Audit', translation_key: 'menu.inventory_audit', route: '/inventory/audit' }
      ]
    },
    {
      id: 'catalog',
      label: 'Catálogo',
      translation_key: 'menu.catalog',
      icon: 'category',
      permissions: ['master:catalog:manage', 'catalog:admin'],
      subItems: [
        { id: 'cat-master', label: 'Catálogo Maestro', translation_key: 'menu.catalog_master', route: '/catalog' },
        { id: 'cat-uom', label: 'Unidades de Medida', translation_key: 'menu.catalog_uom', route: '/catalog/uom' },
        { id: 'cat-categories', label: 'Categorías y Marcas', translation_key: 'menu.catalog_categories', route: '/catalog/categories' },
        { id: 'cat-warehouses', label: 'Almacenes', translation_key: 'menu.catalog_warehouses', route: '/catalog/warehouses' },
        { id: 'cat-concepts', label: 'Conceptos', translation_key: 'menu.catalog_concepts', route: '/catalog/concepts' },
        { id: 'cat-partners', label: 'Socios de Negocio', translation_key: 'menu.catalog_partners', route: '/catalog/partners' }
      ]
    },
    {
      id: 'wms',
      label: 'WMS / Logística',
      translation_key: 'menu.wms',
      icon: 'conveyor_belt',
      permissions: ['wms:admin', 'wms:manage', 'inv:warehouse:manage'],
      subItems: [
        { id: 'wms-receiving', label: 'Recibo', translation_key: 'menu.wms_receiving', route: '/inventory/inbound' },
        { id: 'wms-picking', label: 'Picking', translation_key: 'menu.wms_picking', route: '/inventory/picking' },
        { id: 'wms-putaway', label: 'Put-Away', translation_key: 'menu.wms_putaway', route: '/inventory/put-away' },
        { id: 'wms-cycle', label: 'Conteo Cíclico', translation_key: 'menu.wms_cycle_count', route: '/inventory/cycle-count' },
        { id: 'wms-shipping', label: 'Embarques', translation_key: 'menu.wms_shipping', route: '/inventory/shipping' }
      ]
    },
    {
      id: 'investments',
      label: 'Inversiones (CRM)',
      translation_key: 'menu.investments',
      icon: 'real_estate_agent',
      permissions: ['investments:manage', 'investments:admin'],
      subItems: [
        { id: 'inv-kanban', label: 'Kanban Dashboard', translation_key: 'menu.investments_kanban', route: '/investments/asset-manager' }
      ]
    },
    {
      id: 'system',
      label: 'Sistema',
      translation_key: 'menu.settings',
      icon: 'settings',
      permissions: ['admin', 'auth:user:manage', 'auth:roles:manage'],
      subItems: [
        { id: 'sys-users', label: 'Usuarios', translation_key: 'menu.settings_users', route: '/admin/users' },
        { id: 'sys-staff', label: 'Personal de Planta', translation_key: 'menu.settings_staff', route: '/admin/staff' },
        { id: 'sys-config', label: 'Configuración', translation_key: 'menu.settings_system', route: '/system/config' }
      ]
    }
  ];

  // Helper to translate items
  translateLabel(item: MenuItem | SubMenuItem): string {
    return this.translationService.translate(item.translation_key || '', item.label);
  }

  // Signal for filtered menu items based on RBAC
  menuItems = computed(() => {
    const permissions = this.authService.permissions();
    const roles = this.authService.roles();
    const isAuthenticated = this.authService.isAuthenticated();

    if (!isAuthenticated) return [];

    console.log('[NavigationService] 🛠 Calculating menu for:', { roles, permissions });

    // Admin bypass - check for 'admin' in roles or permissions
    const isAdmin = roles.some((r: string) => r.toLowerCase().includes('admin')) || 
                    permissions.some((p: string) => p.toLowerCase().includes('admin') || p === '*' || p === 'auth:user:manage');

    // Filter items
    const filtered = this.blueprint.filter(item => {
      // Always show items without permissions (like Dashboard)
      if (!item.permissions || item.permissions.length === 0) return true;
      
      // Show everything for admins
      if (isAdmin) {
        console.log(`[NavigationService] ✅ Admin Bypass for: ${item.id}`);
        return true;
      }
      
      const hasPermission = item.permissions.some((p: string) => permissions.includes(p));
      console.log(`[NavigationService] Checking item: ${item.id}`, { required: item.permissions, userHas: permissions, allowed: hasPermission });
      return hasPermission;
    });

    // FAIL-SAFE: If results are empty but user is authenticated, at least show Dashboard
    if (filtered.length === 0 && isAuthenticated) {
      console.warn('[NavigationService] ⚠️ No menu items allowed by RBAC. Forcing Dashboard (Fail-Safe).');
      return this.blueprint.filter(item => item.id === 'dashboard');
    }

    return filtered;
  });

  // State for active submenu
  activeSubMenuId = signal<string | null>(null);

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
}
