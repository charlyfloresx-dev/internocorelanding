# 📜 MES Service - SERVICE LOG

> **Service:** MES Service (Port 8005)
> **Status:** Active / Manufacturing Core — ✅ 100% Auditor Compliant

---

### [2026-05-27] - Phase 149: WorkOrder CRITICAL Bug Fix ✅

- **`models/work_order.py`**: Añadidas dos columnas ausentes: `alias: Mapped[Optional[str]]` (String 100, nullable) y `release_date: Mapped[Optional[datetime]]` (DateTime tz-aware, nullable). El handler las requería desde Phase 137 pero no existían en el modelo → `WorkOrder()` constructor fallaba en runtime.
- **`core/handlers/work_order_handler.py`**: Corregidos 4 mismatches entre `CreateWorkOrderCommand` y el modelo SQLAlchemy:
  - `order_qty=command.order_qty` → `order_quantity=command.order_qty` (nombre correcto del campo)
  - `due_date=command.due_date` → `request_date=command.due_date` (nombre correcto del campo)
  - `status="PLANNED"` → `status="DRAFT"` (alinea con enum del modelo: DRAFT/RELEASED/IN_PROGRESS/COMPLETED/CLOSED)
  - `release_date` y `alias` ahora tienen columnas reales en el modelo
- **`alembic/versions/007_add_workorder_alias_release_date.py`**: Migración `ADD COLUMN alias VARCHAR(100) NULL` + `ADD COLUMN release_date TIMESTAMPTZ NULL` en `mes_work_orders`. Down: `DROP COLUMN`.
- **Referencia Legacy**: `Interno.Production` no tenía `alias` — fue adición del handler sin contraparte en modelo.
- **Status**: ✅ COMPLETED — `POST /api/v1/mes/work-orders/` funcional.

### [2026-05-26] - Phase 135: Core Matemático ✅
- **`alembic/env.py`**: Eliminado bloque de debug prints (líneas 20-27). Añadido `version_table="alembic_version_mes"` en `run_migrations_offline()` y `do_run_migrations()`. Gold Standard cumplido.
- **Migration `006_mes_cycle_time_and_breaks`**: `cycle_time_seconds INTEGER NULL` en `mes_standard_times` + `break_minutes INTEGER DEFAULT 60` en `mes_shifts`.
- **`Shift` model**: `break_minutes: Mapped[int] = mapped_column(Integer, default=60)` — reemplaza el hardcoded de 1h del legacy `Interno.HumanResource`.
- **`StandardTime` model**: `cycle_time_seconds: Mapped[Optional[int]]` — RunTime por pieza en segundos (legacy: `OperationTime.RunTime`).
- **`manufacturing_math.py`**: `calculate_tak_time_seconds()` acepta `cycle_time_seconds` opcional con fallback a fórmula. Nueva `calculate_theoretical_capacity(cycle_time_seconds, available_minutes)` → piezas teóricas por turno.
- **`ShiftService`**: `calculate_available_minutes(shift)` — aritmética overnight `(24h − start) + end` para T2 16:30–01:45. `getattr(shift, 'break_minutes', 60)` seguro contra shifts legacy.
- **Status**: ✅ COMPLETED

---

### [2026-05-26] - Phase 136: Planning Bulk-load ✅
- **`schemas/planning.py`**: `PlanningEntry` con `@field_validator('date')` que rechaza fechas pasadas. `BulkLoadResponse` con `{scheduled, skipped, errors}`.
- **`api/v1/endpoints/planning.py`**: `POST /api/v1/mes/planning/bulk-load` — `begin_nested()` por entrada (fallo parcial no aborta el lote), `company_id` del JWT (Muro de Hierro), `require_scope(["mes:write"])`, validaciones de WorkOrder y Resource por company.
- **`main.py`**: Router registrado en `/api/v1/mes/planning`.
- **Status**: ✅ COMPLETED

---

