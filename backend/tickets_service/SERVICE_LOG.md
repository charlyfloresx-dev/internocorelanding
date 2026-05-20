# Tickets Service Log

## Overview
The InternoCore Tickets Service evolved from a generic helpdesk module to the **Operational Motor** of the enterprise architecture (Phase 10). It orchestrates actions between users, production floors (MES), and inventory control (ERP).

### Service Stats
| Metric | Value |
|---|---|
| **Source Files** | 23 |
| **Data Models** | 6 (Ticket, Comment, History, Resource, StopLog, OutboxEvent) |
| **API Endpoints** | 6 REST |
| **Test Coverage** | 15% (Debouncing logic) |
| **Last Audit** | 2026-05-02 |

---

## 🚀 Log de Cambios y Estabilización

### [2026-05-20] Phase 118: Polymorphic Department Ticket Assignments & Visibility Filters ✅
- **Modelo `Ticket`** (`models/ticket.py`): Campo `assigned_department_id` (UUID, index, nullable) añadido para routing a departamentos sin FK dura a hcm_db.
- **Schemas** (`schemas/ticket_dto.py`): `TicketCreate`, `TicketUpdate`, `TicketRead`, `TicketTriage` actualizados con `assigned_department_id: Optional[UUID]`.
- **Triaje inteligente** (`services/ticket_service.py`): En acción `REASSIGN` con `assigned_department_id`, limpieza atómica de `assigned_to_id`, `collaborator_id`, `external_contact_id`. Ticket retorna a cola del departamento en estado `ASSIGNED`.
- **Filtro de visibilidad** (`infrastructure/repositories/ticket_repository.py`): `list_by_visibility` acepta `department_id: Optional[UUID]`. Operadores de piso ven tickets asignados a su área en `/mine`.
- **Ruta API** (`routers/ticket_routes.py`): `GET /mine` acepta query param `department_id` opcional.
- **Migración Alembic** (`001_add_assigned_department_id.py`): Columna + índice en `tickets_db`.
- **Status**: ✅ COMPLETED — Code Graph 0 errores.

### [2026-05-02] Phase 79: Resiliencia del Motor de Eventos
- **Outbox Debouncing**: Implementado blindaje contra tormentas de eventos. `add_outbox_event` verifica si existe un evento idéntico (`event_type` + `payload`) creado en los últimos 10 segundos, limitando ráfagas generadas por el UI.
- **Timezone Standardization**: Se estandarizó la columna `processed_at` del `OutboxEvent` a `DateTime(timezone=True)` resolviendo errores críticos de cálculo de fechas en PostgreSQL (`asyncpg.exceptions.DataError`).
- **Escalation Watcher**: Validada su tolerancia a fallos de DNS (`Name or service not known`) mediante bucles `try-except`, lo que permite auto-curación sin reinicios del contenedor tras re-despliegues del monolito.
- **Unit Tests**: Implementación de `test_debouncing.py` validando la ventana de tiempo del outbox de manera asíncrona.

---

### Completed Phases

#### Phase 9: Intelligence & Notifications
- **Status**: Completed (2026-03-04)
- **Features**:
  - P1-P4 priority mappings.
  - `TicketsClient` consumption of auto-generated events from the `inventory_service` (Stock Breaks, Low Stock).
  - SHA256 anti-fatigue debouncing logic inside the internal ticket creator to prevent duplicates during storms.
  - Basic Webhook Provider routing (later migrated to Notification Service).

#### Phase 10: Enterprise Orchestration (MES/ERP Migration)
- **Status**: Completed (2026-03-04)
- **Features**:
  - Extracted Webhook dispatch and notifications into a separate decoupled `notification_service`.
  - Added operational tracking parameters (`module_origin`, `area`, `estimated_time`, `real_time_spent`, `cost_estimate`).
  - Added foreign weak-link entities: `TicketResource` (Inventory coupling) and `StopLog` (Production OEE coupling).
  - Implemented the Outbox Pattern (`OutboxEvent` & `OutboxWorker`) to asynchronously push `TicketCreatedEvent` contracts over HTTP without tight blocking.
  - Created CQRS-style Handlers (`CreateTicketCommand`, `ConsumeResourcesCommand`).

