"""
UC-MES-WOL: WorkOrder Document+Lines pattern — Phase 150 integration tests.

Validates against the real mes_db (PostgreSQL):
  - Migration 008 applied correctly (table + enums + tenant_id columns)
  - WorkOrderLine model CRUD
  - WorkOrderHandler BOM explode logic (mocked BOM fetch)
  - Cascade delete: WorkOrder → lines
  - Unique constraint: (work_order_id, line_number)
"""
import uuid
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from mes_app.models.work_order import WorkOrder
from mes_app.models.work_order_line import WorkOrderLine
from mes_app.core.enums import WOType, WorkOrderLineType, WorkOrderLineStatus
from mes_app.core.handlers.work_order_handler import WorkOrderHandler, CreateWorkOrderCommand


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_work_order(company_id: uuid.UUID, order_number: str = "WO-INT-001") -> WorkOrder:
    return WorkOrder(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        order_number=order_number,
        item_code="MOTOR-SKU-X",
        order_quantity=100,
        manufactured_quantity=0,
        status="DRAFT",
    )


def _make_command(company_id: uuid.UUID, **overrides) -> CreateWorkOrderCommand:
    defaults = dict(
        order_number="WO-INT-CMD-001",
        item_code="TURBO-SKU-01",
        order_qty=50,
        due_date=datetime(2026, 7, 31, tzinfo=timezone.utc),
        company_id=company_id,
        alias="Lote Julio",
    )
    defaults.update(overrides)
    return CreateWorkOrderCommand(**defaults)


# ── Schema verification (migration 008) ──────────────────────────────────────

async def test_work_order_lines_table_exists(db_session):
    """Migration 008 aplicó CREATE TABLE mes_work_order_lines."""
    result = await db_session.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='mes_work_order_lines'"
        )
    )
    assert result.fetchone() is not None, "Tabla mes_work_order_lines no existe — migration 008 no aplicada"


async def test_workorderlinetype_enum_exists_in_pg(db_session):
    """PostgreSQL enum 'workorderlinetype' existe (DO block idempotente de 008 funcionó)."""
    result = await db_session.execute(
        text("SELECT typname FROM pg_type WHERE typname = 'workorderlinetype'")
    )
    assert result.fetchone() is not None, "Enum workorderlinetype faltante en pg_type"


async def test_workorderlinestatus_enum_exists_in_pg(db_session):
    """PostgreSQL enum 'workorderlinestatus' existe."""
    result = await db_session.execute(
        text("SELECT typname FROM pg_type WHERE typname = 'workorderlinestatus'")
    )
    assert result.fetchone() is not None, "Enum workorderlinestatus faltante en pg_type"


async def test_wotype_enum_exists_in_pg(db_session):
    """PostgreSQL enum 'wotype' existe."""
    result = await db_session.execute(
        text("SELECT typname FROM pg_type WHERE typname = 'wotype'")
    )
    assert result.fetchone() is not None, "Enum wotype faltante en pg_type"


async def test_tenant_id_added_to_work_orders(db_session):
    """Migration 008 añadió tenant_id a mes_work_orders."""
    result = await db_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='mes_work_orders' AND column_name='tenant_id'"
        )
    )
    assert result.fetchone() is not None, "Columna tenant_id faltante en mes_work_orders"


async def test_bom_id_column_exists_in_work_order_lines(db_session):
    """bom_id existe en mes_work_order_lines (weak-ref al BOM de inventory_service)."""
    result = await db_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='mes_work_order_lines' AND column_name='bom_id'"
        )
    )
    assert result.fetchone() is not None, "Columna bom_id faltante en mes_work_order_lines"


# ── WorkOrderLine model CRUD ──────────────────────────────────────────────────

