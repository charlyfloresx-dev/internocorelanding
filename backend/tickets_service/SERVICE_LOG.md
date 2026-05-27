# Tickets Service Log

## Overview
The InternoCore Tickets Service evolved from a generic helpdesk module to the **Operational Motor** of the enterprise architecture (Phase 10). It orchestrates actions between users, production floors (MES), and inventory control (ERP).

### Service Stats
| Metric | Value |
|---|---|
| **Source Files** | 24 |
| **Data Models** | 7 (Ticket, Comment, History, Resource, StopLog, OutboxEvent, **TicketAction**) |
| **API Endpoints** | 9 REST |
| **Test Coverage** | 15% (Debouncing logic) |
| **Last Audit** | 2026-05-27 |

---

## 🚀 Log de Cambios y Estabilización

### [2026-05-27] Phase 142: TicketAction (CAPA) + Triage Multi-Assignee Fix ✅
- **Triage schema bug:** `TicketTriage` schema no tenía `collaborator_id` ni `external_contact_id`. Pydantic los ignoraba; el service usaba `getattr(cmd, "new_collaborator_id", None)` — siempre `None`. Fix: campos añadidos al schema, service lee directamente.
- **`TicketAction` model:** Nuevo modelo basado en legacy `Interno.Actions`. Campos: `description` (500), Triple Identity (`assigned_to_id | collaborator_id | external_contact_id`), `commit_date`, `escalation_date`, `closed_date`, `is_closed`. Relationship `ticket.actions`.
- **Migration `003_add_ticket_actions.py`:** Tabla `ticket_actions` con índices en `ticket_id`, `company_id`, `assigned_to_id`, `is_closed`. Guard `_table_exists`.
- **Endpoints nuevos:** `POST /{id}/actions` (scope `ticket:triage`), `GET /{id}/actions` (scope `ticket:read`), `PATCH /{id}/actions/{aid}/close` (scope `ticket:triage`).
- **Schemas:** `TicketActionCreate` (validador: al menos un responsable), `TicketActionClose`, `TicketActionRead`. `TicketRead` incluye `actions: []`.
- **Frontend:** Sección "PLAN DE ACCIONES" en drawer triage. Signals: `actions`, `isLoadingActions`, `isAddingAction`, `newActionText`, `newActionDate`, `showActionForm`. Métodos: `loadActions`, `addAction`, `closeAction`, `actionAssigneeLabel`.
- **Angular loop fix definitivo:** `ngOnInit()` skips `loadTickets()` cuando `view() === 'triage'`. `_syncIds()` usa `untracked(() => selectedIdentities())` para evitar reactive dependency en SideDrawer effect.

### [2026-05-22] Phase 127: Sentinel Mobile Dashboard Enrichment & Field Alignment ✅
- **Mapeo de Campos en Dart (`ticket_models.dart`)**: Agregados campos `assignedToId`, `area` y `ticketType` al modelo `Ticket` mapeados desde los payloads del backend.
- **Rutas y Endpoint en Mobile (`ticket_repository.dart`)**: Modificada la petición del listado de tickets en la app móvil para llamar a `GET tickets/mine` en lugar de `GET tickets/` (que es el endpoint de administración global de la empresa).
- **Dashboard Móvil Mejorado (`tickets_screen.dart`)**: 
  - Añadido indicador de prioridad lateral de color con código de color de alta visibilidad (Crítica = Rojo, Alta = Naranja, Media = Amarillo, Baja = Azul).
  - Añadido badge de prioridad con texto estilizado en la parte inferior de la tarjeta.
  - Añadido indicador de asignación: "👤 Asignado" (o nombre del operador si está disponible) vs "⚠️ Sin Asignar".
  - Añadido tag visual para el área operativa del ticket (ej., Producción, Almacén, Mantenimiento).
- **Verificación de Soporte del Backend**:
  - Validado que el DTO `TicketRead` del backend define exactamente los campos `assigned_to_id`, `area`, `ticket_type` y son expuestos correctamente.
  - Verificado el cumplimiento de Code Graph de `tickets_service` al 100% (0 errores) y pruebas HMAC funcionales para endpoints de canal interno.

### [2026-05-22] Phase 126: Multi-Tenant Isolated Ticket Consecutive Number Fix ✅
- **Base de Datos & Migraciones**: Creada migración de Alembic `002_ref_code_composite.py` para reemplazar la restricción única global `tickets_reference_code_key` por un índice y restricción compuesta `tickets_company_id_reference_code_key` sobre `(company_id, reference_code)`. Migración ejecutada exitosamente en el contenedor `interno-tickets-dev`.
- **Modelos SQLAlchemy (`ticket.py`)**: Removido `unique=True` de la columna `reference_code` y agregada la restricción a `__table_args__` del modelo `Ticket`.
- **Algoritmo de Consecutivos (`infrastructure/repositories/ticket_repository.py`)**: `_generate_ref_code` ahora busca tickets mediante el patrón `%-{current_year}-%` filtrado por `company_id`. Cuenta correctamente todos los prefijos del tenant (`IT-`, `SEC-`, `EXT-`, `TKT-`) y emite folios continuos de forma atómica y aislada por empresa (ej. genera `TKT-2026-0008` tras los 7 tickets pre-sembrados).

### [2026-05-22] Phase 125: Sentinel Mobile Ticket Integration & Support Drawer Sync ✅
- **Dart DTOs (`ticket_models.dart`)**: Modelos `Ticket`, `TicketCreateRequest` y `TicketComment` creados para mapear los payloads del backend.
- **Repositorio HTTP (`ticket_repository.dart`)**: Consumo HTTP integrado vía `Dio` e inyección de dependencias `GetIt`. Inyección automática de `company_id` local desde `SharedPreferences` para aislar el multitenancy con cero fricción operacional.
- **Gestión de Estados (`tickets_bloc.dart`)**: Eventos y estados inyectados globalmente en la jerarquía de la app móvil para actualización en tiempo real de las bandejas `/mine` del operador.
- **Interfaces Modernas de Alto Contraste ("Uber-Style")**:
  - `tickets_screen.dart`: Listado dinámico con estadísticas rápidas (pendientes vs cerrados) y estados vacíos.
  - `create_ticket_screen.dart`: Formulario express minimalista con asunto, prioridad y descripción.
  - `ticket_chat_screen.dart`: Chat fluido con burbujas alineadas para operador vs supervisor, cabecera de metadatos y auto-scroll.
- **Calidad de Código**: Ejecución de `flutter analyze` exitosa con 0 warnings y 0 errores.

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

