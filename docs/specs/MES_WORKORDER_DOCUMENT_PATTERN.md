# Spec: MES WorkOrder — Patrón Documento + Líneas

**Estado:** PENDIENTE DE IMPLEMENTACIÓN — Phase 150+  
**Fecha:** 2026-05-27  
**Autor:** Carlos Flores Montoya  
**Referencia:** `common/models/work_order_base.py`, `inventory_service/models/document.py`, `inventory_service/models/movement.py`

---

## 1. Problema Actual

El `WorkOrder` en `mes_service` es un modelo standalone que **no sigue el patrón Documento+Movimientos** que ya funciona en `inventory_service`:

```
inventory_service ✅                    mes_service ❌ (actual)
─────────────────────────────────       ────────────────────────────────
InventoryDocument (cabecera)            WorkOrder (standalone, sin líneas)
  ├── folio                               ├── order_number
  ├── document_type                       ├── order_quantity
  ├── status (DRAFT→PROCESSED)            ├── manufactured_quantity
  ├── external_reference                  ├── status (string libre)
  └── total_amount (Money VO)             └── request_date
         ↕ 1:N
Movement (línea inmutable)
  ├── document_id
  ├── product_id
  ├── quantity
  ├── uom_id
  └── price (Money VO)
```

Además, `WorkOrderBase` ya existe en `common/models/work_order_base.py` con campos ricos (`folio`, `priority`, `due_date`, `scheduled_start/end`, `assigned_to_id`, etc.) pero **nadie lo hereda**.

---

## 2. Arquitectura Objetivo

```
WorkOrder (hereda WorkOrderBase de common)   →  "El Documento"
  ├── folio            "WO-2026-A4K2"
  ├── order_type       PRODUCTION
  ├── status           DRAFT → OPEN → IN_PROGRESS → COMPLETED / CANCELLED
  ├── priority         LOW / MEDIUM / HIGH / CRITICAL
  ├── due_date         datetime UTC
  ├── order_quantity   Decimal (total piezas planificadas)
  ├── manufactured_qty Decimal (actualizado al reportar producción)
  ├── warehouse_id     UUID weak-ref WMS
  ├── assigned_to_id   UUID weak-ref HCM
  ├── external_ref     UUID (idempotency key — igual que InventoryDocument)
  ├── title            "Lote Verano Q2"
  └── alias            (campo libre, legacy)
         ↕ 1:N
WorkOrderLine                               →  "Los Movimientos"
  ├── work_order_id    UUID → WorkOrder.id
  ├── line_type        PLANNED_OUTPUT | MATERIAL_INPUT | ACTUAL_OUTPUT | ACTUAL_SCRAP
  ├── item_code        str (weak-ref a master_data — igual que BOM.component_item_code)
  ├── product_id       UUID weak-ref master_data (optional, para trazabilidad)
  ├── planned_qty      Decimal(18,4)
  ├── actual_qty       Decimal(18,4)  ← se actualiza al reportar producción
  ├── uom              str
  ├── unit_cost_val    Decimal(18,4)  ← solo MATERIAL_INPUT (para backflush)
  ├── unit_cost_curr   str(3)
  └── status           OPEN | ISSUED | COMPLETED | CANCELLED
```

---

## 3. Tipos de Línea (line_type)

| Tipo | Descripción | Quién lo crea | Quién lo actualiza |
|---|---|---|---|
| `PLANNED_OUTPUT` | Producto terminado a fabricar | Handler `create_work_order` (1 línea por WO) | `report_production` → actual_qty += piezas buenas |
| `MATERIAL_INPUT` | Componente del BOM a consumir | Handler `create_work_order` (explosion BOM) | `backflush_consumer` → actual_qty += consumo real |
| `ACTUAL_OUTPUT` | Piezas buenas confirmadas | `report_production` (append) | Inmutable |
| `ACTUAL_SCRAP` | Merma con código de defecto | `report_production` (append) | Inmutable |

> **Nota:** `PLANNED_OUTPUT` y `MATERIAL_INPUT` se crean al abrir el WO y se actualizan.  
> `ACTUAL_OUTPUT` y `ACTUAL_SCRAP` son inmutables (append-only, como `InventoryTransaction`).

---

## 4. Flujo Completo

### 4.1 Crear WorkOrder

```python
# POST /api/v1/mes/work-orders/
# Handler: WorkOrderHandler.handle_create()

1. Crear WorkOrder(status=DRAFT, order_quantity=100)
2. HTTP GET /api/v1/inventory/boms?parent_item_code={item_code}&company_id={cid}
   → retorna lista de componentes BOM
3. INSERT WorkOrderLine(PLANNED_OUTPUT, item_code, planned_qty=100)
4. Para cada bom_line:
   INSERT WorkOrderLine(MATERIAL_INPUT, bom_line.component_item_code,
                        planned_qty = 100 * bom_line.quantity,
                        unit_cost = bom_line.unit_price_if_available)
5. WorkOrder.status = OPEN
6. COMMIT atómico
```

