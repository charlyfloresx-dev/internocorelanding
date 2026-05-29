# 📜 MES Service - SERVICE LOG

> **Service:** MES Service (Port 8005)
> **Status:** Active / Manufacturing Core — ✅ 100% Auditor Compliant

---

### [2026-05-29] - Phase 156-B/C/D: Angular Admin UI + Planning + WO Material Flow ✅

**Phase 156-B — Angular Admin UI:**
- `ResourceConfigComponent` (`/production/config/resources`): tabla con tipo/código, acciones, filtro
- `ShiftConfigComponent` (`/production/config/shifts`): tabla con breaks expandibles, filtro empresa/recurso
- `ProductionAreaFormComponent` (drawer): Facility CRUD + ProductionArea CRUD con selector de facilidad
- `ResourceFormComponent`, `ShiftFormComponent`, `ResourceBulkFormComponent` (todos en drawer)
- `POST /mes/resources/bulk`: batch create con skip de duplicados
- `ShiftService` Angular con full CRUD + break management
- Navigation: `prod-planning`, `prod-config-resources`, `prod-config-shifts`, `prod-item-config`

**Phase 156-C — Shift CRUD REST:** (ver entrada anterior)

**Phase 156-D — Planificación + WO:**
- `DailyPlanningComponent` (`/production/planning`): date picker, recursos por fila, runs asignados, inline modal asignar WO
- `WorkOrderFormComponent` (drawer): WO types cargados de API, banner de alerta material
- `planning.py`: FIXES críticos (`entry.date→production_date`, `status` no existe, falta `tenant_id`) + GET/POST/DELETE `/runs`
- `GET /mes/orders/types`: catálogo dinámico de tipos de OT desde enum
- `WorkOrderHandler`: REMOVIDA explosión automática de BOM. WO crea solo `PLANNED_OUTPUT` + `material_status="PENDING_ISSUE"`
- `POST /mes/orders/{n}/issue-material`: surtido explícito → explota BOM → `MATERIAL_INPUT` lines + `material_status="ISSUED"`
- Badge `⚠️ Sin surtir` + botón "Surtir Material" en `DailyPlanningComponent`

**Decisión:** BreakGroups → HCM. `Resource.break_group_id` pendiente conectar a `/hcm/break-groups`.

---

### [2026-05-29] - Phase 156: MES Cold-Start — seed_mes_config + Migration 010 + Shift CRUD REST ✅

**Migration 010** (`010_fix_shift_code_unique_per_company.py`):
- Corrige `UQ(code)` global → `UQ(company_id, code)` en `mes_shifts`. Bug: bloqueaba multi-tenant con códigos compartidos (MAT/VES/NOC).

**`scripts/seed_mes_config.py`** (Phase 156-A):
- Para 3 empresas × [1 Facility, 3 Areas, 4 Resources, 3 Shifts, 6 ShiftBreaks, 5 StandardTimes].
- Acepta `db_url` parámetro para tests (evita `CORE_DATABASE_URL` → `dbname`).
- Idempotente via `uuid5` determinístico.

**`api/v1/endpoints/shift.py`** (Phase 156-C — FULL CRUD):
- `POST /` create, `GET /{id}` with breaks, `PATCH /{id}` partial update, `DELETE /{id}` soft-delete.
- `GET /{id}/breaks`, `POST /{id}/breaks`, `DELETE /{id}/breaks/{brk_id}`.
- `ShiftRead` ahora incluye `breaks[]` embebidos y expone tiempos como "HH:MM" string.

**Tests**: 87 integration — 0 regresiones. Code Graph: 0 CRITICALs.

---

### [2026-05-28] - Phase 154: Resource Monitor Domain — Facility, ProductionArea, Resource expanded, ShiftBreak, GraphicService ✅

