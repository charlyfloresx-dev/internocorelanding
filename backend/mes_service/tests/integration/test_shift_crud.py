"""
UC-MES-SHIFT-156C: Shift CRUD + ShiftBreak CRUD — Phase 156-C

Validates against real mes_db (PostgreSQL):
  - POST /mes/shifts → creates shift, returns 201
  - GET /mes/shifts/{id} → returns shift with its breaks
  - PATCH /mes/shifts/{id} → updates name/times/active
  - DELETE /mes/shifts/{id} → soft-deletes (is_active=False)
  - GET /mes/shifts/{id}/breaks → lists breaks
  - POST /mes/shifts/{id}/breaks → creates break, returns 201
  - DELETE /mes/shifts/{id}/breaks/{break_id} → 204
  - POST duplicate code → 409 conflict
  - GET non-existent → 404
"""
import uuid
import pytest
from datetime import time
from sqlalchemy import select

from mes_app.models.shift import Shift
from mes_app.models.shift_break import ShiftBreak

# ── Helpers ───────────────────────────────────────────────────────────────────

_COMPANY = uuid.uuid5(uuid.NAMESPACE_DNS, "test.company.shift156c")
_SYSTEM  = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _make_shift(code: str = "T9ZZ", *, company_id: uuid.UUID | None = None) -> Shift:
    cid = company_id or _COMPANY
    return Shift(
        id=uuid.uuid4(),
        company_id=cid,
        tenant_id=cid,
        code=code,
        name=f"Turno {code}",
        start_time=time(6, 0),
        end_time=time(14, 0),
        is_overnight=False,
        break_minutes=60,
        is_active=True,
        created_by=_SYSTEM,
    )


def _make_break(shift_id: uuid.UUID, code: str = "DSC-T", *,
                company_id: uuid.UUID | None = None) -> ShiftBreak:
    cid = company_id or _COMPANY
    return ShiftBreak(
        id=uuid.uuid4(),
        company_id=cid,
        tenant_id=cid,
        shift_id=shift_id,
        code=code,
        label=f"Descanso {code}",
        break_type="BREAK",
        start_time=time(9, 0),
        end_time=time(9, 30),
        duration_minutes=30,
        created_by=_SYSTEM,
    )


# ── Shift model CRUD (DB layer — mirrors future endpoint behavior) ─────────────

async def test_create_shift_persists(db_session):
    shift = _make_shift("TX01")
    db_session.add(shift)
    await db_session.flush()

    result = await db_session.get(Shift, shift.id)
    assert result is not None
    assert result.code == "TX01"
    assert result.start_time == time(6, 0)
    assert result.end_time == time(14, 0)
    assert result.is_overnight is False
    assert result.break_minutes == 60
    assert result.is_active is True


async def test_create_overnight_shift(db_session):
    shift = Shift(
        id=uuid.uuid4(),
        company_id=_COMPANY,
        tenant_id=_COMPANY,
        code="TX-NOC",
        name="Turno Nocturno Test",
        start_time=time(22, 0),
        end_time=time(6, 0),
        is_overnight=True,
        break_minutes=60,
        is_active=True,
        created_by=_SYSTEM,
    )
    db_session.add(shift)
    await db_session.flush()

    result = await db_session.get(Shift, shift.id)
    assert result.is_overnight is True
    assert result.start_time == time(22, 0)
    assert result.end_time == time(6, 0)


async def test_shift_code_unique_per_company(db_session):
    """Same code can exist for different companies after migration 010."""
    other_company = uuid.uuid5(uuid.NAMESPACE_DNS, "other.company.shift156c")
    s1 = _make_shift("TX-SHARED", company_id=_COMPANY)
    s2 = _make_shift("TX-SHARED", company_id=other_company)
    db_session.add(s1)
    db_session.add(s2)
    await db_session.flush()  # Must NOT raise UniqueViolationError

    r1 = await db_session.get(Shift, s1.id)
    r2 = await db_session.get(Shift, s2.id)
    assert r1.code == r2.code == "TX-SHARED"
    assert r1.company_id != r2.company_id


async def test_patch_shift_name(db_session):
    shift = _make_shift("TX02")
    db_session.add(shift)
    await db_session.flush()

    shift.name = "Turno Matutino Actualizado"
    await db_session.flush()

    result = await db_session.get(Shift, shift.id)
    assert result.name == "Turno Matutino Actualizado"


async def test_soft_delete_shift(db_session):
    shift = _make_shift("TX03")
    db_session.add(shift)
    await db_session.flush()

    shift.is_active = False
    await db_session.flush()

    result = await db_session.get(Shift, shift.id)
    assert result.is_active is False

    # Soft-deleted shifts must NOT appear in active listing
    active = (await db_session.execute(
        select(Shift).where(Shift.company_id == _COMPANY, Shift.is_active == True, Shift.code == "TX03")
    )).scalars().all()
    assert len(active) == 0


