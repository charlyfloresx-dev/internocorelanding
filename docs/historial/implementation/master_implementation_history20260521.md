# Master Implementation History — 2026-05-21

## Phase 120: Backend Security Hardening + Frontend Scope/Module Alignment

---

### Contexto y Motivación

Auditoría de seguridad transversal del stack. Se identificaron tres categorías de vulnerabilidades:
1. **Iron Wall violations** en inventory_service — `company_id` provenía del cliente (IDOR potencial).
2. **Endpoints admin sin autenticación** en auth_service y subscription_service.
3. **Frontend scope gap** — JWT `modules` claim no capturado; 403 causaba logout; /inventory sin route guard.

---

### Cambios Implementados

#### `backend/inventory_service/inventory_app/api/v1/endpoints/inventory.py`

**Problema:** 10 endpoints usaban `x_company_id: uuid.UUID = Header(...)`. El header `X-Company-ID` es inyectado por el interceptor Angular pero cualquier cliente HTTP puede enviar el valor que quiera.

**Solución:** Reemplazar la dependencia de Header con `SubscriptionGuard`:
```python
# ANTES
async def create_movement(x_company_id: uuid.UUID = Header(...), ...):
    ...service.create_movement(company_id=x_company_id, ...)

# DESPUÉS
async def create_movement(token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")), ...):
    ...service.create_movement(company_id=token.company_id, ...)
```

Endpoints migrados: `/movements`, `/reconcile`, `/reserve`, `/release`, `/transfers/dispatch`, `/transfers/receive`, `/stock/{warehouse_id}/{product_id}`, `/stock`, `/warehouses/{warehouse_id}/audit-export`, `/warehouses/{warehouse_id}/cycle-count`.

Excepción preservada: `/bulk-load` conserva `X-Internal-Secret` — es endpoint de uso inter-servicio.

#### `backend/inventory_service/inventory_app/api/v1/endpoints/dashboard.py`

Mismo patrón aplicado a 9 endpoints de dashboard/reporting. Antes usaban `x_company_id: Union[uuid.UUID, str] = Header(...)`.

Nota: `/reports/abc` tiene un bug pre-existente (missing return statement) que se dejó intacto — no era el scope del fix de seguridad.

#### `backend/auth_service/auth_app/api/v1/endpoints/companies.py`

Añadida función local `verify_admin_master_key` (misma implementación que en `admin.py`) y aplicada como dependency a los 5 endpoints CRUD. Esta es la misma función que ya existía en `subscription_service/admin.py` y `hcm_service`.

#### `backend/auth_service/auth_app/api/v1/endpoints/seed.py`

Mismo guard aplicado al único endpoint `/run`.

#### `backend/subscription_service/subscription_app/api/v1/endpoints/wallet.py`

Guard aplicado a `/award` y `/deduct`. Endpoints de consulta (`/balance/{id}`, `/history/{id}`) conservados abiertos — guest data de solo lectura.

#### `backend/hcm_service/hcm_app/api/v1/endpoints/collaborators.py`

```python
# Añadido en bulk_upload, antes de db.commit():
await AuditService.log_action(
    db=db,
    user_id=token.sub,
    action="COLLABORATOR_BULK_UPLOAD",
    entity_name="collaborators",
    entity_id=None,
    company_id=token.company_id,
    details=f"Bulk upload: {results['created']} created, {results['updates']} updated, {len(results['errors'])} errors",
    new_value={"created": results["created"], "updates": results["updates"]},
)
```

#### `frontend/src/app/core/models/domain.types.ts`

```typescript
export interface AuthSession {
  // ... campos existentes ...
  modules?: string[];  // JWT claim — e.g. ["INVENTORY_CORE", "HCM_CORE"]
}
```

#### `frontend/src/app/core/services/auth.service.ts`

```typescript
public modules = computed(() => this.session()?.modules ?? []);

public hasModule(moduleCode: string): boolean {
    if (this.isSuperAdmin()) return true;
    const mods = this.modules();
    return mods.includes(moduleCode) || mods.includes('*');
}
```

#### `frontend/src/app/core/interceptors/multi-tenant.interceptor.ts`

**Bug:** El bloque `if ((error.status === 401 || error.status === 403) && ...)` tenía RTR solo para 401, pero al final del bloque llamaba `auth.logout()` para "otros errores de seguridad" — lo que incluía 403.

**Fix:** Separar en dos bloques independientes:
```typescript
// 401 → RTR
if (error.status === 401 && !isMockSession && !isAuthRoute && !isAdminRoute) {
    if (!url.includes('/auth/refresh')) {
        // RTR flow...
    } else {
        auth.logout(); // refresh token expirado → logout
    }
}

// 403 → toast, sin logout
if (error.status === 403 && !isAuthRoute) {
    toast.error('Acceso denegado. Permisos insuficientes para esta operación.', 'Sin Permisos');
}
```

#### `frontend/src/app/app.routes.ts`

```typescript
{
    path: 'inventory',
    canActivate: [permissionGuard],
    data: {
        requiredPermission: [
            'inventory.stock.read',     // collaborator dot-format
            'inventory:read',           // invited user colon-format
            'inventory.document.create',
            'inventory.document.approve',
            'inventory.audit.view'
        ]
    },
    children: [...]
}
```

---

### Servicios NO modificados (auditados y LIMPIOS)

- **`master_data_service`**: Todos los endpoints ya tenían `require_scope`. Sin cambios.
- **`subscription_service/admin.py`**: Ya tenía `verify_admin_master_key` en todos los endpoints `force-*`. Sin cambios.
- **`tickets_service`**: No auditado en esta fase.

---

### Métricas de Phase 120

| Servicio | Endpoints corregidos | Tipo de fix |
|---|---|---|
| inventory_service | 19 | Iron Wall (IDOR) |
| auth_service | 6 | Missing auth guard |
| subscription_service | 2 | Missing auth guard |
| hcm_service | 1 | Missing audit trail |
| Frontend (4 archivos) | — | Scope/module alignment |

**Code Graph:** 0 errores. **Ecosistema:** 8/8 OK.