**Parte 1 — Modelos + Migration 009:**
- **`models/facility.py`**: `Facility(MultiTenantBase)` — `mes_facilities`, `UQ(company_id, code)`, `location_description`.
- **`models/production_area.py`**: `ProductionArea(MultiTenantBase)` — `mes_production_areas`, `facility_id FK SET NULL`.
- **`models/resource.py`** (expandido): añadidos `description`, `resource_type (CELL|MACHINE|AREA|LINE)`, `capacity Decimal`, `warehouse_id UUID` (soft FK — Iron Wall ADR-02, sin FK DB hacia `inventory_db`), `production_area_id FK`, `code` resizado a `VARCHAR(13)` (paridad con legacy `Warehouse.Code`), `UQ(company_id, code)`.
- **`models/resource_support_member.py`**: `ResourceSupportMember` — `collaborator_id` soft FK (Iron Wall hacia `hcm_db`), `role VARCHAR(50)` (acepta valores de `HumanResource.Catalog.Autority`).
- **`models/shift_break.py`**: `ShiftBreak` — portado de `Interno.HumanResource.Models.Catalog.Break + BreaksGroup`: `code (VARCHAR 15)`, `label`, `break_type (BREAK|MEAL|MAINTENANCE)`, `start_time`, `end_time`, `duration_minutes`. Simplifica `BreaksGroup` → breaks directamente vinculados al `Shift`.
- **`alembic/versions/009_...py`**: usa `_base_cols()` para incluir todos los campos de `MultiTenantBase` (`group_id`, `version_id`, `is_active`, `deleted_at`, `transaction_id`). Bug corregido: `index=True` en `sa.Column()` dentro de `create_table` crea el índice internamente — no usar `op.create_index()` duplicado.
- **`api/v1/endpoints/resource.py`**: CRUD completo + `GET/POST /facilities`, `GET/POST /production-areas`.
- **Tests**: 18 integration tests contra `mes_db` real.

**Parte 2 — ResourceGraphicService:**
- **`services/graphic_service.py`**: `ResourceGraphicService` porta `ResultController.GetGraphic()` del legacy .NET:
  1. Detecta turno activo (resource-level override → fallback company-wide).
  2. Genera slots horarios `[shift.start .. shift.end)`, incluyendo turnos nocturnos cross-midnight.
  3. Aplica `ShiftBreak`s: reduce `disponible[i]` en horas para slots que solapan un descanso.
  4. Distribuye `planned_qty` como `Meta[]` usando `StandardTime.set_time_hours` (fallback: `round(qty/horas)`).
  5. Carga `HourlyProductionSnapshot` para `actual[]` por hora.
  6. Computa `missing/excess/efficiency` por slot.
  7. Retorna `ResourceGraphicResponse`: `hours[], breaks[], cumulative_table[], total_goal, total_actual`.
- `get_active_workorder()`: WO con `status=IN_PROGRESS` para el recurso hoy.
- `get_planned_workorders()`: WOs `DRAFT+IN_PROGRESS` del turno actual.
- **3 endpoints HTTP**: `GET /{code}/graphic`, `/{code}/active-workorder`, `/{code}/planned-workorders`.
- **Tests**: 11 integration tests — **55/55 pasando** (0 regresiones).

---

### [2026-05-28] - Phase 152: Scan Pattern Validation (MES) ✅

- **`schemas/scan_pattern.py`**: DTO `ScanPatternRead` local (sin cross-service import — regla Muro de Hierro).
- **`services/pattern_validator.py`**: `PatternValidatorService.validate()` — función pura, `re.fullmatch()`, patrones ordenados por `priority`, retorna primer `error_message` o `None`. 10 unit tests, 100% passing.
- **`infrastructure/clients/master_data_client.py`**: `MasterDataClient.get_scan_patterns()` — httpx best-effort (timeout 3s, retorna `[]` en cualquier error de red/HTTP).
- **`services/scanner_service.py`**: `_MULTI_COUNT_PATTERN` ya existía; añadido 6° argumento `master_data_client`. En `process_scan()`: stripping del prefijo multiplicador antes de validar, llamada best-effort a `get_scan_patterns()`, raise `BusinessRuleException` solo si el input no matchea un patrón activo.
- **`dependencies.py`**: `get_master_data_client()` registrado.
- **`api/v1/endpoints/scan.py`**: `master_data_client` inyectado vía `Depends`.
- **`schemas/planning.py`**: Fix `production_date` (renombrado de `date` para evitar shadowing del tipo `date` importado — bug preexistente que impedía startup).
- **Tests**: 19 tests passing (unit + refactor de `test_mes_core.py` — eliminados 4 xfails, reemplazados por 6 tests que cubren `ShiftService.is_time_in_shift`, `_MULTI_COUNT_PATTERN` y `KPIService._get_total_downtime`).
- **Status**: ✅ COMPLETED — 19 passed, 0 xfail, 0 CRITICAL en Code Graph.