### 4.2 Reportar Producción (ProductionRun)

```python
# POST /api/v1/mes/production/scan
# Service: ScannerService

1. UPDATE WorkOrderLine(PLANNED_OUTPUT, wo_id).actual_qty += good_pieces
2. INSERT WorkOrderLine(ACTUAL_OUTPUT, ...) → inmutable
3. Si scrap > 0:
   INSERT WorkOrderLine(ACTUAL_SCRAP, reason_code=..., actual_qty=scrap)
4. UPDATE WorkOrder.manufactured_quantity = SUM(actual_qty WHERE line_type=ACTUAL_OUTPUT)
5. EMIT event "PRODUCTION_REPORTED" → inventory consumer para backflush
```

### 4.3 Backflush (inventory_service consumer)

```python
# Event: PRODUCTION_REPORTED → BackflushConsumer

1. Leer WorkOrderLine(MATERIAL_INPUT, wo_id) desde MES via HTTP
   (o recibir en el evento los componentes a consumir)
2. Para cada material_line:
   - Crear InventoryDocument(type=ISSUANCE, external_ref=f"{wo_id}:{line_id}")
   - INSERT Movement(OUT, product_id, qty=actual_consumption, warehouse_id)
   - UPDATE InventoryLevel
3. Si insuficiente stock: INSERT BackflushError (comportamiento actual — ok)
```

### 4.4 Cerrar WorkOrder

```python
# PATCH /api/v1/mes/work-orders/{folio}/close

1. WorkOrder.actual_end = now()
2. WorkOrder.status = COMPLETED
3. WorkOrderLine(MATERIAL_INPUT).status = COMPLETED
4. WorkOrderLine(PLANNED_OUTPUT).status = COMPLETED
```

---

## 5. Migración de Base de Datos

### 5.1 Migración 008 — Refactor `mes_work_orders` + nueva tabla `mes_work_order_lines`

```python
# backend/mes_service/alembic/versions/008_add_workorder_document_pattern.py

def upgrade():
    # A) Nuevas columnas en mes_work_orders
    op.add_column('mes_work_orders', sa.Column('folio', sa.String(30), nullable=True, unique=True))
    op.add_column('mes_work_orders', sa.Column('order_type', sa.String(20), server_default='PRODUCTION'))
    op.add_column('mes_work_orders', sa.Column('priority', sa.String(20), server_default='MEDIUM'))
    op.add_column('mes_work_orders', sa.Column('title', sa.String(200), nullable=True))
    op.add_column('mes_work_orders', sa.Column('external_reference', sa.String(100), nullable=True, unique=True))
    op.add_column('mes_work_orders', sa.Column('warehouse_id', sa.UUID, nullable=True))
    op.add_column('mes_work_orders', sa.Column('assigned_to_id', sa.UUID, nullable=True))
    op.add_column('mes_work_orders', sa.Column('scheduled_start', sa.DateTime(tz=True), nullable=True))
    op.add_column('mes_work_orders', sa.Column('scheduled_end', sa.DateTime(tz=True), nullable=True))
    op.add_column('mes_work_orders', sa.Column('actual_start', sa.DateTime(tz=True), nullable=True))
    op.add_column('mes_work_orders', sa.Column('actual_end', sa.DateTime(tz=True), nullable=True))
    # Backfill folio desde order_number para filas existentes
    op.execute("UPDATE mes_work_orders SET folio = order_number WHERE folio IS NULL")

    # B) Nueva tabla mes_work_order_lines
    op.create_table('mes_work_order_lines',
        sa.Column('id', sa.UUID, nullable=False),
        sa.Column('work_order_id', sa.UUID, nullable=False),
        sa.Column('company_id', sa.UUID, nullable=False),
        sa.Column('tenant_id', sa.UUID, nullable=False),
        sa.Column('line_type', sa.String(20), nullable=False),   # PLANNED_OUTPUT | MATERIAL_INPUT | ACTUAL_OUTPUT | ACTUAL_SCRAP
        sa.Column('item_code', sa.String(100), nullable=True),
        sa.Column('product_id', sa.UUID, nullable=True),
        sa.Column('planned_qty', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('actual_qty', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('uom', sa.String(20), nullable=False, server_default='PCS'),
        sa.Column('unit_cost_val', sa.Numeric(18, 4), nullable=True),
        sa.Column('unit_cost_curr', sa.String(3), nullable=True, server_default='MXN'),
        sa.Column('status', sa.String(20), nullable=False, server_default='OPEN'),
        sa.Column('reason_code', sa.String(50), nullable=True),   # para ACTUAL_SCRAP
        sa.Column('version_id', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['work_order_id'], ['mes_work_orders.id'], name='fk_wol_work_order'),
    )
    op.create_index('ix_wol_work_order_id', 'mes_work_order_lines', ['work_order_id'])
    op.create_index('ix_wol_company_type', 'mes_work_order_lines', ['company_id', 'line_type'])
    op.create_index('ix_wol_item_code', 'mes_work_order_lines', ['item_code'])
```

