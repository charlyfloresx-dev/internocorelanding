# Consolidated Tasks — 2026-05-18

## Resumen de la Jornada (Phases 112 & 113)
Jornada de robustecimiento integral de seguridad y control de acceso en InternoCore. Se completó la implementación del **sistema RBAC granular** (Phase 112) y el **Sprint 1 de Security Hardening** (Phase 113), remediando 6 hallazgos críticos/altos identificados en la auditoría de pentesting estático. Además, se integró el panel backend y flujo de auditoría forense para **GOD MODE** con control de rate limits y logs detallados.

---

## ✅ Completado

### 1. Sprint 1 — Fixes Críticos (Security Hardening)

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

### 2. GOD MODE Frontend & Backend Integration

| Componente | Archivo | Estado |
|---|---|---|
| `create_god_mode_token()` (300s, jti) | `auth_service/core/security.py` | ✅ Creado token firmado y efímero |
| `AuditService.log_action()` + `ip_address`/`user_agent` | `common/services/audit_service.py` | ✅ Registro forense extendido |
| `POST /api/v1/admin/elevate` (rate limit 3/h) | `auth_service/api/v1/endpoints/admin.py` | ✅ Endpoint de elevación controlado |
| `GET /api/v1/admin/security-logs` | `auth_service/api/v1/endpoints/admin.py` | ✅ Endpoint de auditoría expuesto |

### 3. Sistemas RBAC Granular (Phase 112)

*   **Migración Seed RBAC (`a1b2c3d4e5f6`):**
    *   Siembra de 23 Permission slugs, 4 roles de sistema con UUIDs estables y 33 role_permissions.
    *   Garantía de idempotencia mediante `ON CONFLICT DO NOTHING` en permisos e inspección previa por UUID en roles.
    *   Eliminación de rol Manager duplicado heredado.
*   **`select_company_command.py` (Extirpación de `ROLE_SCOPE_MAP`):**
    *   Eliminadas 51 líneas de mapa hardcodeado.
    *   Reemplazado por carga dinámica y `_build_scopes` (retorna `["*"]` para administradores y slugs reales de la DB para otros roles).
*   **`collaborator_login_command.py` (Scopes desde DB):**
    *   Eliminada la lista estática anterior de permisos de colaborador.
    *   Implementado `_load_collaborator_slugs` desde la base de datos real con fallback de seguridad.
*   **Alineamiento del Frontend Angular:**
    *   `auth.service.ts`: Corregidos bugs de permisos (eliminado falso positivo de sub-texto `read` en slugs y blindado chequeo de `isSuperAdmin`).
    *   `navigation.service.ts`: Mapeo completo de menús de UI a slugs DB reales (`inventory.stock.read`, `inventory.put_away`, `master_data.product.write`, etc.).
    *   `permission.guard.ts` y `app.routes.ts`: Validaciones estrictas Angular en navegación lateral y vistas del sistema.

### 4. Sincronización Offline-First en App Móvil (Phase 114)

*   **Paginación y Resolución de Variantes:**
    *   Soporte robusto a variables y precios específicos en el payload sincronizado desde la API maestra.
    *   Resolución correcta de moneda (US vs MXN) previniendo hardcodes y caídas de tipo de dato.
*   **Alineamiento Arquitectónico API-Flutter:**
    *   El API mantiene su tipado estricto `UUID` para conceptos de movimiento en vez de ensuciar el ruteo interno con cast desde códigos manuales.
    *   Los scripts y app cliente se han adaptado para consultar los UUIDs deterministas (como el concepto `ENT-PUR`) e introducirlos limpiamente en los payloads.
    *   Generación exitosa de folios de entrada industrial mediante `scanner_bloc.dart` y validado por test scripts end-to-end.

### 5. Tests en Vivo (Gateway Puerto 8000)

| Test | Resultado |
|---|---|
| `POST /elevate` — key correcta → 200 + token 300s + JTI | ✅ Completado exitosamente |
| `POST /elevate` — key incorrecta → 401 Unauthorized | ✅ Bloqueado |
| `POST /elevate` — sin header → 422 Unprocessable (fail-closed) | ✅ Bloqueado |
| `GET /security-logs` — con god-token → 200 + Logs de auditoría | ✅ Auditado correctamente |
| `GET /security-logs` — sin token → 401 Unauthorized | ✅ Bloqueado |
| **Generación Documento (App/API)** — Payload strict UUID | ✅ Generado `DOC-` satisfactoriamente |
| **Code Graph Integrity** | ✅ 0 errores CRITICALs en 14 servicios |
| **Ecosystem Status** | ✅ 8/8 servicios reportan `[ OK ]` |

---

## 🔧 Archivos Modificados

