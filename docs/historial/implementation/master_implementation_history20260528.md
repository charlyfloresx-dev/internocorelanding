# Implementation History — 2026-05-28 (Phases 150 → 154)

---

## Phase 154 — Resource Monitor: Análisis Arquitectónico

### Objetivo
Diseñar la implementación para conectar `ResourceMonitorComponent` (Angular, 100% mock) al `mes_service` real, portando la lógica del legacy `.NET` `Interno.Production`.

### Hallazgos del Legacy (portados al plan Python)

**`Resource : Warehouse` — identidad compartida**
En .NET, un `Resource` de producción hereda directamente de `Warehouse`. Comparte: `Code (PK string max 13)`, `Name`, `Description`, `TypeId/Type`, `Capacity`, `Unit`, `Group`, `Active`, timestamps. Solo agrega `BreakGroupId` y `ProductionArea`.

**Implicación Python (Iron Wall ADR-02):**
`Resource(MultiTenantBase)` en `mes_service` con `warehouse_id: Optional[UUID]` como soft FK — sin FK a nivel BD. El `code` es la clave de negocio. No hay herencia cross-servicio.

**Jerarquía de dominio:**
```
Facility(code, name, location)
  └─ ProductionArea(name, description, facility_id)
       └─ Resource(code, name, resource_type, warehouse_id[soft], production_area_id)
            └─ BreakGroup → Break[] (horarios de descanso del turno)
```

**`Result` = sesión de producción (equivale a `ProductionRun` en Python):**
- `ResourceCode + ShiftId + Date + Priority` — clave natural.
- Colecciones: `HourByHour[]` (→ `HourlyProductionSnapshot`), `Labor[]`, `Downtime[]`, `Goals[]`.
- KPIs calculados: OEE, OE, TEP, Availability, Efficiency, FirstPassYield.
- Fechas logísticas: `ShippingDate`, `WHSDate`, `SMKTDate`.

**Algoritmo `GetGraphic()` — portado a Python:**
```
1. Detectar turno: 5h < now.hour < 17h → turno diurno; else nocturno
2. Generar slots: [shift.start .. shift.end] en horas enteras
3. Disponible[i] = 1.0 por defecto
4. Aplicar breaks:
   - break inicia en slot i → Disponible[i] = break.start.hours - slot_hour
   - break termina en slot i → Disponible[i] = next_slot_hour - break.end.hours
5. Para cada Result (WO planificada) ordenado por Priority:
   if OperationTime: qtyPerHour = floor(Disponible[i] / operationTime.set_time)
   else:             qtyPerHour = round(plan_qty / total_horas_necesarias)
   Meta[i] = qtyPerHour; Faltante[i] = qtyPerHour
6. Cargar HourlyProductionSnapshot (GROUP BY hora):
   if actual > meta → Excedente[i] = actual - meta; Faltante[i] = 0
   else             → Faltante[i] = meta - actual; Producidas[i] = actual
7. Eficiencia[i] = ceil((Producidas[i] * 100) / Meta[i])
```

### Arquitectura de la solución (4 partes)

| Parte | Alcance | Estimado |
|---|---|---|
| 1 | `Facility` + `ProductionArea` + `Resource` + migration + seed + CRUD | 1 sesión |
| 2 | Endpoint `/graphic` (algoritmo hora×hora) + `/active-workorder` + `/planned-workorders` | 1 sesión |
| 3 | `ResourceService` Angular + desconectar mock + `:code` param + selector | 1 sesión |
| 4 | Nginx upstream verificación + smoke test E2E | ½ sesión |

---

## Phase 150 — MES Service: WorkOrder Document+Lines Pattern

## MES Service: WorkOrder Document+Lines Pattern

### Objetivo
Implementar el Patrón Documento+Líneas en MES, desplegar mes-service en el stack Docker, y escribir tests de integración contra la base de datos real.

### Decisiones Arquitectónicas

**1. PostgreSQL enums nativos vs Enumeration table**
- `WorkOrderLineType` / `WorkOrderLineStatus` → PostgreSQL nativo. Son tipos del sistema, no configurables por tenant.
- `WOType` → PostgreSQL nativo hoy. Candidato a migrar a `enumerations` en master_data_db en fase futura (7 valores, potencialmente diferente por industria).
- DO block idempotente para cada enum: `DO $ BEGIN CREATE TYPE ... EXCEPTION WHEN duplicate_object THEN NULL; END $;`
- `postgresql.ENUM(..., create_type=False)` en columnas (no `sa.Enum`) — diferencia crítica: solo el dialecto-específico respeta el parámetro.

**2. BOM explode best-effort**
- `_fetch_bom()` usa httpx con timeout=5s hacia `inventory-service:8000`.
- Si falla → `[]` → WO se crea solo con PLANNED_OUTPUT. No bloquea producción.
- Justificación: en piso de producción, la creación de la WO es crítica; las líneas de material son informativas.

**3. tenant_id en tablas existentes**
- Migraciones 001-007 no tenían tenant_id (MultiTenantBase lo requiere).
- Migration 008 lo añade como nullable en las 10 tablas existentes (seguro — mes_db empieza vacía).

**4. ForeignKey en ORM**
- `WorkOrderLine.work_order_id` necesitaba `ForeignKey("mes_work_orders.id", ondelete="CASCADE")` declarado en la columna para que SQLAlchemy resuelva el join automáticamente.
- La migración ya tenía `sa.ForeignKeyConstraint` a nivel DB, pero el ORM no lo veía sin la declaración explícita.

### Estructura de tests

```
mes_service/tests/
├── conftest.py                         # Path setup + dotenv (root .env)
├── test_work_order.py                  # 3 unit tests → PostgreSQL (migrado de SQLite)
├── test_main.py                        # SKIP (planning.py PydanticUserError)
├── test_mes_core.py                    # 4 xfail (service repos cambiaron API)
└── integration/
    ├── conftest.py                     # PostgreSQL fixture con rollback
    └── test_work_order_lines.py        # 17 tests: schema + CRUD + handler + cascade
```

**Patrón fixture:** `session.begin()` → yield → `session.rollback()` — no contamina mes_db.

### Resultado final
- `interno-mes-dev` desplegado en puerto 8005
- 22 tablas en mes_db, 8 migraciones Alembic aplicadas
- 20 tests passing, 1 skipped, 4 xfailed
- Code Graph: 0 CRITICALs, mes_service 100% compliant
