# Consolidado de Tareas: 2026-05-26

Jornada de auditoría y hardening de seguridad del ecosistema InternoCore. Phase 133 — revisión OWASP Top 10, corrección de excepción raw expuesta, implementación de `AuditService.track()` con persistencia real en DB.

---

## Phase 133 — Security Hardening Sprint 2 ✅ COMPLETADO

### Auditoría de Seguridad (OWASP Top 10)

- `[x]` Revisión completa de `common/middleware.py` — JWT decode, tenant validation, subscription guard
- `[x]` Revisión de `common/security/cors_setup.py` — wildcard origins, allowed headers
- `[x]` Revisión de `common/config.py` — CORS origins list, `https://*.vercel.app` wildcard
- `[x]` Revisión de `common/security/dependencies.py` — God Mode bypass, JTI gate, scope matching
- `[x]` Revisión de `backend/kiosk_service/app/main.py` — CORS `["*"]` CRÍTICO identificado
- `[x]` Revisión de `backend/asset_manager_service/asset_app/main.py` — CORS fallback peligroso
- `[x]` Revisión de `tickets_service` — HMAC `hmac.compare_digest()` confirmado ✅

### Reporte de hallazgos (7 issues, 7 confirmaciones positivas)

| # | Severidad | Hallazgo | Estado |
|---|---|---|---|
| 1 | CRÍTICO | `kiosk_service` CORS `allow_origins=["*"]` | Pendiente fix |
| 2 | ALTO | `asset_manager_service` CORS fallback a `["*"]` | Pendiente fix |
| 3 | ALTO | Excepción raw `str(e)` expuesta en HTTP 500 middleware | **✅ CORREGIDO** |
| 4 | MEDIO | `https://*.vercel.app` wildcard subdomain en `common/config.py` | Pendiente fix |
| 5 | MEDIO | God Mode `==` no es constant-time (debería ser `hmac.compare_digest`) | Pendiente fix |
| 6 | INFO | `X-Admin-Master-Key` en allowed headers CORS (attack surface) | Aceptado (intencional) |
| 7 | INFO | JWT base64 decodificado sin verificar firma (solo extracción) | Aceptado (válido) |
| + | POSITIVO | HMAC `hmac.compare_digest()` en tickets `/internal` | ✅ Correcto |
| + | POSITIVO | Redis blocklist + JTI gate para God Mode | ✅ Correcto |
| + | POSITIVO | `require_scope()` con namespace matching | ✅ Correcto |
| + | POSITIVO | `X-Client-Request-ID` idempotency en frontend | ✅ Correcto |

### Fix #3 — Exception raw + AuditService DB logging

- `[x]` `common/middleware.py` — `traceback.print_exc()` eliminado
- `[x]` `common/middleware.py` — `logger.error(..., exc_info=True)` con trace_id estructurado
- `[x]` `common/middleware.py` — mensaje cliente: `"An unexpected error occurred."` (sin detalles internos)
- `[x]` `common/middleware.py` — `asyncio.create_task(AuditService.track(...))` fire-and-forget con acción `CRITICAL_MIDDLEWARE_ERROR`
- `[x]` `common/services/audit_service.py` — `track()` implementado con persistencia real en DB (era `print()` TODO desde el inicio)
- `[x]` `common/services/audit_service.py` — `import logging` + `_logger` a nivel de módulo
- `[x]` `common/services/audit_service.py` — `asyncio.create_task(_persist())` con `AsyncSessionLocal` propio, falla silenciosamente con `_logger.warning`

---

## Phase 134 — mes_service: Análisis Legacy + Plan de Refactorización ✅ PLANIFICADO

Sesión de análisis profundo del código legacy (`Interno.Production`, `Interno.HumanResource`, `Interno.DJO`, `Interno.Outset`) cruzado con el estado actual de `mes_service` (auditado en la misma sesión). Resultado: plan de implementación en 3 bloques + conexión con `hcm_service`.

### Auditorías realizadas
- `[x]` Auditoría completa `mes_service` — 10 CRITICOs identificados (bugs runtime + seguridad)
- `[x]` Análisis legacy `Interno.Production` (.NET 7) — mapa de equivalencias vs mes_service
- `[x]` Análisis legacy `Interno.HumanResource` (.NET 7) — mapa vs hcm_service
- `[x]` Análisis legacy `Interno.DJO` (.NET Core 3.1) — dominio supply chain / procurement (cliente Enovis)
- `[x]` Análisis legacy `Interno.Outset` (.NET 7) — adaptador Tulip MES → analytics local

### Decisiones estratégicas acordadas
- `[x]` Modelo central `ProductionRun` ya limpio (Phase 17.5) — no rediseño, solo extensión
- `[x]` Flujo de creación vía `POST /planning/bulk-load` (sustituye Excel monolítico legacy)
- `[x]` N:M WorkOrders resuelto con patrón Ledger de eventos (no FK rígido)
- `[x]` `quality = 1.0` bug ya corregido en Phase 16 (ScrapEntry + ManufacturingMath)
- `[x]` Downtime sanitización vía JWT (no body/query params para IDs de usuario)
- `[x]` `cycle_time_seconds` (RunTime legacy) como extensión prioritaria de StandardTime
- `[x]` Escalación Andon → `notification_service` por evento de dominio (sin acoplamiento)
- `[x]` mes_service listo para activar en Nginx (Phase 20.5 pasó auditor)

