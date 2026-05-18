# Service Log — Frontend Angular (interno-web)

## 🕒 Última Actividad (2026-05-18)
**Phase 112: RBAC Frontend — isReadOnly Fix, Kiosk Scopes, Permission Guard** ✅

- **`auth.service.ts` — Bug `isReadOnly` extirpado**: `isReadOnly` ya no evalúa `.includes('read')` sobre la lista de permisos. Con slugs granulares como `inventory.stock.read`, el check previo clasificaba a todos los colaboradores como solo-lectura, deshabilitando botones de acción. Ahora depende exclusivamente de `session().readonly` (JWT flag) + estado de suscripción `RESTRICTED` + rol explícito `viewer`.
- **`auth.service.ts` — `isSuperAdmin` endurecido**: Reemplazado `.includes('admin')` (que matcheaba `admin.user.manage`, escalando managers a super-admin) por comparación exacta `r === 'admin' || r === 'owner'` más `permissions.includes('*')`.
- **`auth.service.ts` — `collaboratorLogin()` Case B**: Eliminado el hardcode `permissions: ['inv:movements:manage']`. Ahora lee `data.scopes || data.permissions` del response del backend, propagando los 5 slugs granulares reales del rol `collaborator`.
- **`navigation.service.ts` — Blueprint migrado a slugs DB**: Permisos del menú transaccional actualizados: `inventory` → `inventory.stock.read`, `wms` → `inventory.put_away / inventory.cycle_count`, `catalog` → `master_data.product.write`. `isAdmin()` usa match exacto de rol o `permissions.includes('*')`.
- **`permission.guard.ts` creado**: `CanActivateFn` funcional (`core/guards/permission.guard.ts`). Lee `route.data['requiredPermission']` (string o array OR-semantics). Bypass wildcard `["*"]`. Redirige a `/dashboard` si denegado.
- **`app.routes.ts` — Rutas protegidas**: `/admin/*` → `admin.user.manage`, `/catalog/*` → `['master_data.product.write', 'master_data.product.read']`, `/inventory/audit` → `inventory.audit.view`. TypeScript sin errores de compilación.
- **Status**: ✅ COMPLETED — Menú y rutas alineados con slugs RBAC. Colaboradores no pueden navegar por URL a secciones administrativas.

---

## [2026-05-17] Phase 110 & 111: Navigation Shell, Price Drawer & Dynamic Currency

- **Navigation Shell**: `setup_screen.dart` redirige a `MainNavigationScreen` en restauración de sesión.
- **Price Drawer 750px**: 4 triggers en `product-catalog.component.ts` con `width: 'md:w-[750px] w-full'`.
- **Dynamic Currency**: `product_service.py` `lookup_product_by_code()` resuelve moneda desde `PriceAgreement → ProductPrice → fallback "MXN"`.
- **Status**: ✅ COMPLETED.