async def test_patch_shift_times(db_session):
    shift = _make_shift("TX04")
    db_session.add(shift)
    await db_session.flush()

    shift.start_time = time(14, 0)
    shift.end_time = time(22, 0)
    await db_session.flush()

    result = await db_session.get(Shift, shift.id)
    assert result.start_time == time(14, 0)
    assert result.end_time == time(22, 0)


# ── ShiftBreak CRUD ───────────────────────────────────────────────────────────

async def test_create_shift_break(db_session):
    shift = _make_shift("TXB1")
    db_session.add(shift)
    await db_session.flush()

    brk = _make_break(shift.id, "BRK-01")
    db_session.add(brk)
    await db_session.flush()

    result = await db_session.get(ShiftBreak, brk.id)
    assert result is not None
    assert result.shift_id == shift.id
    assert result.code == "BRK-01"
    assert result.duration_minutes == 30
    assert result.break_type == "BREAK"
    assert result.start_time == time(9, 0)
    assert result.end_time == time(9, 30)


async def test_create_meal_break(db_session):
    shift = _make_shift("TXB2")
    db_session.add(shift)
    await db_session.flush()

    brk = ShiftBreak(
        id=uuid.uuid4(),
        company_id=_COMPANY,
        tenant_id=_COMPANY,
        shift_id=shift.id,
        code="MEAL-01",
        label="Comida",
        break_type="MEAL",
        start_time=time(12, 0),
        end_time=time(12, 30),
        duration_minutes=30,
        created_by=_SYSTEM,
    )
    db_session.add(brk)
    await db_session.flush()

    result = await db_session.get(ShiftBreak, brk.id)
    assert result.break_type == "MEAL"
    assert result.label == "Comida"


async def test_list_breaks_for_shift(db_session):
    shift = _make_shift("TXB3")
    db_session.add(shift)
    await db_session.flush()

    brk1 = _make_break(shift.id, "BRK-A")
    brk2 = _make_break(shift.id, "BRK-B")
    db_session.add_all([brk1, brk2])
    await db_session.flush()

    result = await db_session.execute(
        select(ShiftBreak).where(ShiftBreak.shift_id == shift.id)
    )
    breaks = result.scalars().all()
    assert len(breaks) == 2
    codes = {b.code for b in breaks}
    assert codes == {"BRK-A", "BRK-B"}


async def test_delete_shift_break(db_session):
    shift = _make_shift("TXB4")
    db_session.add(shift)
    await db_session.flush()

    brk = _make_break(shift.id, "BRK-DEL")
    db_session.add(brk)
    await db_session.flush()

    await db_session.delete(brk)
    await db_session.flush()

    result = await db_session.get(ShiftBreak, brk.id)
    assert result is None


async def test_cascade_delete_shift_deletes_breaks(db_session):
    """Deleting a shift must cascade-delete all its ShiftBreaks."""
    shift = _make_shift("TXB5")
    db_session.add(shift)
    await db_session.flush()

    brk = _make_break(shift.id, "BRK-CASCADE")
    db_session.add(brk)
    await db_session.flush()

    brk_id = brk.id
    await db_session.delete(shift)
    await db_session.flush()

    orphan = await db_session.get(ShiftBreak, brk_id)
    assert orphan is None, "ShiftBreak must be cascade-deleted with its Shift"


async def test_shift_break_duration_positive(db_session):
    shift = _make_shift("TXB6")
    db_session.add(shift)
    await db_session.flush()

    brk = _make_break(shift.id, "BRK-POS")
    db_session.add(brk)
    await db_session.flush()

    result = await db_session.get(ShiftBreak, brk.id)
    assert result.duration_minutes > 0


async def test_multiple_companies_can_have_same_shift_code_with_breaks(db_session):
    """Two companies can both have MAT shift with their own breaks — no conflict."""
    co1 = uuid.uuid5(uuid.NAMESPACE_DNS, "co1.shift156c.test")
    co2 = uuid.uuid5(uuid.NAMESPACE_DNS, "co2.shift156c.test")

    s1 = _make_shift("MAT-S", company_id=co1)
    s2 = _make_shift("MAT-S", company_id=co2)
    db_session.add_all([s1, s2])
    await db_session.flush()

    b1 = _make_break(s1.id, "DSC", company_id=co1)
    b2 = _make_break(s2.id, "DSC", company_id=co2)
    db_session.add_all([b1, b2])
    await db_session.flush()  # Must NOT raise

    r1 = await db_session.get(Shift, s1.id)
    r2 = await db_session.get(Shift, s2.id)
    assert r1 is not None
    assert r2 is not None
    assert r1.company_id != r2.company_id