### [2026-05-26] - Phase 137: Seguridad y Calidad ✅
- **`downtime.py`**: IDOR eliminado — `tech_user_id`/`admin_user_id` del cliente → `uuid.UUID(current_user.sub)` del JWT. `company_id` añadido como filtro en todos los UPDATE (`respond`, `close`, `admin-close`) y en `get_active_downtimes`. `require_scope` en los 5 endpoints. `DowntimeAdminClose` sin `admin_user_id` (campo eliminado del body).
- **`scan.py`**: `float(ledger_entry.qty)` → `str(Decimal(ledger_entry.qty))` — PRIMITIVE_FLOAT_VIOLATION resuelto. `require_scope(["mes:write"])` añadido.
- **`dashboard.py`**: `require_scope(["mes:read"])` en `/oee`, `/graphic`, `/pareto`. Router duplicado eliminado.
- **`labor.py`**: `require_scope` en los 4 endpoints. `company_id` añadido al UPDATE de `clock_out`.
- **`work_order.py`**: `WHERE company_id == company_id` aplicado en `get_work_orders`. Fix BUG-02: `db.get(WorkOrder, order_number)` → `select().where(order_number == ...)` (buscaba por PK UUID, no por string).
- **`api/v1/endpoints/production.py`**: Nuevo endpoint `POST /api/v1/mes/production/scrap` — persiste `ScrapEntry` verificando ownership del `ProductionRun` por `company_id`.
- **Code Graph**: 100% Compliance, 0 CRITICALs, 0 WARNINGs post-fase.
- **Status**: ✅ COMPLETED

---

### [2026-05-26] - Phase 134: Análisis Legacy + Plan de Refactorización 📋

**Tipo:** Sesión de planificación — sin cambios de código.

**Auditorías realizadas esta sesión:**
- Auditoría de seguridad mes_service: 10 CRITICOs identificados (bugs runtime + IDOR + scopes). Varios ya resueltos en phases previas (17.5, 20.5).
- Análisis cruzado con 4 proyectos legacy .NET: `Interno.Production`, `Interno.HumanResource`, `Interno.DJO`, `Interno.Outset`.

**Hallazgos que confirman el estado actual:**
- Phase 17.5 ya resolvió: `ResourceResult → ProductionRun` renaming, `NameError/IndentationError`, BOM Guard, Andon escalation.
- Phase 16 ya resolvió: `quality = 1.0` bug → `ScrapEntry` + `ManufacturingMath` con factor de calidad real.
- Phase 20.5 ya resolvió: interfaces de repositorio, zero infrastructure imports en services.
- Phase 3 ya resolvió: `ScheduleProduction` command con actualizaciones atómicas.

**Gaps confirmados por análisis legacy (pendientes de implementación):**

| Gap | Legacy confirma | Fase |
|---|---|---|
| `cycle_time_seconds` (RunTime) | Production + Outset usan RunTime | Phase 135 |
| Overnight shift aritmética | Legacy `if End < Start → 24h - Start + End` | Phase 135 |
| `alembic/env.py` sin `version_table` | Gold Standard violation | Phase 135 |
| Debug prints en `alembic/env.py` | Expone paths del servidor | Phase 135 |
| `POST /planning/bulk-load` | Legacy PlanningController 82 cols | Phase 136 |
| Downtime IDOR (tech_user_id / admin_user_id del cliente) | Legacy tampoco lo tenía | Phase 137 |
| Scopes faltantes en scan/dashboard/labor | Legacy no tenía auth | Phase 137 |
| `POST /scrap` endpoint en API | Legacy tenía ScrapEntry visible | Phase 137 |

**Funcionalidad legacy descartada (no genérica):**
- STBL, Kanban/Bin picking, Supplier Scorecard → pertenece a `purchasing_service` futuro
- Integración Tulip MES → específico a clientes con Tulip instalado
- Windows AD auth → reemplazado correctamente por JWT
- Rout/Routing multi-operación → fase futura

---