---

## 6. Archivos a Crear / Modificar

| Acción | Archivo | Descripción |
|---|---|---|
| MODIFICAR | `mes_app/models/work_order.py` | Heredar de `WorkOrderBase`; mantener `order_number` como alias de `folio` |
| CREAR | `mes_app/models/work_order_line.py` | Nuevo modelo `WorkOrderLine` |
| MODIFICAR | `mes_app/models/__init__.py` | Exportar `WorkOrderLine` |
| CREAR | `alembic/versions/008_add_workorder_document_pattern.py` | Migración |
| MODIFICAR | `mes_app/core/handlers/work_order_handler.py` | Explotar BOM via HTTP + crear líneas |
| MODIFICAR | `mes_app/api/v1/endpoints/work_order.py` | `WorkOrderCreate` + `WorkOrderRead` con líneas |
| CREAR | `mes_app/api/v1/endpoints/work_order_lines.py` | `GET /work-orders/{folio}/lines` |
| MODIFICAR | `mes_app/core/services/scanner_service.py` | Actualizar `actual_qty` en PLANNED_OUTPUT al reportar |
| CREAR | `tests/integration/test_work_order_with_lines.py` | Test end-to-end contra mes_db real |

---

## 7. Prerequisitos Bloqueantes

### 7.1 MES no está desplegado en docker-compose

El `Dockerfile` usa paths obsoletos (`mes_service/app` en vez de `mes_service/mes_app`).  
El `CMD` usa `app.main:app` en vez de `mes_app.main:app`.

**Tarea previa obligatoria:**
- `[ ]` Corregir `backend/mes_service/Dockerfile`:
  - `COPY mes_service/app` → `COPY mes_service/mes_app`
  - `CMD uvicorn app.main:app` → `CMD uvicorn mes_app.main:app`
  - `COPY mes_service/scripts` → agregar si existe
- `[ ]` Agregar `mes-service` a `infrastructure/docker/docker-compose.dev.yml` (puerto 8005)
- `[ ]` Agregar upstream `mes-service:8005` a `infrastructure/nginx/nginx.conf`
- `[ ]` Corregir `migrate_all.ps1` para incluir mes-service
- `[ ]` Ejecutar `alembic upgrade head` en `mes_db` (actualmente vacía — 0 tablas)

### 7.2 Tests de WorkOrder (pendientes por MES sin desplegar)

El test `tests/test_work_order.py` fue escrito para SQLite in-memory.  
Una vez MES esté desplegado, crear `tests/integration/test_work_order.py` que:
- Conecte a `postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/mes_db`
- Pruebe `WorkOrderHandler.handle_create()` → INSERT en `mes_work_orders` real
- Pruebe creación de líneas → INSERT en `mes_work_order_lines`

---

## 8. Deuda Técnica que Resuelve

| Deuda (CLAUDE.md) | Cómo se resuelve |
|---|---|
| **ALTA: Backflush de materiales al cerrar corrida** | `WorkOrderLine(MATERIAL_INPUT)` alimenta el consumer de backflush con los componentes exactos |
| **ALTA: `WorkOrder.manufactured_quantity` nunca se actualiza** | Al reportar producción: `SUM(actual_qty WHERE line_type=ACTUAL_OUTPUT)` → `WorkOrder.manufactured_quantity` |
| **MEDIA: Transición automática WO status** | Con líneas se puede derivar status: si `actual_qty >= planned_qty` en PLANNED_OUTPUT → COMPLETED |

---

## 9. Referencia de Código Existente

| Archivo | Relevancia |
|---|---|
| `common/models/work_order_base.py` | `WorkOrderBase` abstracto — heredar aquí |
| `inventory_service/inventory_app/models/document.py` | Patrón de cabecera a replicar |
| `inventory_service/inventory_app/models/movement.py` | Patrón de línea a replicar |
| `inventory_service/inventory_app/models/bom.py` | Source de componentes para explosion BOM |
| `mes_service/mes_app/core/handlers/work_order_handler.py` | Handler a extender con creación de líneas |
| `inventory_service/inventory_app/events/consumers/production_consumer.py` | Backflush consumer que lee `BOM.parent_item_code` |
