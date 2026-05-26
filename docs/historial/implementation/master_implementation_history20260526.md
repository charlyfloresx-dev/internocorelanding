# Historial Maestro de Implementación: 2026-05-26

Jornada de Security Hardening Sprint 2. Auditoría OWASP completa del ecosistema InternoCore y corrección del issue #3 (excepción raw expuesta + implementación de `AuditService.track()` con persistencia real en DB).

---

## 1. Phase 133 — Security Hardening Sprint 2

### Contexto

El skill `/security-and-hardening` fue aplicado como framework de auditoría sobre el core del ecosistema. La sesión combinó revisión de seguridad con corrección inmediata del hallazgo más crítico identificado en `common/` (la capa transversal que afecta a todos los microservicios).

### Auditoría realizada

Se revisaron los siguientes archivos:

| Archivo | Foco |
|---|---|
| `common/middleware.py` | JWT decode, tenant extraction, God Mode key comparison, exception handling |
| `common/security/cors_setup.py` | CORS origins, allowed headers, `X-Admin-Master-Key` exposure |
| `common/config.py` | `int_backend_cors_origins` — wildcard subdomain `*.vercel.app` |
| `common/security/dependencies.py` | God Mode bypass, JTI gate, scope matching |
| `kiosk_service/app/main.py` | CORS wildcard total `["*"]` — CRÍTICO |
| `asset_manager_service/asset_app/main.py` | CORS fallback peligroso `or ["*"]` |
| `tickets_service` (routers) | HMAC verification — confirmado correcto |

### Fix implementado: Exception raw + DB audit logging

#### Problema raíz

El bloque `except Exception as e` al final de `InternoCoreGlobalMiddleware.dispatch()` exponía el mensaje de excepción crudo directamente en el cuerpo HTTP de la respuesta 500:

```python
# ANTES (vulnerable):
traceback.print_exc()
return Response(
    status_code=500,
    content=json.dumps({
        "status": "error",
        "message": f"Critical Middleware Error: {str(e)}"   # Fuga de internals
        ...
    })
)
```

Esto permite a un atacante obtener:
- Rutas del sistema de archivos del servidor
- Nombres de tablas SQL y columnas
- Stack traces con líneas de código
- Tipos de excepción y mensajes de SQLAlchemy

Adicionalmente, `AuditService.track()` era un stub con `print()` + TODO comment — los errores críticos de middleware no quedaban registrados en ningún lugar trazable.

#### Solución — `common/middleware.py` (líneas 349–378)

```python
# DESPUÉS (seguro):
import asyncio
logger.error(
    f"UNHANDLED_EXCEPTION [{type(e).__name__}] method:{request.method} path:{path} trace:{transaction_id}",
    exc_info=True,   # Stack trace completo en logs del servidor, NO en respuesta HTTP
)

from common.services.audit_service import AuditService
asyncio.create_task(AuditService.track(
    user_id=str(user_id) if user_id else "SYSTEM",
    action="CRITICAL_MIDDLEWARE_ERROR",
    resource=path,
    metadata={
        "trace_id": transaction_id,
        "error_type": type(e).__name__,
        "error_message": str(e),
        "method": request.method,
        "path": path,
    },
))

return Response(
    status_code=500,
    content=json.dumps({
        "status": "error",
        "message": "An unexpected error occurred.",   # Sin detalles internos
        "meta": {"trace_id": transaction_id}          # trace_id para soporte
    }, cls=InternoCoreEncoder),
    media_type="application/json"
)
```

**Decisiones de diseño:**
- `exc_info=True` reemplaza a `traceback.print_exc()` — el stack trace va al logger estructurado (stdout del contenedor → sistema de logs centralizado), nunca al cliente
- El cliente recibe el `trace_id` para poder abrirlo en soporte sin exponer internals
- `asyncio.create_task()` es fire-and-forget — el audit no bloquea la respuesta HTTP aunque la DB esté lenta
- `action="CRITICAL_MIDDLEWARE_ERROR"` es buscable en `audit_logs` por `action` column

#### Solución — `common/services/audit_service.py` (método `track`)

`AuditService.track()` era un stub sin implementación desde que fue creado. Se implementó con persistencia real:

```python
# ANTES (stub):
@staticmethod
async def track(user_id: Any, action: str, resource: str, metadata: dict):
    print(f"[AUDIT] {action} | {resource} | {metadata}")
    # TODO: idealmente usariamos un background_task con un nuevo session_factory

# DESPUÉS (implementado):
@staticmethod
async def track(user_id: Any, action: str, resource: str, metadata: dict):
    import asyncio

    async def _persist():
        try:
            from common.infrastructure.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    await AuditService.log_action(
                        db=session,
                        user_id=user_id,
                        action=action,
                        entity_name=resource,
                        entity_id=metadata.get("trace_id"),
                        details=str(metadata),
                    )
        except Exception as exc:
            _logger.warning(f"AuditService.track DB persist failed: {exc}")

    asyncio.create_task(_persist())
    return True
```

**Decisiones de diseño:**
- `_persist()` abre su propia sesión con `AsyncSessionLocal` — no depende de la sesión del request (que puede estar cerrada o en fallo)
- `session.begin()` como context manager — commit automático al salir limpio, rollback automático en excepción
- Falla silenciosamente con `_logger.warning` — el tracking de audit nunca debe reventar el flujo del request
- Se añadió `_logger = logging.getLogger(__name__)` a nivel de módulo para logging estructurado consistente

**Nota:** `AsyncSessionLocal` conecta a `dbname` (la DB compartida del auth_service donde existe `audit_logs`). Para `hcm_service` y `subscription_service` que usan DBs propias, la tabla `audit_logs` aún no existe — está documentada como deuda técnica (ver plan `analizame-este-punto-para-resilient-kay.md`).

---

## 2. Hallazgos Pendientes (no corregidos en esta sesión)

### CRÍTICO — `kiosk_service` CORS wildcard