async def test_insert_planned_output_line(db_session):
    """INSERT + SELECT de WorkOrderLine PLANNED_OUTPUT — todos los campos persisten."""
    company_id = uuid.uuid4()
    wo = _make_work_order(company_id)
    db_session.add(wo)
    await db_session.flush()

    line = WorkOrderLine(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        work_order_id=wo.id,
        line_number=1,
        line_type=WorkOrderLineType.PLANNED_OUTPUT,
        item_code="MOTOR-SKU-X",
        planned_quantity=Decimal("100"),
        actual_quantity=Decimal("0"),
        status=WorkOrderLineStatus.PENDING,
    )
    db_session.add(line)
    await db_session.flush()

    fetched = await db_session.get(WorkOrderLine, line.id)
    assert fetched is not None
    assert fetched.line_type == WorkOrderLineType.PLANNED_OUTPUT
    assert fetched.item_code == "MOTOR-SKU-X"
    assert fetched.planned_quantity == Decimal("100")
    assert fetched.actual_quantity == Decimal("0")
    assert fetched.status == WorkOrderLineStatus.PENDING
    assert fetched.work_order_id == wo.id


async def test_insert_material_input_line_with_bom_ref(db_session):
    """WorkOrderLine MATERIAL_INPUT guarda bom_id (referencia débil al BOM de inventory)."""
    company_id = uuid.uuid4()
    bom_uuid = uuid.uuid4()
    wo = _make_work_order(company_id, order_number="WO-INT-BOM-001")
    db_session.add(wo)
    await db_session.flush()

    line = WorkOrderLine(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        work_order_id=wo.id,
        line_number=1,
        line_type=WorkOrderLineType.MATERIAL_INPUT,
        item_code="COMP-SKU-ABC",
        planned_quantity=Decimal("200"),
        actual_quantity=Decimal("0"),
        uom="PCS",
        bom_id=bom_uuid,
        status=WorkOrderLineStatus.PENDING,
    )
    db_session.add(line)
    await db_session.flush()

    result = await db_session.execute(
        select(WorkOrderLine).where(WorkOrderLine.id == line.id)
    )
    fetched = result.scalar_one()
    assert fetched.line_type == WorkOrderLineType.MATERIAL_INPUT
    assert fetched.bom_id == bom_uuid
    assert fetched.uom == "PCS"


async def test_unique_constraint_line_number_per_work_order(db_session):
    """(work_order_id, line_number) es único — insertar duplicado lanza IntegrityError."""
    company_id = uuid.uuid4()
    wo = _make_work_order(company_id, order_number="WO-INT-UQ-001")
    db_session.add(wo)
    await db_session.flush()

    def _line(number: int) -> WorkOrderLine:
        return WorkOrderLine(
            id=uuid.uuid4(),
            company_id=company_id,
            tenant_id=company_id,
            work_order_id=wo.id,
            line_number=number,
            line_type=WorkOrderLineType.PLANNED_OUTPUT,
            item_code="ITEM-001",
            planned_quantity=Decimal("1"),
            actual_quantity=Decimal("0"),
        )

    db_session.add(_line(1))
    await db_session.flush()

    db_session.add(_line(1))  # same line_number → constraint violation
    with pytest.raises(IntegrityError, match="uq_wo_line_number"):
        await db_session.flush()


async def test_status_defaults_to_pending(db_session):
    """status omitido → PENDING por server_default de la columna."""
    company_id = uuid.uuid4()
    wo = _make_work_order(company_id, order_number="WO-INT-DEF-001")
    db_session.add(wo)
    await db_session.flush()

    line = WorkOrderLine(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        work_order_id=wo.id,
        line_number=1,
        line_type=WorkOrderLineType.PLANNED_OUTPUT,
        item_code="SKU-DEF",
        planned_quantity=Decimal("10"),
        actual_quantity=Decimal("0"),
    )
    db_session.add(line)
    await db_session.flush()

    await db_session.refresh(line)
    assert line.status == WorkOrderLineStatus.PENDING


# ── WorkOrderHandler integration (BOM mocked) ─────────────────────────────────

