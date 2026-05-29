"""
UC-MES-GRAPHIC-154: Resource graphic endpoint — Phase 154 Part 2.

Tests:
  - GET /resources/{code}/graphic → ResourceGraphicResponse with hours[], breaks[], cumulative
  - GET /resources/{code}/active-workorder → ActiveWorkOrderRead or 404
  - GET /resources/{code}/planned-workorders → list of today's WOs

All tests run against real mes_db with rollback.
"""
import uuid
import pytest
from datetime import date, time, datetime, timezone
from decimal import Decimal
from sqlalchemy import select

from mes_app.models.facility import Facility
from mes_app.models.production_area import ProductionArea
from mes_app.models.resource import Resource
from mes_app.models.shift import Shift
from mes_app.models.shift_break import ShiftBreak
from mes_app.models.work_order import WorkOrder
from mes_app.models.production_run import ProductionRun
from mes_app.models.production_snapshot import HourlyProductionSnapshot
from mes_app.models.standard_time import StandardTime
from mes_app.services.graphic_service import ResourceGraphicService


# ── Fixtures ──────────────────────────────────────────────────────────────────

COMPANY = uuid.uuid5(uuid.NAMESPACE_DNS, "test.graphic.154")
TODAY = date.today()


def _resource(code: str = "CELDA-G01") -> Resource:
    return Resource(
        id=uuid.uuid4(), company_id=COMPANY, tenant_id=COMPANY,
        code=code, name="Celda Gráfica", resource_type="CELL", active=True,
    )


_shift_counter = [0]

def _shift(resource_id: uuid.UUID, start: time = time(6, 0), end: time = time(14, 0)) -> Shift:
    _shift_counter[0] += 1
    return Shift(
        id=uuid.uuid4(), company_id=COMPANY, tenant_id=COMPANY,
        code=f"T{_shift_counter[0]:04d}",  # max 20 chars — safe
        name="Matutino",
        start_time=start, end_time=end,
        is_overnight=False, break_minutes=60, is_active=True,
        resource_id=resource_id,
    )


def _break(shift_id: uuid.UUID, code: str, label: str,
           start: time, end: time, minutes: int) -> ShiftBreak:
    return ShiftBreak(
        id=uuid.uuid4(), company_id=COMPANY, tenant_id=COMPANY,
        shift_id=shift_id, code=code, label=label,
        break_type="BREAK", start_time=start, end_time=end,
        duration_minutes=minutes,
    )


def _work_order(order_number: str, item_code: str, order_qty: int,
                status: str = "DRAFT") -> WorkOrder:
    return WorkOrder(
        id=uuid.uuid4(), company_id=COMPANY, tenant_id=COMPANY,
        order_number=order_number, item_code=item_code,
        order_quantity=order_qty, manufactured_quantity=0, status=status,
    )


def _production_run(resource_id: uuid.UUID, work_order_id: uuid.UUID,
                    shift_id: uuid.UUID, planned_qty: int = 240) -> ProductionRun:
    return ProductionRun(
        id=uuid.uuid4(), company_id=COMPANY, tenant_id=COMPANY,
        resource_id=resource_id, work_order_id=work_order_id,
        shift_id=shift_id, date=TODAY,
        planned_quantity=planned_qty, actual_quantity=0,
    )


def _snapshot(resource_id: uuid.UUID, run_id: uuid.UUID,
              hour: int, goal: int, actual: int, item_code: str) -> HourlyProductionSnapshot:
    eff = Decimal(str(round((actual / goal * 100) if goal > 0 else 0, 2)))
    return HourlyProductionSnapshot(
        id=uuid.uuid4(), company_id=COMPANY, tenant_id=COMPANY,
        resource_id=resource_id, production_run_id=run_id,
        date=TODAY, hour=hour,
        goal_quantity=goal, actual_quantity=actual,
        efficiency_percentage=eff, item_code=item_code,
    )


# ── Tests — GraphicService (unit, no HTTP) ────────────────────────────────────

async def test_graphic_returns_hourly_slots_for_8h_shift(db_session):
    """Un turno 06:00-14:00 sin descansos produce 8 slots hora×hora."""
    res = _resource("CELDA-G02")
    db_session.add(res)
    await db_session.flush()

    sh = _shift(res.id, time(6, 0), time(14, 0))
    db_session.add(sh)
    await db_session.flush()

    wo = _work_order("WO-G-001", "MOTOR-SKU", 240)
    db_session.add(wo)
    await db_session.flush()

    run = _production_run(res.id, wo.id, sh.id, planned_qty=240)
    db_session.add(run)
    await db_session.flush()

    svc = ResourceGraphicService(db_session)
    graphic = await svc.get_graphic(resource_code="CELDA-G02", company_id=COMPANY, target_date=TODAY)

    assert graphic is not None
    assert len(graphic.hours) == 8
    assert graphic.hours[0].time == "06:00"
    assert graphic.hours[-1].time == "13:00"


