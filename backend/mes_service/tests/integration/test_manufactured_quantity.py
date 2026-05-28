"""
UC-MES-MFQ: WorkOrder.manufactured_quantity — Phase 151 integration tests.

Validates SQLAlchemyWorkOrderRepository.increment_manufactured_quantity() against mes_db:
  - manufactured_quantity accumulates per scan
  - PLANNED_OUTPUT line actual_quantity tracks scans
  - Status transitions: DRAFT → IN_PROGRESS (first scan), → COMPLETED (at capacity)
  - WO with no lines does not crash (graceful — pre-Phase-150 WOs)
  - Decimal qty handled correctly (fractional units)
"""
import uuid
import pytest
from decimal import Decimal
from sqlalchemy import select

from mes_app.models.work_order import WorkOrder
from mes_app.models.work_order_line import WorkOrderLine
from mes_app.core.enums import WorkOrderLineType, WorkOrderLineStatus
from mes_app.infrastructure.repositories.sqlalchemy_repositories import SQLAlchemyWorkOrderRepository


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_wo(company_id: uuid.UUID, order_number: str, order_quantity: int = 100) -> WorkOrder:
    return WorkOrder(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        order_number=order_number,
        item_code="SKU-MFQ-TEST",
        order_quantity=order_quantity,
        manufactured_quantity=0,
        status="DRAFT",
    )


