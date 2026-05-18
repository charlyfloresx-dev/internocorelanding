# Consolidated Tasks — 2026-05-18

## Resumen de la Jornada
Implementación full-stack del sistema RBAC granular (Phase 112). Se cerró el cortocircuito entre la infraestructura de DB existente y el JWT/Frontend. Todos los roles sistémicos están sembrados, los scopes viajan firmados en el JWT, el menú filtra por slugs, y las rutas Angular validan permisos antes de renderizar.

---

## ✅ Completado

### 1. Migración Seed RBAC — `a1b2c3d4e5f6`
- **Archivo:** `backend/auth_service/alembic/versions/a1b2c3d4e5f6_seed_system_roles_permissions.py`
- **Qué hace:** Siembra 23 Permission slugs, 4 roles sistema con UUIDs estables, y 33 role_permissions.
- **Aplicada:** `docker exec interno-auth-dev alembic upgrade head` → revisión `a1b2c3d4e5f6 (head)` ✅
- **Idempotencia:** `ON CONFLICT DO NOTHING` en permissions + existence-check por UUID en roles (workaround para `NULL ≠ NULL` en unique constraints de PostgreSQL).
- **Cleanup:** Manager duplicado pre-existente eliminado (`a45d5142-...`, 0 usuarios, 0 permisos).

### 2. `select_company_command.py` — Extirpación de `ROLE_SCOPE_MAP`
- **Eliminado:** 51 líneas de mapa hardcodeado + función `resolve_scopes()`.
- **Reemplazado por:**
  - `_build_scopes(role_names, ucr_scopes, db_permissions)` → `["*"]` para admin/owner, slugs DB para otros.
  - `_load_role_slugs_by_name(db, role_name)` → raw SQL para el path de collaborador industrial (HR fallback).

### 3. `collaborator_login_command.py` — Scopes desde DB
- **Eliminado:** Lista hardcodeada `["inv:movements:manage", "inv:warehouse:manage", ...]`.
- **Reemplazado por:** `_load_collaborator_slugs(db)` (consulta DB con fallback de 5 slugs mínimos).

### 4. Validación JWT Live
- `full_auth_flow.py`: admin → `scopes: ["*"]` ✅
- `kiosk_auth_flow.py`: 3 colaboradores → 5 slugs DB exactos ✅

### 5. `auth.service.ts` — 3 bugs corregidos
- `isReadOnly`: eliminado `.includes('read')` en permissions (falso positivo con slugs granulares).
- `isSuperAdmin`: `r === 'admin' || r === 'owner'` + `permissions.includes('*')`.
- `collaboratorLogin()` Case B: lee `data.scopes || data.permissions` en lugar de hardcodear.

### 6. `navigation.service.ts` — Blueprint a slugs DB
- Inventory: `inventory.stock.read`
- WMS: `inventory.put_away`, `inventory.cycle_count`
- Catalog: `master_data.product.write`
- `isAdmin()`: match exacto de rol o `["*"]`.

### 7. `RequirePermission` guard (FastAPI/common)
- **Archivo:** `backend/common/security/require_permission.py`
- Auto-resolución de `module_code` por slug prefix.
- Compone sobre `SubscriptionGuard`.
- 0 Code Graph CRITICALs.

### 8. `permissionGuard` (Angular)
- **Archivo:** `frontend/src/app/core/guards/permission.guard.ts`
- `CanActivateFn` funcional con OR-semantics.
- Aplicado en `app.routes.ts`: `/admin/*`, `/catalog/*`, `/inventory/audit`.
- TypeScript compila sin errores.

### 9. `pos.py` — 2 bugs corregidos
- Import `Decimal` faltante → `NameError` en cualquier checkout.
- `quantity_change=item.quantity` → `quantity_change=-item.quantity`.

---

## 🔧 Archivos Modificados

| Archivo | Cambio |
|---|---|
| `backend/auth_service/alembic/versions/a1b2c3d4e5f6_seed_system_roles_permissions.py` | NUEVO — seed RBAC |
| `backend/auth_service/auth_app/commands/select_company_command.py` | Extirpación ROLE_SCOPE_MAP |
| `backend/auth_service/auth_app/commands/collaborator_login_command.py` | Scopes desde DB |
| `backend/common/security/require_permission.py` | NUEVO — guard FastAPI |
| `backend/common/security/__init__.py` | Export RequirePermission |
| `backend/inventory_service/inventory_app/api/v1/endpoints/pos.py` | Fix Decimal + qty negativa |
| `frontend/src/app/core/services/auth.service.ts` | isReadOnly + isSuperAdmin + collaboratorLogin |
| `frontend/src/app/core/services/navigation.service.ts` | Slugs DB + isAdmin exacto |
| `frontend/src/app/core/guards/permission.guard.ts` | NUEVO — guard Angular |
| `frontend/src/app/app.routes.ts` | canActivate en admin/catalog/audit |
| `frontend/SERVICE_LOG.md` | NUEVO |

---

## 📋 Pendientes (deuda técnica activa)

- [ ] Aplicar `RequirePermission("inventory.document.approve")` en el endpoint de aprobación de documentos de inventario.
- [ ] Aplicar `RequirePermission("inventory.audit.view")` en `GET /inventory/audit` (backend).
- [ ] Aplicar `RequirePermission("inventory.bulk_load")` en `POST /inventory/bulk-load`.
- [ ] Point-in-Time Price Lookup para reimprimir documentos históricos (`as_of_date` en `product_service.py`).
- [ ] Tabla `audit_logs` faltante en `hcm_db` / `subscription_db` (AuditService falla silenciosamente).
- [ ] Columna `internal_id_pattern` faltante en `hr_tenant_configs`.
- [ ] `default_tax_rate` Planta US: actualmente 0.16, debería ser 0.0.
- [ ] Sesión 4 RBAC: CRUD Owner de usuarios + rol + UI `/admin/staff`.
- [ ] Rate limit por endpoint en WMS, MES, HR, Subscription.