async def test_graphic_goal_equals_planned_qty_distributed(db_session):
    """Meta total de las horas == planned_quantity de la ProductionRun."""
    res = _resource("CELDA-G03")
    db_session.add(res)
    await db_session.flush()

    sh = _shift(res.id, time(6, 0), time(14, 0))
    db_session.add(sh)
    await db_session.flush()

    wo = _work_order("WO-G-002", "TURBO-SKU", 240)
    db_session.add(wo)
    await db_session.flush()

    run = _production_run(res.id, wo.id, sh.id, planned_qty=240)
    db_session.add(run)
    await db_session.flush()

    svc = ResourceGraphicService(db_session)
    graphic = await svc.get_graphic("CELDA-G03", COMPANY, TODAY)

    total_goal = sum(h.goal for h in graphic.hours)
    assert total_goal == 240


async def test_graphic_actual_from_snapshots(db_session):
    """actual en cada slot viene de HourlyProductionSnapshot."""
    res = _resource("CELDA-G04")
    db_session.add(res)
    await db_session.flush()

    sh = _shift(res.id, time(6, 0), time(14, 0))
    db_session.add(sh)
    await db_session.flush()

    wo = _work_order("WO-G-003", "BRAKE-SKU", 240)
    db_session.add(wo)
    await db_session.flush()

    run = _production_run(res.id, wo.id, sh.id, planned_qty=240)
    db_session.add(run)
    await db_session.flush()

    # Solo snapshot para la hora 07 con 25 piezas
    snap = _snapshot(res.id, run.id, hour=7, goal=30, actual=25, item_code="BRAKE-SKU")
    db_session.add(snap)
    await db_session.flush()

    svc = ResourceGraphicService(db_session)
    graphic = await svc.get_graphic("CELDA-G04", COMPANY, TODAY)

    slot_07 = next(h for h in graphic.hours if h.time == "07:00")
    assert slot_07.actual == 25
    assert slot_07.missing == slot_07.goal - 25


async def test_graphic_excess_when_actual_exceeds_goal(db_session):
    """Si actual > goal → excedente = actual - goal; missing = 0."""
    res = _resource("CELDA-G05")
    db_session.add(res)
    await db_session.flush()

    sh = _shift(res.id, time(6, 0), time(14, 0))
    db_session.add(sh)
    await db_session.flush()

    wo = _work_order("WO-G-004", "ECM-SKU", 200)
    db_session.add(wo)
    await db_session.flush()

    run = _production_run(res.id, wo.id, sh.id, planned_qty=200)
    db_session.add(run)
    await db_session.flush()

    # Snapshot hora 08: goal=25, actual=40 (excedente)
    snap = _snapshot(res.id, run.id, hour=8, goal=25, actual=40, item_code="ECM-SKU")
    db_session.add(snap)
    await db_session.flush()

    svc = ResourceGraphicService(db_session)
    graphic = await svc.get_graphic("CELDA-G05", COMPANY, TODAY)

    slot_08 = next(h for h in graphic.hours if h.time == "08:00")
    assert slot_08.actual == 40
    assert slot_08.excess == 15
    assert slot_08.missing == 0


async def test_graphic_breaks_included_in_response(db_session):
    """Los ShiftBreaks del turno se incluyen en graphic.breaks."""
    res = _resource("CELDA-G06")
    db_session.add(res)
    await db_session.flush()

    sh = _shift(res.id, time(6, 0), time(14, 0))
    db_session.add(sh)
    await db_session.flush()

    sb1 = _break(sh.id, "R1", "Primer descanso", time(8, 35), time(9, 5), 30)
    sb2 = _break(sh.id, "LCH", "Comida", time(12, 0), time(12, 30), 30)
    db_session.add_all([sb1, sb2])
    await db_session.flush()

    svc = ResourceGraphicService(db_session)
    graphic = await svc.get_graphic("CELDA-G06", COMPANY, TODAY)

    assert len(graphic.breaks) == 2
    codes = {b.code for b in graphic.breaks}
    assert "R1" in codes
    assert "LCH" in codes


async def test_graphic_no_runs_returns_empty_goals(db_session):
    """Sin ProductionRuns hoy → goal=0 en todos los slots (pero slots generados)."""
    res = _resource("CELDA-G07")
    db_session.add(res)
    await db_session.flush()

    sh = _shift(res.id, time(6, 0), time(14, 0))
    db_session.add(sh)
    await db_session.flush()

    svc = ResourceGraphicService(db_session)
    graphic = await svc.get_graphic("CELDA-G07", COMPANY, TODAY)

    assert len(graphic.hours) == 8
    assert all(h.goal == 0 for h in graphic.hours)