| Archivo | Cambio principal |
|---|---|
| `backend/common/config.py` | Sin default en `int_admin_master_key` + validadores de seguridad. |
| `backend/common/middleware.py` | Bypass de tenant usa settings y whitelist de elevación. |
| `backend/common/security/subscription_guard.py` | Logs de auditoría críticos para GOD MODE sin fallback inseguro. |
| `backend/common/security/require_permission.py` | NUEVO — Guard FastAPI para control de scopes granulares. |
| `backend/common/infrastructure/database.py` | RLS Hook blindado con validación estricta de UUID e invalidación. |
| `backend/master_data_service/master_app/infrastructure/repositories/sqlalchemy_master_data_repository.py` | Exposición de precios de variantes y moneda de inventario en endpoints. |
| `frontend/src/app/core/guards/permission.guard.ts` | NUEVO — Angular Guard para validación estricta basada en roles/permisos. |
| `src/interno_billing_app/lib/core/services/product_sync_service.dart` | Parseo correcto de precios/monedas anidadas de la DB al cache local. |
| `src/interno_billing_app/lib/features/scanner/presentation/bloc/scanner_bloc.dart` | Envío estricto de UUID en lugar de códigos duros. |

---

## 📋 Pendientes & Acciones Planificadas

### 1. Sprint 2 — robustecimiento (Próxima Semana)

- [ ] **Validación de Respuestas de API:** Validar la respuesta del servicio HR con un esquema Pydantic robusto (`select_company_command.py:129`).
- [ ] **Limpieza de Bypass RLS:** Remover el bypass comodín por `ucr_scopes` en la capa de base de datos (`select_company_command.py:27`).
- [ ] **Alineamiento Asíncrono:** Convertir el log de auditoría `PAST_DUE` de fire-and-forget a awaited/esperado (`subscription_guard.py:94`).
- [ ] **Mapeo de Rutas de Inventario con RequirePermission:**
    - [ ] Aplicar `RequirePermission("inventory.document.approve")` en el endpoint de aprobación.
    - [ ] Aplicar `RequirePermission("inventory.audit.view")` en `GET /inventory/audit` (backend).
    - [ ] Aplicar `RequirePermission("inventory.bulk_load")` en `POST /inventory/bulk-load`.
- [ ] **UI del Panel GOD MODE (Frontend Angular):**
    - [ ] Componente `GodModeTrigger` + `GodModeStore` (Signal Store para control de estado).
    - [ ] Componente `AuditAlertsDashboard` (Tabla de logs forenses de `/security-logs`).
    - [ ] Aplicar `permissionGuard` en `/admin/system-control` (solo accesible para Owner/Admin).
- [ ] **Endurecimiento de Infraestructura de Elevación:** Rate limit controlado por Redis para `/admin/elevate` (actualmente en memoria vía slowapi).

### 2. Sprint 3 — Deuda Técnica de Seguridad (2 semanas)

| ID | Acción | Archivo / Contexto | Esfuerzo | Estado |
|---|---|---|---|:---:|
| **12** | **Endpoint de revocación de tokens de colaborador** (Redis blocklist) | `auth_service` | 2h | [ ] Pendiente |
| **13** | **Reducir TTL de token colaborador a 8h** (mayor frecuencia de rotación de sesión) | `collaborator_login_command.py` | 10 min | [ ] Pendiente |
| **14** | **Validación de longitud mínima de PIN de seguridad** | `collaborator_login_command.py` | 10 min | [ ] Pendiente |
| **15** | **Fuga de PII en logs:** Reemplazar `full_name` por `user_id` en info logs | `select_company_command.py` | 15 min | [ ] Pendiente |

### 3. Deuda Técnica General y Continuidad

- [ ] **Point-in-Time Price Lookup:** Soporte para reimpresión exacta de documentos históricos con precios vigentes en la fecha de emisión (`as_of_date` en `product_service.py`).
- [ ] **Infraestructura de Logs Silenciosa:** Resolver tablas `audit_logs` faltantes en `hcm_db` y `subscription_db` (actualmente capturadas y silenciadas para evitar fallos de transacción).
- [ ] **Configuración HR:** Añadir columna `internal_id_pattern` faltante en la tabla `hr_tenant_configs`.
- [ ] **Sincronización Fiscal de Planta US:** Ajustar `default_tax_rate` in Planta US to `0.0` (actualmente sembrado en `0.16` por herencia de IVA MX).
- [ ] **RBAC Sesión 4:** Construcción del panel CRUD de Staff / Colaboradores (`/admin/staff`) para administración de usuarios y asignación de roles.
- [ ] **Rate Limiting Distribuido:** Aplicar políticas de rate limit controladas en Redis para endpoints en WMS, MES, HR y Subscription.
- [x] **Sincronización Offline-First en App Móvil:** Implementar el plan de sincronización de catálogo de productos y precios locales en la app móvil ([mobile_product_sync_plan.md](file:///c:/API/interno/docs/historial/tasks/mobile_product_sync_plan.md)) utilizando Drift/SQLite para garantizar operación 100% offline y latencia de 0ms en escaneo.