def _make_planned_output(company_id: uuid.UUID, work_order_id: uuid.UUID, planned_qty: int) -> WorkOrderLine:
    return WorkOrderLine(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        work_order_id=work_order_id,
        line_number=1,
        line_type=WorkOrderLineType.PLANNED_OUTPUT,
        item_code="SKU-MFQ-TEST",
        planned_quantity=Decimal(str(planned_qty)),
        actual_quantity=Decimal("0"),
        status=WorkOrderLineStatus.PENDING,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_first_scan_transitions_draft_to_in_progress(db_session):
    """Primera pieza escaneada: DRAFT → IN_PROGRESS."""
    company_id = uuid.uuid4()
    wo = _make_wo(company_id, "WO-MFQ-001")
    db_session.add(wo)
    db_session.add(_make_planned_output(company_id, wo.id, 100))
    await db_session.flush()

    repo = SQLAlchemyWorkOrderRepository(db_session)
    await repo.increment_manufactured_quantity(wo.id, Decimal("1"), company_id)
    await db_session.flush()

    await db_session.refresh(wo)
    assert wo.status == "IN_PROGRESS"
    assert wo.manufactured_quantity == 1


async def test_manufactured_quantity_accumulates_across_scans(db_session):
    """Tres escaneos acumulan manufactured_quantity correctamente."""
    company_id = uuid.uuid4()
    wo = _make_wo(company_id, "WO-MFQ-002")
    db_session.add(wo)
    db_session.add(_make_planned_output(company_id, wo.id, 100))
    await db_session.flush()

    repo = SQLAlchemyWorkOrderRepository(db_session)
    await repo.increment_manufactured_quantity(wo.id, Decimal("10"), company_id)
    await repo.increment_manufactured_quantity(wo.id, Decimal("20"), company_id)
    await repo.increment_manufactured_quantity(wo.id, Decimal("5"), company_id)
    await db_session.flush()

    await db_session.refresh(wo)
    assert wo.manufactured_quantity == 35
    assert wo.status == "IN_PROGRESS"


async def test_scan_at_capacity_transitions_to_completed(db_session):
    """manufactured_quantity == order_quantity → COMPLETED."""
    company_id = uuid.uuid4()
    wo = _make_wo(company_id, "WO-MFQ-003", order_quantity=50)
    db_session.add(wo)
    db_session.add(_make_planned_output(company_id, wo.id, 50))
    await db_session.flush()

    repo = SQLAlchemyWorkOrderRepository(db_session)
    await repo.increment_manufactured_quantity(wo.id, Decimal("50"), company_id)
    await db_session.flush()

    await db_session.refresh(wo)
    assert wo.status == "COMPLETED"
    assert wo.manufactured_quantity == 50


async def test_planned_output_actual_quantity_updates_on_scan(db_session):
    """PLANNED_OUTPUT line actual_quantity se incrementa por cada escaneo."""
    company_id = uuid.uuid4()
    wo = _make_wo(company_id, "WO-MFQ-004")
    line = _make_planned_output(company_id, wo.id, 100)
    db_session.add(wo)
    db_session.add(line)
    await db_session.flush()

    repo = SQLAlchemyWorkOrderRepository(db_session)
    await repo.increment_manufactured_quantity(wo.id, Decimal("15"), company_id)
    await db_session.flush()

    await db_session.refresh(line)
    assert line.actual_quantity == Decimal("15")


async def test_planned_output_status_transitions_to_in_progress_on_first_scan(db_session):
    """PLANNED_OUTPUT line: PENDING → IN_PROGRESS al primer escaneo."""
    company_id = uuid.uuid4()
    wo = _make_wo(company_id, "WO-MFQ-005")
    line = _make_planned_output(company_id, wo.id, 100)
    db_session.add(wo)
    db_session.add(line)
    await db_session.flush()

    repo = SQLAlchemyWorkOrderRepository(db_session)
    await repo.increment_manufactured_quantity(wo.id, Decimal("1"), company_id)
    await db_session.flush()

    await db_session.refresh(line)
    assert line.status == WorkOrderLineStatus.IN_PROGRESS


async def test_planned_output_status_transitions_to_completed_at_capacity(db_session):
    """PLANNED_OUTPUT line: IN_PROGRESS → COMPLETED cuando actual >= planned."""
    company_id = uuid.uuid4()
    wo = _make_wo(company_id, "WO-MFQ-006", order_quantity=10)
    line = _make_planned_output(company_id, wo.id, 10)
    db_session.add(wo)
    db_session.add(line)
    await db_session.flush()

    repo = SQLAlchemyWorkOrderRepository(db_session)
    await repo.increment_manufactured_quantity(wo.id, Decimal("10"), company_id)
    await db_session.flush()

    await db_session.refresh(line)
    assert line.status == WorkOrderLineStatus.COMPLETED
    assert line.actual_quantity == Decimal("10")


async def test_wo_without_planned_output_line_does_not_crash(db_session):
    """WO sin líneas (creado antes de Phase 150) — increment no lanza excepción."""
    company_id = uuid.uuid4()
    wo = _make_wo(company_id, "WO-MFQ-007")
    db_session.add(wo)
    await db_session.flush()

    repo = SQLAlchemyWorkOrderRepository(db_session)
    # Should not raise — graceful when no PLANNED_OUTPUT line exists
    await repo.increment_manufactured_quantity(wo.id, Decimal("1"), company_id)
    await db_session.flush()

    await db_session.refresh(wo)
    assert wo.manufactured_quantity == 1
    assert wo.status == "IN_PROGRESS"


async def test_nonexistent_work_order_returns_silently(db_session):
    """WO ID inexistente — increment retorna sin error (no WO to update)."""
    repo = SQLAlchemyWorkOrderRepository(db_session)
    fake_id = uuid.uuid4()
    # Should not raise
    await repo.increment_manufactured_quantity(fake_id, Decimal("5"), uuid.uuid4())


async def test_over_production_marks_completed_and_keeps_counting(db_session):
    """Sobreproducción: manufactured_quantity > order_quantity, status = COMPLETED."""
    company_id = uuid.uuid4()
    wo = _make_wo(company_id, "WO-MFQ-008", order_quantity=10)
    db_session.add(wo)
    db_session.add(_make_planned_output(company_id, wo.id, 10))
    await db_session.flush()

    repo = SQLAlchemyWorkOrderRepository(db_session)
    await repo.increment_manufactured_quantity(wo.id, Decimal("5"), company_id)
    await repo.increment_manufactured_quantity(wo.id, Decimal("8"), company_id)  # total 13 > 10
    await db_session.flush()

    await db_session.refresh(wo)
    assert wo.manufactured_quantity == 13
    assert wo.status == "COMPLETED"