---

### [2026-05-28] - Phase 151: manufactured_quantity + WO Status Transitions ✅

- **`IWorkOrderRepository`** (nueva): `increment_manufactured_quantity(work_order_id, qty, company_id)` — incrementa contador header + actual_quantity de PLANNED_OUTPUT line.
- **Status transitions automáticas:** DRAFT→IN_PROGRESS (primer scan), IN_PROGRESS→COMPLETED (manufactured_qty >= order_qty). Sobreproducción permitida.
- **`ScannerService`**: añadido `wo_repo: IWorkOrderRepository` al constructor. Post-ledger, llama increment best-effort (excepción en WO nunca rechaza scan).
- **`scan.py` endpoint**: inyecta `get_work_order_repo` vía Depends.
- **`dependencies.py`**: `get_work_order_repo()` registrado.
- **Tests**: 9 integration tests en `tests/integration/test_manufactured_quantity.py` — todos pasan.
- **Status**: ✅ COMPLETED — 29 tests passing en suite MES.

---

### [2026-05-28] - Phase 150: WorkOrder Document+Lines Pattern + Deployment ✅

- **Infraestructura desplegada:** `Dockerfile` reescrito (`app` → `mes_app`), `entrypoint.sh` creado, `docker-compose.dev.yml` + `nginx.conf` + `migrate_all.ps1` actualizados. `interno-mes-dev` corriendo en puerto 8005.
- **`models/work_order_line.py`** (NUEVO): `WorkOrderLine(MultiTenantBase)` — `work_order_id` con `ForeignKey("mes_work_orders.id", ondelete="CASCADE")`, `line_type: WorkOrderLineType` (MATERIAL_INPUT / PLANNED_OUTPUT / SCRAP), `planned_quantity / actual_quantity: Decimal`, `bom_id: UUID nullable`, unique constraint `(work_order_id, line_number)`.
- **`models/work_order.py`**: `wo_type: WOType` (nullable), `rout_id: UUID` (nullable), `lines: List[WorkOrderLine]` relationship (selectin, cascade delete-orphan).
- **`core/enums.py`**: Añadidos `WOType` (7 valores), `WorkOrderLineType`, `WorkOrderLineStatus`, `ProdIssueType`, `IssueType`.
- **`core/handlers/work_order_handler.py`**: BOM explode — `_fetch_bom()` GET best-effort a `inventory-service:8000`; N líneas `MATERIAL_INPUT` (qty = bom.qty × order_qty) + 1 línea `PLANNED_OUTPUT`. `begin_nested()` para CQRS atomicity.
- **`api/v1/endpoints/work_order.py`**: Nuevo endpoint `GET /{order_number}/lines → List[WorkOrderLineRead]`. `WorkOrderCreate` acepta `wo_type`.
- **Migration 008** (`008_wo_doc_pattern`): 3 enums PostgreSQL con DO blocks idempotentes; `tenant_id` a 10 tablas existentes; crea `mes_work_order_lines`.
- **Tests:** 17 integration tests contra `mes_db` real + 3 unit tests (todos pasan). Bug descubierto: `work_order_id` sin `ForeignKey` en modelo — corregido en esta fase.
- **Status**: ✅ COMPLETED — 22 tablas en mes_db, 8 migraciones, servicio live en puerto 8005.

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