#### Phase 16: Industrial Strengthening & Sanitization ✅
- **Status**: Completed (2026-03-05)
- **Sanitization**: Resolved **12 governance violations** (Root pollution moved, Multi-tenant models updated, Audit integrated).
- **Compliance**: `AuditService.track` integrated in `TicketCommandHandler` for professional forensic auditing.

---

### Audit Report (2026-03-08)

#### 🔴 Critical Bugs Found (3)
1. **`outbox_worker.py`**: Import from non-existent `app.db.session` — should be `app.dependencies.database`.
2. **`integration_events.py`**: Missing `import uuid` module — `uuid.uuid4` reference on line 13 will crash at runtime.
3. **`ticket_routes.py`**: Orphan `@router.post("/internal")` decorator on line 22 with no handler function — causes silent double-registration of `POST /`.

#### 🟡 Technical Debt (7 items)
| # | Item | Severity |
|---|---|---|
| D1 | `ConsumeResourcesCommand` doesn't dispatch to Kardex | 🔴 High |
| D2 | `AuditService.log_action` is a stub (console `print()`) | 🟡 Medium |
| D3 | Zero test coverage — no `tests/` directory exists | 🔴 High |
| D4 | No Alembic migrations | 🟡 Medium |
| D5 | `reference_code` COUNT() not scoped by `company_id` — multi-tenant collision | 🟡 Medium |
| D6 | `TicketRead` DTO missing `history`, `resources`, `stop_logs` | 🟡 Medium |
| D7 | `OutboxWorker` URL hardcoded to `localhost:8008` | 🟡 Medium |

#### ✅ Architecture Validated
- **CQRS Pattern**: Working (`CreateTicketCommand`, `ConsumeResourcesCommand`).
- **Outbox Pattern**: Implemented (`OutboxEvent` → `OutboxWorker`), aside from broken import.
- **SHA256 Debouncing**: Active and correctly hashing `company_id + warehouse_id + product_id + priority`.
- **Multi-Tenant Compliance**: All 6 models inherit `MultiTenantBase`.
- **API Response Format**: `{status, data, message, meta}` compatible with Angular frontend interceptor.

---

### Phase 1: Critical Bug Fixes & Multi-Tenant Blindaje ✅
- **Status**: Completed (2026-03-08)
- **Fixes Applied**:
  - ✅ **Bug 1**: `outbox_worker.py` — Fixed broken import `app.db.session` → `app.dependencies.database`.
  - ✅ **Bug 2**: `integration_events.py` — Added missing `import uuid` for `uuid.uuid4()` default_factory.
  - ✅ **Bug 3**: `ticket_routes.py` — Implemented `create_internal_ticket` handler for orphan `/internal` decorator with SHA256 debouncing + `X-Company-ID` / `X-Service-Signature` headers.
  - ✅ **D5**: `ticket_service.py` — Scoped `reference_code` generation COUNT by `company_id` to prevent multi-tenant collisions.

---

### Phase 2: Architectural Stabilization ✅
- **Status**: Completed (2026-03-08)
- **Changes Applied**:
  - ✅ **Outbox Config**: `outbox_worker.py` — Migrated hardcoded `localhost:8008` URL to `common.config.settings` with Docker-network default fallback.
  - ✅ **DTO Enrichment**: `ticket_dto.py` — `TicketRead` now includes `history`, `resources`, `stop_logs`, and MES metrics (`module_origin`, `area`, `estimated_time`, `real_time_spent`, `cost_estimate`). Added `TicketResourceRead` and `StopLogRead` DTOs.
  - ✅ **Tenant Cleanup**: Removed redundant `company_id` from `TicketRead` (managed by JWT).
  - ✅ **Soft-Delete**: Added `DELETE /tickets/{id}` endpoint with `is_active=False` + status set to `CANCELED`.
  - ✅ **Audit**: `soft_delete_ticket` records `TicketHistory` entry and triggers `AuditService.log_action`.