### Funcionalidad legacy descartada (no genérica)
- `[x]` STBL / Shortage to Build List — específico cliente Enovis/DJO
- `[x]` Kanban/Bin picking — pertenece a wms_service
- `[x]` Supplier Scorecards — dominio purchasing separado
- `[x]` Integración Tulip MES — específico a instalaciones con Tulip
- `[x]` Windows AD auth — reemplazado correctamente por JWT
- `[x]` Rout/Routing secuencial multi-operación — complejidad alta, fase futura

---

## Phase 135 — mes_service Bloque 1: Core de Manufactura ✅ COMPLETADO

### Matemáticas y tiempos
- `[x]` **Alembic migration `006`** — `cycle_time_seconds INTEGER NULL` a `mes_standard_times` + `break_minutes INTEGER DEFAULT 60` a `mes_shifts`
- `[x]` **`manufacturing_math.py`** — `calculate_tak_time_seconds()` con fallback `cycle_time_seconds → fórmula`
- `[x]` **`manufacturing_math.py`** — nueva `calculate_theoretical_capacity(cycle_time_seconds, available_minutes)`
- `[x]` **ShiftService** — `calculate_available_minutes(shift)` con aritmética overnight `(24h − start) + end`
- `[x]` **Alembic env.py** — `version_table="alembic_version_mes"` en ambos contextos
- `[x]` **Alembic env.py** — debug prints eliminados

---

## Phase 136 — mes_service Bloque 2: Ingesta y Planificación ✅ COMPLETADO

- `[x]` **`schemas/planning.py`** — `PlanningEntry` con `@field_validator('date')` rechaza pasado + `BulkLoadResponse`
- `[x]` **`api/v1/endpoints/planning.py`** — `POST /api/v1/mes/planning/bulk-load` con `begin_nested()` por entrada, `company_id` JWT, `require_scope(["mes:write"])`
- `[x]` **`main.py`** — router registrado

---

## Phase 137 — mes_service Bloque 3: Seguridad y Calidad ✅ COMPLETADO

### Sanitización Downtime IDOR
- `[x]` `respond_downtime`: `tech_user_id` query param eliminado → `current_user.sub` del JWT
- `[x]` `admin_close_downtime`: `admin_user_id` del body eliminado → JWT; `require_scope(["mes:admin","mes:write"])`
- `[x]` `close_downtime`: filtro `Downtime.company_id == company_id` en UPDATE
- `[x]` `get_active_downtimes`: filtro `company_id` en query

### Scopes aplicados
- `[x]` `scan.py` — `require_scope(["mes:write"])` + fix `float → Decimal`
- `[x]` `dashboard.py` — `require_scope(["mes:read"])` en `/oee`, `/graphic`, `/pareto`
- `[x]` `labor.py` — `require_scope` en 4 endpoints + `company_id` en `clock_out`
- `[x]` `work_order.py` — `WHERE company_id == company_id` + fix BUG-02 `db.get` → `select().where`

### Scrap
- `[x]` `POST /api/v1/mes/production/scrap` — persiste `ScrapEntry` con ownership check
- `[ ]` **`kpi_service.py`** — `get_resource_graphic()`: incluir `scrap_qty` por hora *(pendiente siguiente fase)*

---

## Phase 138 — hcm_service: Mexicanización del Expediente ✅ COMPLETADO

- `[x]` **Migration `002_split_last_name`** — `last_name` → `last_name_paternal VARCHAR(50)` + `last_name_maternal VARCHAR(50) NULL`
- `[x]` **Model `Collaborator`** — `last_name_paternal` + `last_name_maternal` + `full_name` property actualizada
- `[x]` **Schemas** — `CollaboratorRead/Create/Update` actualizados
- `[x]` RFC + CURP ya tenían validators desde Phase 50 — sin cambios requeridos

---

## Pendientes Acumulados (cross-phase)

- `[ ]` **[CRÍTICO]** Fix `kiosk_service` CORS: cambiar `allow_origins=["*"]` a origen real
- `[ ]` **[ALTO]** Fix `asset_manager_service` CORS: eliminar `or ["*"]` fallback
- `[ ]` **[MEDIO]** Reemplazar `"https://*.vercel.app"` por dominio exacto en `common/config.py`
- `[ ]` **[MEDIO]** God Mode comparison: `==` → `hmac.compare_digest()` en `middleware.py:123`
- `[ ]` Rebuild contenedor `interno-inventory-dev` para aplicar migración 003 (`payment_method`)
- `[ ]` Re-run `unified_industrial_seed.py` para poblar `PAYMENT_METHOD` en ambas DBs
- `[ ]` Fix `GET /products/{id}/variants` 403 para rol `collaborator` — agregar `inventory:read` en `select_company_command.py`
- `[ ]` `default_tax_rate` Planta US = 0.0 (actualmente 0.16)
- `[ ]` `POST /api/v1/pos/checkout` validación end-to-end con flows antigravity
- `[ ]` Activar `mes_service` y `wms_service` en nginx (ADR-04)
- `[ ]` HMAC tickets `/internal` retorna 400 en vez de 403 — verificar que guard precede a body validation
- `[ ]` Agregar `+526641667684` al seed `unified_industrial_seed.py`
- `[ ]` `audit_logs` migration para `hcm_db` y `subscription_db` (plan: `plans/analizame-este-punto-para-resilient-kay.md`)
- `[ ]` `kpi_service.py get_resource_graphic()` — incluir `scrap_qty` por hora