async def test_graphic_resource_not_found_returns_none(db_session):
    """Resource desconocido → None."""
    svc = ResourceGraphicService(db_session)
    result = await svc.get_graphic("NONEXISTENT", COMPANY, TODAY)
    assert result is None


# ── Tests — active-workorder ──────────────────────────────────────────────────

async def test_active_workorder_returns_in_progress_wo(db_session):
    """active-workorder retorna la WO con status IN_PROGRESS para el recurso."""
    res = _resource("CELDA-AWO")
    db_session.add(res)
    await db_session.flush()

    sh = _shift(res.id)
    db_session.add(sh)
    await db_session.flush()

    wo = _work_order("WO-AWO-001", "INJECTOR-SKU", 500, status="IN_PROGRESS")
    wo.manufactured_quantity = 120
    db_session.add(wo)
    await db_session.flush()

    run = _production_run(res.id, wo.id, sh.id, planned_qty=240)
    db_session.add(run)
    await db_session.flush()

    svc = ResourceGraphicService(db_session)
    awo = await svc.get_active_workorder("CELDA-AWO", COMPANY, TODAY)

    assert awo is not None
    assert awo.order_number == "WO-AWO-001"
    assert awo.manufactured_quantity == 120
    assert awo.progress_pct == pytest.approx(24.0)


async def test_active_workorder_returns_none_when_only_draft(db_session):
    """Sin WO IN_PROGRESS → None."""
    res = _resource("CELDA-NODRAFT")
    db_session.add(res)
    await db_session.flush()

    sh = _shift(res.id)
    db_session.add(sh)
    await db_session.flush()

    wo = _work_order("WO-DRAFT-001", "PART-X", 100, status="DRAFT")
    db_session.add(wo)
    await db_session.flush()

    run = _production_run(res.id, wo.id, sh.id)
    db_session.add(run)
    await db_session.flush()

    svc = ResourceGraphicService(db_session)
    result = await svc.get_active_workorder("CELDA-NODRAFT", COMPANY, TODAY)
    assert result is None


# ── Tests — planned-workorders ────────────────────────────────────────────────

async def test_planned_workorders_returns_todays_runs(db_session):
    """planned-workorders retorna las ProductionRuns de hoy para el recurso.

    Nota: UniqueConstraint(resource_id, date, shift_id, company_id) impide dos runs
    en el mismo turno. Usamos dos turnos distintos para simular dos órdenes del día.
    """
    res = _resource("CELDA-PLN")
    db_session.add(res)
    await db_session.flush()

    sh1 = _shift(res.id, time(6, 0), time(10, 0))    # primer bloque
    sh2 = _shift(res.id, time(10, 0), time(14, 0))   # segundo bloque
    db_session.add_all([sh1, sh2])
    await db_session.flush()

    wo1 = _work_order("WO-PLN-001", "PART-A", 240, status="IN_PROGRESS")
    wo2 = _work_order("WO-PLN-002", "PART-B", 180, status="DRAFT")
    db_session.add_all([wo1, wo2])
    await db_session.flush()

    run1 = _production_run(res.id, wo1.id, sh1.id, planned_qty=240)
    run2 = _production_run(res.id, wo2.id, sh2.id, planned_qty=180)
    db_session.add_all([run1, run2])
    await db_session.flush()

    svc = ResourceGraphicService(db_session)
    runs = await svc.get_planned_workorders("CELDA-PLN", COMPANY, TODAY)

    assert len(runs) == 2
    order_numbers = {r.order_number for r in runs}
    assert "WO-PLN-001" in order_numbers
    assert "WO-PLN-002" in order_numbers


async def test_planned_workorders_excludes_completed(db_session):
    """WOs COMPLETED no aparecen en planned."""
    res = _resource("CELDA-DONE")
    db_session.add(res)
    await db_session.flush()

    sh1 = _shift(res.id, time(6, 0), time(10, 0))
    sh2 = _shift(res.id, time(10, 0), time(14, 0))
    db_session.add_all([sh1, sh2])
    await db_session.flush()

    wo_done = _work_order("WO-DONE-001", "PART-Z", 100, status="COMPLETED")
    wo_active = _work_order("WO-ACTIVE-001", "PART-Y", 100, status="IN_PROGRESS")
    db_session.add_all([wo_done, wo_active])
    await db_session.flush()

    run_done = _production_run(res.id, wo_done.id, sh1.id)
    run_active = _production_run(res.id, wo_active.id, sh2.id)
    db_session.add_all([run_done, run_active])
    await db_session.flush()

    svc = ResourceGraphicService(db_session)
    runs = await svc.get_planned_workorders("CELDA-DONE", COMPANY, TODAY)

    assert len(runs) == 1
    assert runs[0].order_number == "WO-ACTIVE-001"
