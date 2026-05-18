# Consolidated Tasks — 2026-05-18 (Phase 113)

## Resumen
Sprint 1 de Security Hardening. Remediación de 6 hallazgos críticos/altos identificados en auditoría de pentesting estático. Implementación completa del panel GOD MODE para el frontend con backend seguro, auditado y testeado.

---

## ✅ Completado

### Sprint 1 — Fixes Críticos

| # | Fix | Archivo | Resultado |
|---|---|---|---|
| C-1 | Eliminar default `GOD_MODE_ACTIVE` + validator | `common/config.py` | ✅ Fail-closed si `CORE_ADMIN_MASTER_KEY` ausente |
| C-1b | Middleware bypass usa `settings` | `common/middleware.py` | ✅ Eliminado hardcode + `/admin/elevate` en whitelist |
| C-1c | Audit log en activación GOD MODE | `common/security/subscription_guard.py` | ✅ `logger.critical` + `AuditService` en cada activación |
| C-2 | RLS hook blindado | `common/infrastructure/database.py` | ✅ UUID validation + `invalidate()` + raise |
| C-3 | BOLA en POS — warehouse + product sin tenant | `inventory_service/api/v1/endpoints/pos.py` | ✅ `ERR_WAREHOUSE_NOT_OWNED` + `company_id` en queries |
| H-1 | Price enumeration via error message | `pos.py:120` | ✅ `ERR_PRICE_MISMATCH` genérico |
| H-3 | Missing `RequirePermission("pos.checkout")` | `pos.py:19` | ✅ Guard aplicado |
| - | Float prohibido en `total_amount` | `pos.py:155` | ✅ `str(sale.total_amount)` |

### GOD MODE Frontend Backend

| Componente | Archivo | Estado |
|---|---|---|
| `create_god_mode_token()` (300s, jti) | `auth_service/core/security.py` | ✅ |
| `AuditService.log_action()` + `ip_address`/`user_agent` | `common/services/audit_service.py` | ✅ |
| `POST /api/v1/admin/elevate` (rate limit 3/h) | `auth_service/api/v1/endpoints/admin.py` | ✅ |
| `GET /api/v1/admin/security-logs` | `auth_service/api/v1/endpoints/admin.py` | ✅ |

### Tests en Vivo (gateway port 8000)

| Test | Resultado |
|---|---|
| `POST /elevate` — key correcta → 200 + token 300s + JTI | ✅ |
| `POST /elevate` — key incorrecta → 401 | ✅ |
| `POST /elevate` — sin header → 422 (fail-closed) | ✅ |
| `GET /security-logs` — con god-token → 4 eventos GOD_MODE_ACTIVATED | ✅ |
| `GET /security-logs` — sin token → 401 | ✅ |
| Code Graph | ✅ 0 CRITICALs en 14 servicios |
| Ecosistema | ✅ 8/8 servicios OK |

---

## 🔧 Archivos Modificados

| Archivo | Cambio |
|---|---|
| `backend/common/config.py` | Sin default en `int_admin_master_key` + validator |
| `backend/common/middleware.py` | `bypass_tenant` usa settings + `/admin/elevate` en whitelist |
| `backend/common/security/subscription_guard.py` | Audit log GOD MODE + getattr sin fallback |
| `backend/common/infrastructure/database.py` | UUID validation + invalidate() + raise en RLS hook |
| `backend/common/services/audit_service.py` | `ip_address` + `user_agent` en `log_action()` |
| `backend/auth_service/auth_app/core/security.py` | `create_god_mode_token()` + `create_admin_god_token()` legacy |
| `backend/auth_service/auth_app/api/v1/endpoints/admin.py` | `POST /elevate` + `GET /security-logs` |
| `backend/inventory_service/inventory_app/api/v1/endpoints/pos.py` | BOLA fix + price enumeration + RequirePermission + float |

---

## 📋 Pendientes — Sprint 2 (próxima semana)

- [ ] Validar HR service response con schema Pydantic (`select_company_command.py:129`)
- [ ] Remover wildcard bypass por `ucr_scopes` del DB (`select_company_command.py:27`)
- [ ] Convertir audit log PAST_DUE de fire-and-forget a awaited (`subscription_guard.py:94`)
- [ ] Aplicar `RequirePermission("inventory.document.approve")` en endpoint de aprobación
- [ ] Aplicar `RequirePermission("inventory.audit.view")` en `GET /inventory/audit`
- [ ] Aplicar `RequirePermission("inventory.bulk_load")` en `POST /inventory/bulk-load`
- [ ] Endpoint de revocación de tokens de colaborador (Redis blocklist)
- [ ] Componente Angular `GodModeTrigger` + `GodModeStore` (signal store)
- [ ] Componente Angular `AuditAlertsDashboard` (tabla `/security-logs`)
- [ ] `permissionGuard` en `/admin/system-control` (solo owner/admin)
- [ ] Rate limit Redis-backed para `/admin/elevate` (actualmente en memoria por slowapi)