async def test_handler_creates_planned_output_when_bom_empty(db_session):
    """
    Sin BOM disponible → handler crea WO + exactamente 1 línea PLANNED_OUTPUT.
    La graceful degradation del _fetch_bom no bloquea la creación de la orden.
    """
    company_id = uuid.uuid4()
    handler = WorkOrderHandler(db_session)
    cmd = _make_command(company_id, order_number="WO-INT-NOBOM-001")

    with patch.object(handler, "_fetch_bom", new=AsyncMock(return_value=[])):
        result = await handler.handle_create(cmd)

    assert result["status"] == "DRAFT"
    wo_id = uuid.UUID(result["id"])

    lines = (await db_session.execute(
        select(WorkOrderLine).where(WorkOrderLine.work_order_id == wo_id)
    )).scalars().all()

    assert len(lines) == 1
    assert lines[0].line_type == WorkOrderLineType.PLANNED_OUTPUT
    assert lines[0].item_code == "TURBO-SKU-01"
    assert lines[0].planned_quantity == Decimal("50")
    assert lines[0].line_number == 1


async def test_handler_explodes_bom_into_material_input_lines(db_session):
    """
    BOM con 2 componentes → handler crea WO + 2 MATERIAL_INPUT lines + 1 PLANNED_OUTPUT.
    Lines numeradas: 1 (comp-A), 2 (comp-B), 3 (output).
    """
    company_id = uuid.uuid4()
    bom_data = [
        {"id": str(uuid.uuid4()), "component_item_code": "COMP-A", "quantity": 2.0, "uom": "PCS"},
        {"id": str(uuid.uuid4()), "component_item_code": "COMP-B", "quantity": 1.5, "uom": "KG"},
    ]

    handler = WorkOrderHandler(db_session)
    cmd = _make_command(company_id, order_number="WO-INT-BOM2-001", order_qty=10)

    with patch.object(handler, "_fetch_bom", new=AsyncMock(return_value=bom_data)):
        result = await handler.handle_create(cmd)

    wo_id = uuid.UUID(result["id"])
    lines = (await db_session.execute(
        select(WorkOrderLine)
        .where(WorkOrderLine.work_order_id == wo_id)
        .order_by(WorkOrderLine.line_number)
    )).scalars().all()

    assert len(lines) == 3

    comp_a = lines[0]
    assert comp_a.line_type == WorkOrderLineType.MATERIAL_INPUT
    assert comp_a.item_code == "COMP-A"
    assert comp_a.planned_quantity == Decimal("20")  # 2.0 × 10 qty
    assert comp_a.uom == "PCS"
    assert comp_a.line_number == 1

    comp_b = lines[1]
    assert comp_b.line_type == WorkOrderLineType.MATERIAL_INPUT
    assert comp_b.item_code == "COMP-B"
    assert comp_b.planned_quantity == Decimal("15")  # 1.5 × 10 qty
    assert comp_b.line_number == 2

    output = lines[2]
    assert output.line_type == WorkOrderLineType.PLANNED_OUTPUT
    assert output.item_code == "TURBO-SKU-01"
    assert output.planned_quantity == Decimal("10")
    assert output.line_number == 3


async def test_handler_wo_type_persists(db_session):
    """wo_type STANDARD se persiste correctamente en mes_work_orders."""
    company_id = uuid.uuid4()
    handler = WorkOrderHandler(db_session)
    cmd = _make_command(company_id, order_number="WO-INT-TYPE-001", wo_type=WOType.STANDARD)

    with patch.object(handler, "_fetch_bom", new=AsyncMock(return_value=[])):
        result = await handler.handle_create(cmd)

    wo = await db_session.get(WorkOrder, uuid.UUID(result["id"]))
    assert wo is not None
    assert wo.wo_type == WOType.STANDARD


