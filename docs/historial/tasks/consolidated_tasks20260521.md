# Consolidated Tasks — 2026-05-21

## Sesión: Phase 120 — Security Hardening + Frontend Scope Alignment

---

### Backlog Completado

#### Backend
- [x] **Iron Wall fix — inventory_service** `inventory.py` (10 endpoints): migrar de `Header(x_company_id)` a `SubscriptionGuard` — company_id siempre del JWT.
- [x] **Iron Wall fix — inventory_service** `dashboard.py` (9 endpoints): mismo patrón.
- [x] **Admin guard — auth_service** `companies.py`: añadir `verify_admin_master_key` a POST/GET/PUT/DELETE.
- [x] **Admin guard — auth_service** `seed.py`: añadir `verify_admin_master_key` a `/run`.
- [x] **Admin guard — subscription_service** `wallet.py`: añadir `verify_admin_master_key` a `/award` y `/deduct`.
- [x] **Audit trail — hcm_service** `collaborators.py` `bulk_upload`: añadir `AuditService.log_action("COLLABORATOR_BULK_UPLOAD")` antes del commit.

#### Frontend Angular
- [x] **`domain.types.ts`**: Añadir `modules?: string[]` a `AuthSession` — el JWT de backend incluía este claim pero el tipo no lo declaraba.
- [x] **`auth.service.ts`**: Añadir `modules` computed signal + `hasModule(moduleCode)` method con bypass para SuperAdmin.
- [x] **`multi-tenant.interceptor.ts`**: Corregir bug donde 403 (scope insuficiente) disparaba `auth.logout()`. Ahora: 401 → RTR, 403 → toast de denegación sin logout.
- [x] **`app.routes.ts`**: Añadir `canActivate: [permissionGuard]` a ruta padre `/inventory` con `requiredPermission` aceptando formatos dot y colon.

#### Sync-Docs
- [x] Code Graph audit — 0 errores, todos los servicios CLEAN.
- [x] Ecosystem validation — 8/8 servicios OK.
- [x] REPO_LOG.md actualizado (Phase 120).
- [x] SERVICE_LOGs actualizados: inventory_service, auth_service, hcm_service, subscription_service.

---

### Pendientes (deuda técnica identificada)

- [ ] **Scope format standardization**: Backend emite dot-format (`inventory.stock.read`) para colaboradores y colon-format (`inventory:read`) para usuarios invitados. Frontend `NavigationService` solo verifica dot-format — usuarios invitados no ven ítems de nav. Decisión pendiente: estandarizar en backend o actualizar NavigationService para aceptar ambos formatos.
- [ ] **`canActivate` en `/monitor/tickets`**: Necesita `ticket:read` o `tickets.view`. Fuera de scope hoy.
- [ ] **`canActivate` en `/production`**: Pendiente despliegue de mes_service.
- [ ] **Bug conocido (Phase 109)**: `GET /products/{id}/variants` retorna 403 para rol `collaborator`. Fix: agregar `inventory:read` al scope mapping del colaborador en `select_company_command.py`.