```python
# backend/kiosk_service/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # CRÍTICO — cualquier origen puede hacer requests credenciados
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Riesgo:** Un sitio malicioso puede hacer requests autenticados al kiosk service desde cualquier origen. Si `allow_credentials=True` también está presente, permite CSRF completo.

**Fix requerido:** Cambiar a lista de orígenes conocidos (mismo patrón que `common/cors_setup.py`).

### ALTO — `asset_manager_service` CORS fallback

```python
# backend/asset_manager_service/asset_app/main.py
allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"]   # Si la variable no está, abre todo
```

**Fix requerido:** Eliminar `or ["*"]` — si `BACKEND_CORS_ORIGINS` no está configurada, debe fallar al arrancar (fail-closed).

### MEDIO — Wildcard subdomain en config.py

```python
"https://*.vercel.app"   # Cualquier deployment de Vercel puede hacer requests credenciados
```

**Fix requerido:** Reemplazar por `"https://interno-core-frontend.vercel.app"` (dominio exacto).

### MEDIO — God Mode comparison no es constant-time

```python
# common/middleware.py:123
request.headers.get("X-Admin-Master-Key") == _settings.int_admin_master_key
```

**Riesgo:** Timing oracle — un atacante puede medir el tiempo de respuesta para adivinar caracteres de la master key.

**Fix requerido:**
```python
import hmac
hmac.compare_digest(
    request.headers.get("X-Admin-Master-Key", ""),
    _settings.int_admin_master_key
)
```

---

## 3. Archivos Modificados

| Archivo | Cambio |
|---|---|
| `backend/common/middleware.py` | Eliminado `traceback.print_exc()` + `str(e)` en respuesta; añadido `logger.error(exc_info=True)` + `AuditService.track()` fire-and-forget |
| `backend/common/services/audit_service.py` | `track()` implementado con `asyncio.create_task` + `AsyncSessionLocal`; añadido `_logger` a nivel de módulo |

---

## 4. Phase 134 — mes_service: Análisis Legacy + Plan de Refactorización

### Contexto

Sesión de análisis profundo cruzando el estado actual de `mes_service` con 4 proyectos legacy .NET para confirmar qué está implementado, qué hace falta y qué debe descartarse. Sin cambios de código — solo planificación.

### Proyectos legacy analizados

| Proyecto | Stack | Dominio | Relevancia |
|---|---|---|---|
| `Interno.Production` | .NET 7 | MES core | Alta — equivalente directo de mes_service |
| `Interno.HumanResource` | .NET 7 | RRHH / colaboradores | Alta — equivalente directo de hcm_service |
| `Interno.DJO` | .NET Core 3.1 | Supply chain Enovis | Baja — cliente-específico, descartado |
| `Interno.Outset` | .NET 7 | Adaptador Tulip MES | Baja — hardware-específico, descartado |

### Hallazgos del análisis cruzado

#### `Interno.Production` → `mes_service`

| Concepto legacy | Estado en mes_service |
|---|---|
| `Result` (clase base) | ✅ Renombrado a `ProductionRun` en Phase 17.5 |
| `ResultWorkOrder` (N:M) | ✅ Patrón Ledger en `ManufacturingLedger` |
| `OperationTime.RunTime` (ciclo/pieza) | ❌ Falta `cycle_time_seconds` en `StandardTime` → Phase 135 |
| `OperationTime.SetTime` (arranque) | ✅ `set_time_hours` existe |
| `Planning` module (82 cols Excel) | ❌ No hay `POST /planning/bulk-load` → Phase 136 |
| `WOType` enum (Production/Repair/Rework) | ⚠️ Enum existe pero sin validación frontend |
| `FirstPassYield` | ❌ Calculable con ScrapEntry existente, no expuesto aún |
| `quality = 1.0` bug | ✅ Corregido Phase 16 — ScrapEntry + ManufacturingMath |

#### `Interno.HumanResource` → `hcm_service`

| Concepto legacy | Estado en hcm_service |
|---|---|
| `Person.RFC` + `Person.CURP` | ❌ Campos no existen en `Collaborator` → Phase 138 |
| `Employee.LastNameP + LastNameM` | ❌ Solo `last_name` único → Phase 138 |
| `JobPosition` (6 dimensiones) | ⚠️ `Department` existe, profundidad de posición no |
| `Shift.TotalTimeBreaks = 1h` | ⚠️ Bug heredado — hardcoded; revisar en mes_service ShiftService |
| Windows AD auth | ✅ Descartado correctamente — JWT |

#### `Interno.Outset` → mes_service (StdTime)

Confirmación clave: `StdTime = (RunTime + SetTime).TotalHours` — RunTime y SetTime son conceptos **separados** en el legacy. Valida decisión de añadir `cycle_time_seconds` como campo separado de `set_time_hours`.

#### `Interno.DJO` — Funcionalidad descartada

Todo el dominio es cliente-específico (Enovis/DJO):
- STBL (Shortage to Build List) → `purchasing_service` futuro
- Kanban / Bin picking → `wms_service` futuro
- Supplier Scorecards (OTD/Inflation/Quality) → `purchasing_service` futuro
- Windows AD authentication → reemplazado por JWT
- Integración Tulip MES → específico a instalaciones con Tulip

### Auditoría de seguridad mes_service — resumen de los 10 hallazgos

| ID | Tipo | Hallazgo | Phase |
|---|---|---|---|
| BUG-01 | Runtime | `ScannerService(db)` — constructor espera 4 repos, recibe 1 | — (sin docs aún) |
| BUG-02 | Runtime | `db.get(WorkOrder, order_number)` — usa PK UUID, order_number es string | — |
| BUG-03 | Runtime | `Downtime(resource_result_id=...)` — field renombrado a `production_run_id` en 17.5 | — |
| BUG-04 | Runtime | `event_publisher.py` — método entero es `print()` stub, `settings.is_monolith` no existe | — |
| ARCH-01 | Code Quality | `float(ledger_entry.qty)` en scan.py — PRIMITIVE_FLOAT_VIOLATION | Phase 137 |
| SEC-01 | IDOR | `respond_downtime(tech_user_id: uuid.UUID)` como query param libre | Phase 137 |
| SEC-02 | IDOR | `close_downtime` UPDATE sin filtro `company_id` | Phase 137 |
| SEC-03 | IDOR | `admin_close_downtime` toma `admin_user_id` del body | Phase 137 |
| SEC-04 | Auth | `scan.py`, `dashboard.py`, `labor.py` sin `require_scope` | Phase 137 |
| SEC-05 | Auth | `get_work_orders` extrae `company_id` del JWT pero no lo aplica al query | Phase 137 |
| OPS-01 | Gold Standard | `alembic/env.py` sin `version_table` + debug prints líneas 20-27 | Phase 135 |

Varios issues YA resueltos en phases previas (no listados arriba):
- Phase 17.5: NameError/IndentationError, ProductionRun rename, BOM Guard, Andon escalation
- Phase 16: `quality = 1.0` bug → ScrapEntry + ManufacturingMath
- Phase 20.5: Repository pattern, zero infrastructure imports en services
- Phase 3: ScheduleProduction command, actualizaciones atómicas

### Plan de Implementación acordado

#### Phase 135 — Core matemático
1. Alembic migration: `cycle_time_seconds INTEGER NULL` en `standard_times`
2. `manufacturing_math.py`: `calculate_tak_time_seconds()` con fallback `cycle_time_seconds → set_time_hours`
3. Nueva función `calculate_theoretical_capacity(cycle_time_seconds, available_minutes)`
4. `ShiftService`: aritmética overnight `(24h - start) + end` para T2 16:30–01:45
5. `alembic/env.py`: añadir `version_table="alembic_version_mes"` + eliminar debug prints

#### Phase 136 — Planning Bulk-load
1. Nuevo router `planning.py` con `POST /api/v1/mes/planning/bulk-load`
2. `PlanningEntry` schema con validación `date >= today`
3. Invoca `ScheduleProduction` en loop atómico con respuesta `{scheduled, skipped, errors}`
4. `company_id` del JWT únicamente (Muro de Hierro)

#### Phase 137 — Seguridad y Calidad
1. Sanitizar Downtime: IDOR en `tech_user_id`/`admin_user_id` → extraer del JWT
2. Añadir `company_id` filter en `close_downtime`, `get_active_downtimes`
3. `require_scope` en scan, dashboard, labor, downtime
4. Nuevo endpoint `POST /api/v1/mes/production/scrap`
5. `kpi_service.py` `get_resource_graphic()`: incluir `scrap_qty` por hora
6. Fix `float()` → `Decimal` en scan.py

#### Phase 138 — hcm_service Mexicanización
1. Migración `hcm_db`: `last_name` → `last_name_paternal` + `last_name_maternal`
2. Validators Pydantic: RFC (`^[A-Z]{4}[0-9]{6}[A-Z0-9]{3}$`) + CURP (`^[A-Z]{4}[0-9]{6}[A-Z]{6}[0-9]{2}$`)
3. Ambos opcionales (no bloquear colaboradores extranjeros)

### Conexión mes_service ↔ hcm_service

Para que `mes_service` valide capacidades de operadores necesita consultar `hcm_service`:
- `GET /api/v1/hcm/collaborators/{id}/certifications` — antes de asignar labor en una operación
- `mes_service` llama HTTP a `hcm_service` (sin import directo — regla 4.4)
- Phase 138 debe completarse antes de que Phase 135 active la validación de capacidades

---

## 5. Phases 135–138 — Implementación

### Phase 135 — mes_service Core Matemático

| Archivo | Cambio |
|---|---|
| `mes_service/alembic/env.py` | Debug prints eliminados. `version_table="alembic_version_mes"` en ambos contextos |
| `mes_service/alembic/versions/006_mes_cycle_time_and_breaks.py` | `cycle_time_seconds INTEGER NULL` en `mes_standard_times`. `break_minutes INTEGER DEFAULT 60` en `mes_shifts` (`server_default='60'` para no romper turnos existentes) |
| `mes_service/mes_app/models/shift.py` | `break_minutes: Mapped[int] = mapped_column(Integer, default=60)` |
| `mes_service/mes_app/models/standard_time.py` | `cycle_time_seconds: Mapped[Optional[int]]` nullable |
| `mes_service/mes_app/core/services/manufacturing_math.py` | `calculate_tak_time_seconds(productive_mins, actual_qty, cycle_time_seconds=None)` — toma `cycle_time_seconds` directo si disponible. Nueva `calculate_theoretical_capacity(cycle_time_seconds, available_minutes) → int` |
| `mes_service/mes_app/services/shift_service.py` | `calculate_available_minutes(shift)` con overnight `(24h − start) + end`; `getattr(shift, 'break_minutes', 60)` seguro contra shifts legacy |

**Decisión de diseño clave:** `break_minutes` en el modelo `Shift` en lugar de tabla separada — el legacy confirmó que breaks son a nivel de turno, no por operación individual. El `DEFAULT 60` en la migración evita `NOT NULL` constraint en rows existentes.

### Phase 136 — mes_service Planning Bulk-load

| Archivo | Cambio |
|---|---|
| `mes_service/mes_app/schemas/planning.py` | `PlanningEntry` con `@field_validator('date')` rechaza fechas pasadas. `BulkLoadResponse {scheduled, skipped, errors}` |
| `mes_service/mes_app/api/v1/endpoints/planning.py` | `POST /api/v1/mes/planning/bulk-load` — `begin_nested()` por entrada, commit global al final. `company_id` del JWT únicamente |
| `mes_service/mes_app/main.py` | Routers `planning` y `production` registrados |

**Decisión de diseño clave:** `begin_nested()` por entrada (savepoint) en lugar de un solo bloque — permite continuar el lote cuando una entrada falla (ej. conflicto de fecha/turno). El caller recibe `{scheduled: N, skipped: M, errors: [...]}` para saber exactamente qué pasó con cada entrada.

### Phase 137 — mes_service Seguridad y Calidad

| Archivo | Issues resueltos |
|---|---|
| `mes_service/mes_app/api/v1/endpoints/downtime.py` | SEC-01/02/03: IDOR eliminado. SEC-04: require_scope en 5 endpoints |
| `mes_service/mes_app/api/v1/endpoints/scan.py` | ARCH-01: `float → Decimal`. SEC-04: require_scope |
| `mes_service/mes_app/api/v1/endpoints/dashboard.py` | SEC-04: require_scope en /oee, /graphic, /pareto. Router duplicado eliminado |
| `mes_service/mes_app/api/v1/endpoints/labor.py` | SEC-04: require_scope en 4 endpoints. company_id en clock_out |
| `mes_service/mes_app/api/v1/endpoints/work_order.py` | SEC-05: WHERE company_id. BUG-02: db.get → select().where(order_number) |
| `mes_service/mes_app/api/v1/endpoints/production.py` | Nuevo: POST /mes/production/scrap con ownership check |

**Code Graph post-implementación: 100% Compliance, 0 CRITICALs, 0 WARNINGs.**

**Nota sobre BUG-03 y BUG-04:** No resueltos en esta fase. `BUG-03` (`resource_result_id` renombrado) y `BUG-04` (`event_publisher.py` stub) quedan pendientes como deuda técnica para cuando se active `mes_service` en Nginx.

### Phase 138 — hcm_service Mexicanización

| Archivo | Cambio |
|---|---|
| `hcm_service/alembic/versions/002_split_last_name.py` | Migration con data copy: `SET last_name_paternal = last_name` → `ALTER NOT NULL` → `DROP last_name` |
| `hcm_service/hcm_app/models/collaborator.py` | `last_name` → `last_name_paternal + last_name_maternal`. `full_name` property actualizada |
| `hcm_service/hcm_app/schemas/collaborator.py` | `CollaboratorRead/Create/Update` actualizados. RFC/CURP sin cambios (ya existían) |

---

## 6. Estado de Seguridad Post-Fase

| Check | Estado |
|---|---|
| Exception raw expuesta en HTTP 500 | ✅ CORREGIDO — `"An unexpected error occurred."` |
| Stack traces en logs del servidor | ✅ `exc_info=True` — solo en logs internos |
| Audit trail de errores críticos | ✅ `CRITICAL_MIDDLEWARE_ERROR` en `audit_logs` |
| `AuditService.track()` persistencia | ✅ Real DB write (antes era `print()`) |
| kiosk_service CORS wildcard | ❌ Pendiente |
| asset_manager CORS fallback | ❌ Pendiente |
| *.vercel.app wildcard | ❌ Pendiente |
| God Mode constant-time | ❌ Pendiente |
| HMAC tickets (constant-time) | ✅ `hmac.compare_digest()` ya correcto |
| JTI gate Redis | ✅ Correcto |
| Scope matching namespace | ✅ Correcto |