---

### Phase 3: Kardex Integration ✅
- **Status**: Completed (2026-03-08)
- **Changes Applied**:
  - ✅ **Inventory Client**: Created `IInventoryClient` port and `HttpInventoryClient` adapter using `httpx` to trigger Kardex `OUT` transactions.
  - ✅ **CQRS Atomic Logic**: Modified `TicketCommandHandler.handle_consume_resources` to execute the HTTP dispatch *before* the local DB commit. Fast-fail uses `HTTPException` to safely abort the transaction upon external errors.
  - ✅ **Price Validation Metadata**: Added `warehouse_id` to `ConsumeResourceDto` ensuring `inventory_service` receives proper contextual data for accurate material costing.
  - ✅ **Endpoint Exposed**: Implemented `POST /tickets/{id}/consume-resources` returning standard `ApiResponse`.

---

## Missing Logic / Pending Backlog
- Automated tests for `create_internal_ticket_with_debouncing` (burst window mocking).
- Background Consumer to process state updates originated from other services.
- GraphQL/REST endpoints for frontend dashboard (MTTR, MTBF, OEE).

---

### Phase 4: Remediación Crítica & Auditoría (Nivel 2 y 3) ✅
- **Status**: Completed (2026-05-01)
- **Fixes Applied**:
  - ✅ **Precisión Numérica**: Refactorizado `cost_estimate` en `ticket.py` a `Numeric(18, 8)` y `Decimal` en DTOs para evitar pérdida de precisión financiera en Kardex.
  - ✅ **Seguridad Inter-servicio (HMAC)**: Implementada validación criptográfica HMAC-SHA256 en `/internal` usando `SECRET_KEY` para bloquear inyección de tickets falsos.
  - ✅ **Auditoría Forense Estándar**: Sustituidas las llamadas a `audit_repo` por `AuditService.track()` con parámetros estandarizados (`resource`, `metadata`).
  - ✅ **SECRET_KEY Alineado**: Corregido `docker-compose.yml` para usar `DEV_SECRET_KEY_CAMBIAME_EN_PROD_12345` (era `changeme`), alineando con el resto de servicios.
  - ✅ **Subscription Seed**: Actualizado `subscription_service/scripts/seed.py` con `timedelta(days=3650)` para evitar bloqueos por suscripción vencida durante desarrollo.

---

### Phase 5: Expansión del Modelo de Dominio (Motor Operacional) ✅
- **Status**: Completed (2026-05-01)
- **Objetivo**: Transformar el servicio de helpdesk a Motor Operacional Industrial con 4 flujos de trabajo.
- **Changes Applied**:
  - ✅ **Enums Expandidos**: `TicketType` ahora incluye `Mantenimiento`, `Recibo Material`, `Tiempo Muerto`, `Escalación`.
  - ✅ **Modelo Expandido**: `Ticket` incluye 7 nuevos campos:
    - `source_service` (String) — Origen del ticket: INVENTORY, MES, MANUAL, SENSOR
    - `station_id` (UUID, indexed) — Weak ref a estación MES para Mantenimiento
    - `reported_by_id` (UUID) — Para notificaciones de cierre al reportante
    - `parent_ticket_id` (UUID, FK self-ref) — Jerarquía de escalación
    - `auto_close_on_event` (String) — Evento de cierre automático: KARDEX_ENTRY_CONFIRMED
    - `escalation_level` (Integer, default=0) — Nivel de escalación jerárquica
    - `resolved_at` (DateTime TZ) — Para cálculo de MTTR
  - ✅ **DTOs Expandidos**: `TicketRead`, `TicketCreate`, `TicketUpdate`, `InternalTicketCreate` actualizados.
  - ✅ **CQRS Expandido**: `CreateTicketCommand` y handler propagan todos los campos nuevos.
  - ✅ **Self-referential Relationship**: `parent_ticket` ↔ `child_tickets` para jerarquía.