### [2026-03-07] - Phase 20.5: Architectural Shielding & Repository Pattern ✅
- **Status**: ✅ COMPLETED — **0 CRITICAL errors** in Auditor v4.1
- **Repository Pattern**: Defined 6 domain repository interfaces:
  - `IShiftRepository`, `IResourceRepository`, `IWMSClient`
  - `IProductionEventRepository`, `IProductionSessionRepository`, `IManufacturingLedgerRepository`
- **Implementations**: Created SQLAlchemy repository implementations + `SQLAlchemyWMSClient` adapter.
- **Service Refactoring**: `KPIService`, `ScannerService`, `ProductionService`, `ShiftService` — zero infrastructure imports.
- **DI Wiring**: Updated `dependencies.py` and all API endpoints for proper injection.
- **Config**: Added `ALGORITHM`/`SECRET_KEY` to MES `config.py`.
- **Import Migration**: Updated all model imports from `common.domain.entities` to `common.models`.

---

### [2026-03-05] - Phase 16: Industrial Strengthening
- **Status**: ✅ COMPLETED
- **Features**: LMPU benchmarking, Scrap tracking, and Quality factor integration.
- **Math**: `ManufacturingMath` now supports improvement % comparison vs historical targets.

### [2026-03-06] - Phase 17.5: Industrial MES Categories & Stabilization ✅
- **Status**: ✅ COMPLETED
- **Stabilization**: Resolved `NameError` and `IndentationError` in models and API endpoints.
- **Consistency**: Standardized `ResourceResult` renaming to `ProductionRun` across models, services, and APIs.
- **OpenAPI**: Successfully extracted `mes.json` spec.
- **Downtime Categories**: Standardized Equipment, Management, Material, Method, Personal, and Service categories ([seed_mes_robust.py](file:///c:/API/interno/backend/mes_service/scripts/seed_mes_robust.py)).
- **Labor Options**: Standardized activities including Enfermería, RRHH, Auditorías, etc.
- **Control de Piso**: Actualización del pulso en tiempo real al registrar producción.
- **BOM Guard**: Bloqueo y congelación de versión de BOM por cada WorkOrder.
- **Andon**: Escalación automática para fallas mecánicas (Nivel Director incluido).

### [2026-03-05] - Phase 3: Operational Pulse & Real-time Reporting
- **Comandos**: Implementación de `ScheduleProduction` y `ReportHourlyProduction` con actualizaciones atómicas.
- **Calidad**: Creación de la entidad `ScrapEntry` y ajuste de la fórmula OEE para incluir el factor de Calidad.
- **Integración**: Emisión del evento `ProductionReported` al finalizar cada reporte horario exitoso.
- **Matemáticas**: Optimización de `ManufacturingMath` para manejar cálculos granulares por hora.

### [2026-03-05] - Phase 2: ProductionRun & Read Models Migration
- **Refactorización**: Monolito legacy `Result.cs` dividido en entidades normalizadas: `ProductionRun`, `DowntimeEvent`, `LaborAllocation`.
- **CQRS**: Implementación del comando `CloseProductionRun` en `app/core/commands/close_production_run.py`.
- **Read Models**: Creación de `RunMetricsSnapshot` (OEE, LMPU, TakTime) y `HourlyProductionSnapshot`.
- **Domain Logic**: Servicio matemático extraído en `manufacturing_math.py` para cálculos de eficiencia.
- **Persistencia**: Migración Alembic `04dfb9667459_mes_models.py` con el nuevo esquema de la BD.

### [2026-03-04] - Phase 22: Governance Sanitization & Structure Migration
- **Refactorización**: Movimiento de modelos Pydantic (Command, Response) a `app/schemas/production_event.py`.
- **Limpieza**: Sancionamiento de la entidad `ProductionEvent` en `app/models/` como entidad pura SQLAlchemy.
- **Cumplimiento**: Verificación de herencia de `MultiTenantBase` y `AuditBase`.

### [2026-03-03] - Activación de MES Service
- **Nacimiento**: Scaffolding inicial del servicio de manufactura.
- **Modelado**: Definición de `ProductionEvent`, `WorkOrder`, `Resource`, `Shift` y `Downtime`.
- **Enums**: Integración de tipos de eventos de producción en `common`.
