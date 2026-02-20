import { Injectable, signal } from '@angular/core';

export interface MenuItem {
  id: string;
  title: string;
  icon: string;
  link?: string;
  children?: MenuItem[];
  requiredRoles?: string[]; // Roles necesarios para ver este item
}

@Injectable({
  providedIn: 'root'
})
export class NavigationService {
  // Signal para la reactividad del menú
  readonly menuItems = signal<MenuItem[]>([]);

  constructor() {
    // Inicialización automática para asegurar que el menú se muestre
    this.generateMenu([]);
  }

  generateMenu(roleNames: string[] = []): void {
    console.log('[NavigationService] 🚀 generateMenu invocado. Roles entrada:', roleNames);

    // === PROTECCIÓN DE CONTEXTO ===
    // Si recibimos roles débiles (vacío o 'viewer') que suelen venir de inicializaciones por defecto,
    // intentamos recuperar los permisos reales (scopes) del localStorage para no perder el menú.
    const isWeakRole = roleNames.length === 0 || (roleNames.length === 1 && roleNames[0] === 'viewer');

    if (isWeakRole) {
      try {
        const savedCtx = localStorage.getItem('interno_auth_ctx');
        if (savedCtx) {
          const ctx = JSON.parse(savedCtx);
          if (ctx.permissions && Array.isArray(ctx.permissions) && ctx.permissions.length > 0) {
            // Solo sobreescribimos si lo que hay en storage NO es 'viewer'
            const storedPerms = ctx.permissions;
            const isStoredWeak = storedPerms.length === 1 && storedPerms[0] === 'viewer';
            
            if (!isStoredWeak) {
              roleNames = storedPerms;
              console.log('[NavigationService] 🛡️ Contexto protegido. Ignorando rol débil:', isWeakRole, '-> Usando permisos de storage:', roleNames);
            }
          }
        }
      } catch (e) { console.warn('[NavigationService] Fallo al recuperar permisos locales', e); }
    }

    // Definición de la estructura de navegación con roles requeridos
    const allMenuItems: MenuItem[] = [
      {
        id: 'dashboard',
        title: 'Dashboard',
        icon: 'fas fa-chart-line',
        link: '/dashboard',
        requiredRoles: ['admin', 'Admin Enterprise', 'operator', 'Operador de Inventario', 'inventory:admin', 'catalog:admin', 'production_mes:admin'] // Todos pueden ver
      },
      {
        id: 'production',
        title: 'Producción',
        icon: 'fas fa-industry',
        requiredRoles: ['admin', 'Admin Enterprise', 'production_mes:admin'], // Solo admin
        children: [
          { id: 'prod-orders', title: 'Órdenes de Trabajo', icon: 'fas fa-clipboard-list', link: '/production/orders' }
        ]
      },
      {
        id: 'inventory',
        title: 'Inventarios',
        icon: 'fas fa-boxes-stacked',
        requiredRoles: ['admin', 'Admin Enterprise', 'operator', 'Operador de Inventario', 'inventory:admin', 'inventory:read'], // Todos
        children: [
          { id: 'inv-dash', title: 'Resumen', icon: 'fas fa-chart-pie', link: '/inventory' },
          { id: 'inv-docs', title: 'Documentos', icon: 'fas fa-file-invoice', link: '/inventory/documents', requiredRoles: ['admin', 'Admin Enterprise', 'inventory:admin'] },
          { id: 'inv-warehouses', title: 'Almacenes', icon: 'fas fa-warehouse', link: '/inventory/warehouses', requiredRoles: ['admin', 'Admin Enterprise', 'inventory:admin'] },
          { id: 'inv-partners', title: 'Socios', icon: 'fas fa-handshake', link: '/inventory/partners', requiredRoles: ['admin', 'Admin Enterprise', 'inventory:admin'] }
        ]
      },
      {
        id: 'catalog',
        title: 'Catálogo Maestro',
        icon: 'fa-solid fa-boxes-stacked',
        requiredRoles: ['admin', 'Admin Enterprise', 'operator', 'catalog:admin'],
        children: [
          { id: 'cat-products', title: 'Productos', icon: 'fa-solid fa-box', link: '/catalog/products' },
          { id: 'cat-uoms', title: 'Unidades de Medida', icon: 'fa-solid fa-ruler-combined', link: '/catalog/uoms', requiredRoles: ['admin', 'Admin Enterprise', 'catalog:admin'] },
          { id: 'cat-categories', title: 'Categorías', icon: 'fa-solid fa-layer-group', link: '/catalog/categories', requiredRoles: ['admin', 'Admin Enterprise', 'catalog:admin'] },
          { id: 'cat-brands', title: 'Marcas', icon: 'fa-solid fa-tag', link: '/catalog/brands', requiredRoles: ['admin', 'Admin Enterprise', 'catalog:admin'] }
        ]
      },
      {
        id: 'system',
        title: 'Sistema',
        icon: 'fas fa-cogs',
        requiredRoles: ['admin', 'Admin Enterprise'], // Solo admin
        children: [
          { id: 'sys-snapshots', title: 'Snapshots', icon: 'fas fa-camera', link: '/system/snapshots' }
        ]
      }
    ];

    // Filtrar menú según roles del usuario
    const filteredMenu = this.filterMenuByRoles(allMenuItems, roleNames);
    
    console.log('[NavigationService] 🔍 Resultado del filtro:', {
      rolesAplicados: roleNames,
      itemsVisibles: filteredMenu.map(i => i.id)
    });

    if (filteredMenu.length === 0 && roleNames.length > 0) {
      console.error('[NavigationService] ❌ Error: Menú vacío. Roles recibidos:', roleNames, 'Se requiere al menos uno de los roles definidos en allMenuItems');
    }

    this.menuItems.set(filteredMenu);
  }

  /**
   * Filtra recursivamente los items del menú según los roles del usuario
   */
  private filterMenuByRoles(items: MenuItem[], roleNames: string[]): MenuItem[] {
    const isGlobalAdmin = roleNames.includes('admin') || roleNames.includes('Admin Enterprise');

    return items
      .filter(item => {
        // Jerarquía de Poder: Si es admin global, tiene acceso a todo.
        if (isGlobalAdmin) {
          return true;
        }

        // Si no hay requiredRoles específicados, mostrar a todos
        if (!item.requiredRoles || item.requiredRoles.length === 0) {
          return true;
        }
        // Si hay requiredRoles, verificar si el usuario tiene alguno
        return roleNames.some(role => item.requiredRoles?.includes(role));
      })
      .map(item => {
        // Si el item tiene hijos, se filtran recursivamente.
        if (item.children) {
          const filteredChildren = this.filterMenuByRoles(item.children, roleNames);
          // Solo se devuelve el item si tiene hijos visibles o si es un link en sí mismo
          if (filteredChildren.length > 0 || item.link) {
            return { ...item, children: filteredChildren };
          }
          return null; // Este item se descarta porque sus hijos no son visibles
        }
        return item; // Es un item final, se mantiene
      })
      .filter((item): item is MenuItem => item !== null); // Eliminar los nulos
  }
}