async def test_handler_all_lines_have_pending_status(db_session):
    """Todas las líneas creadas por el handler empiezan con status PENDING."""
    company_id = uuid.uuid4()
    bom_data = [
        {"id": str(uuid.uuid4()), "component_item_code": "COMP-X", "quantity": 3.0, "uom": "EA"},
    ]
    handler = WorkOrderHandler(db_session)
    cmd = _make_command(company_id, order_number="WO-INT-PEND-001")

    with patch.object(handler, "_fetch_bom", new=AsyncMock(return_value=bom_data)):
        result = await handler.handle_create(cmd)

    wo_id = uuid.UUID(result["id"])
    lines = (await db_session.execute(
        select(WorkOrderLine).where(WorkOrderLine.work_order_id == wo_id)
    )).scalars().all()

    assert all(line.status == WorkOrderLineStatus.PENDING for line in lines)


async def test_handler_material_input_bom_id_stored(db_session):
    """MATERIAL_INPUT lines almacenan el bom_id del componente BOM (weak-ref a inventory)."""
    company_id = uuid.uuid4()
    bom_uuid = uuid.uuid4()
    bom_data = [
        {"id": str(bom_uuid), "component_item_code": "FILTER-001", "quantity": 1.0, "uom": "PCS"},
    ]
    handler = WorkOrderHandler(db_session)
    cmd = _make_command(company_id, order_number="WO-INT-BOMID-001")

    with patch.object(handler, "_fetch_bom", new=AsyncMock(return_value=bom_data)):
        result = await handler.handle_create(cmd)

    wo_id = uuid.UUID(result["id"])
    lines = (await db_session.execute(
        select(WorkOrderLine).where(
            WorkOrderLine.work_order_id == wo_id,
            WorkOrderLine.line_type == WorkOrderLineType.MATERIAL_INPUT,
        )
    )).scalars().all()

    assert len(lines) == 1
    assert lines[0].bom_id == bom_uuid


# ── Cascade delete ─────────────────────────────────────────────────────────────

async def test_cascade_delete_removes_lines(db_session):
    """Eliminar WorkOrder elimina en cascada sus WorkOrderLines (ondelete CASCADE)."""
    company_id = uuid.uuid4()
    wo = _make_work_order(company_id, order_number="WO-INT-DEL-001")
    db_session.add(wo)
    await db_session.flush()

    for i in range(1, 4):
        db_session.add(WorkOrderLine(
            id=uuid.uuid4(),
            company_id=company_id,
            tenant_id=company_id,
            work_order_id=wo.id,
            line_number=i,
            line_type=WorkOrderLineType.PLANNED_OUTPUT,
            item_code="SKU-DEL",
            planned_quantity=Decimal("10"),
            actual_quantity=Decimal("0"),
        ))
    await db_session.flush()

    wo_id = wo.id
    await db_session.delete(wo)
    await db_session.flush()

    orphans = (await db_session.execute(
        select(WorkOrderLine).where(WorkOrderLine.work_order_id == wo_id)
    )).scalars().all()
    assert orphans == [], f"Se esperaban 0 líneas huérfanas, se encontraron {len(orphans)}"


# ── Query by work_order lines ─────────────────────────────────────────────────

async def test_query_lines_by_work_order_id_ordered(db_session):
    """SELECT lines WHERE work_order_id devuelve líneas ordenadas por line_number."""
    company_id = uuid.uuid4()
    wo = _make_work_order(company_id, order_number="WO-INT-ORD-001")
    db_session.add(wo)
    await db_session.flush()

    for i in [3, 1, 2]:  # insertar en orden arbitrario
        db_session.add(WorkOrderLine(
            id=uuid.uuid4(),
            company_id=company_id,
            tenant_id=company_id,
            work_order_id=wo.id,
            line_number=i,
            line_type=WorkOrderLineType.PLANNED_OUTPUT,
            item_code=f"SKU-{i:03d}",
            planned_quantity=Decimal(str(i * 10)),
            actual_quantity=Decimal("0"),
        ))
    await db_session.flush()

    result = await db_session.execute(
        select(WorkOrderLine)
        .where(WorkOrderLine.work_order_id == wo.id)
        .order_by(WorkOrderLine.line_number)
    )
    lines = result.scalars().all()

    assert [l.line_number for l in lines] == [1, 2, 3]
    assert lines[0].item_code == "SKU-001"