- **Validación**: Docker build + Uvicorn startup exitoso. Backward compatible.

---

### Estado Actual de Fases (Actualización de Log 2026-05-01)

---

### Phase 6: Notificaciones & Auto-cierre ✅
- **Status**: Completed (2026-05-01)
- **Features**:
  - ✅ **Outbox Dispatcher**: Integración del motor de notificaciones para `TicketCreated` y `TicketStatusChanged`.
  - ✅ **Auto-cierre**: Lógica de cierre automático de tickets de `Recibo Material` al confirmar entrada en Kardex.

---

### Phase 7: Escalación Dinámica Multi-tenant ✅
- **Status**: Completed (2026-05-01)
- **Features**:
  - ✅ **Escalation Matrix**: Implementación de `EscalationRule` con fallback jerárquico (`Producción` -> `Almacén` -> `Soporte`).
  - ✅ **EscalationWatcher**: Script industrial funcional para escaneo de SLAs y disparo de escalaciones automatizadas.
  - ✅ **Soporte AI (Preview)**: Integración de lógica de auto-respuesta AI para tickets de tipo `SUPPORT`.

---

### Phase 7.5: Remediación de Enrutamiento & Sync Frontend ✅
- **Status**: Completed (2026-05-01)
- **Fixes Applied**:
  - ✅ **Routing Remediation**: Eliminado prefijo redundante `/tickets` en el `APIRouter` de `ticket_routes.py` para evitar rutas anidadas (`/tickets/tickets`) al montar en el monolito.
  - ✅ **Constants Endpoint**: Implementado `GET /config/constants` para exponer Enums de forma segura al frontend.
  - ✅ **Frontend Alignment**: Sincronizado `SupportService` para consumir las constantes y habilitar reactividad total.

---

### Estado Actual de Fases (Actualización de Log 2026-05-01)

### Phase 7.6: Consolidación Industrial ✅
- **Status**: Completed (2026-05-02)
- **Changes Applied**:
  - ✅ **Alembic Migration**: Generada y aplicada la migración `ba0421906267` que "congela" los campos de las Fases 5-7.
  - ✅ **Sincronización DB**: Creada base de datos `tickets_db` e inicializado el esquema completo con precisión financiera `Numeric(18, 8)`.
  - ✅ **Persistencia Outbox**: Refactorizado `scripts/outbox_worker.py` con loop infinito `while True`, manejo de señales SIGTERM y re-intento ante fallos de red.
  - ✅ **Docker Orchestration**: Registrado `tickets-outbox-worker` en `docker-compose.yml` con `restart: always`.
  - ✅ **Fix Imports**: Normalizados todos los imports de `app.` a `tickets_app.` en `env.py`, `outbox_worker.py` y `escalation_watcher.py`.

---

### Estado Actual de Fases (Actualización de Log 2026-05-02)

| Fase | Estado | Descripción |
|---|---|---|
| Fase 1-7.5 | ✅ COMPLETADA | Lógica de negocio, CQRS, HMAC, Escalación Matrix |
| Fase 7.6: Consolidación | ✅ COMPLETADA | Alembic Migration, Outbox Worker Persistence, Docker Setup |
| Fase 8: Mantenimiento + StopLog | 🚀 SIGUIENTE | Auto-StopLog + costo downtime |
| Fase 9: Dashboard KPIs | 📋 PLANIFICADA | MTTR, MTBF, OEE, SLA compliance |

---

## Missing Logic / Pending Backlog
- [ ] Automated tests for `create_internal_ticket_with_debouncing` (burst window mocking).
- [ ] Implementación de `while True` loop en `escalation_watcher.py` (Validar si ya está activo en dev).
- [ ] KPI REST endpoints (MTTR, MTBF, OEE).
- [ ] Frontend: Dashboard component para visualización de KPIs industriales.

