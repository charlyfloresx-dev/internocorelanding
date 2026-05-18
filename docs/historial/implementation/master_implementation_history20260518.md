# Master Implementation History — 2026-05-18
## Phase 112: RBAC Full-Stack

---

## Arquitectura Implementada

### Cadena de seguridad completa (antes vs después)

**Antes (Phase 111):**
```
JWT Login → ROLE_SCOPE_MAP hardcodeado → scopes legacy ("inv:movements:manage")
Frontend → .includes('read') → isReadOnly=true para colaboradores ❌
Rutas Angular → cualquier usuario autenticado accede a /admin/* ❌
```

**Después (Phase 112):**
```
DB (roles/permissions/role_permissions) → permission_checker.get_user_permissions()
  → _build_scopes() → scopes: ["*"] (admin) | slugs DB (otros) → JWT firmado
Frontend → session().readonly → isReadOnly real
Rutas Angular → permissionGuard → route.data['requiredPermission'] → /dashboard si denegado
```

---

## Decisiones Arquitectónicas

### 1. Admin sin filas en role_permissions
Admin recibe `scopes: ["*"]` detectado por nombre de rol en `_build_scopes()`. No hay filas en `role_permissions` para admin. El wildcard es suficiente y evita sincronizar 23 filas cuando los permisos del admin son siempre totales.

### 2. Sentinel UUID `00000000-0000-0000-0000-000000000001`
Usado para `tenant_id` y `company_id` en registros sistema donde los campos son NOT NULL pero el concepto es global (sin tenant). Convención documentada y usada consistentemente en permisos, roles y role_permissions.

### 3. `NULL ≠ NULL` en PostgreSQL unique constraints
`ON CONFLICT (name, company_id) DO NOTHING` no funciona cuando `company_id IS NULL` para ambas filas — PostgreSQL no considera que dos NULLs sean iguales en este contexto. Fix: existence-check explícito por UUID estable antes de insertar roles.

### 4. `RequirePermission` compone sobre `SubscriptionGuard`
No duplica lógica de JWT parsing, readonly enforcement ni God Mode. La instancia de `SubscriptionGuard` se crea en `__init__` (no por request) porque es stateless. El `module_code` se auto-resuelve desde el prefix del slug.

### 5. `permissionGuard` sobre el parent route en Angular
Guardar el parent `/admin` y `/catalog` es suficiente para proteger todos los hijos, porque Angular evalúa `canActivate` de todos los segmentos del path en cada navegación directa por URL. Para `/inventory/audit` se guarda el child directamente (el resto del tree de inventario es accesible para colaboradores).

---

## Mapeo de permisos por rol (sembrado)

| Slug | admin | manager | wh_operator | collaborator |
|---|---|---|---|---|
| `inventory.stock.read` | ✓* | ✓ | ✓ | ✓ |
| `inventory.document.create` | ✓* | ✓ | ✓ | ✓ |
| `inventory.document.approve` | ✓* | ✓ | — | — |
| `inventory.document.cancel` | ✓* | ✓ | — | — |
| `inventory.transfer.inter_co` | ✓* | ✓ | — | — |
| `inventory.audit.view` | ✓* | ✓ | — | — |
| `inventory.bulk_load` | ✓* | ✓ | — | — |
| `inventory.location.manage` | ✓* | ✓ | — | — |
| `inventory.cycle_count` | ✓* | ✓ | ✓ | — |
| `inventory.put_away` | ✓* | — | ✓ | — |
| `master_data.product.read` | ✓* | ✓ | ✓ | ✓ |
| `master_data.product.write` | ✓* | ✓ | — | — |
| `master_data.price.read` | ✓* | ✓ | ✓ | ✓ |
| `master_data.price.write` | ✓* | ✓ | — | — |
| `master_data.partner.manage` | ✓* | ✓ | — | — |
| `master_data.warehouse.manage` | ✓* | ✓ | — | — |
| `hcm.collaborator.read` | ✓* | ✓ | — | — |
| `hcm.collaborator.write` | ✓* | ✓ | — | — |
| `hcm.collaborator.rfid_assign` | ✓* | ✓ | — | — |
| `admin.user.manage` | ✓* | ✓ | — | — |
| `admin.role.view` | ✓* | ✓ | — | — |
| `pos.checkout` | ✓* | ✓ | ✓ | ✓ |
| `pos.price_override` | ✓* | — | — | — |

`✓*` = wildcard `["*"]`, no filas en role_permissions.

---

## Rutas Angular protegidas

| Ruta | Guard | `requiredPermission` | Quién accede |
|---|---|---|---|
| `/admin/*` | `permissionGuard` | `admin.user.manage` | Admin, Manager |
| `/catalog/*` | `permissionGuard` | `['master_data.product.write', 'master_data.product.read']` | Admin, Manager, Collaborator (read) |
| `/inventory/audit` | `permissionGuard` | `inventory.audit.view` | Admin, Manager |
| Resto de `/inventory/*` | `authGuard` (solo autenticación) | — | Todos autenticados |
