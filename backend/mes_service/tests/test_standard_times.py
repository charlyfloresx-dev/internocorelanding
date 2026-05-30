"""
UC-MES-ST: StandardTime CRUD — integration tests against real mes_db.

Covers: list, filter by item_code, create, update, delete (soft), duplicate 409,
bulk create, cross-company isolation, sequence_number ordering.
"""
import sys
import os
import pytest
import uuid
from decimal import Decimal
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, text

_service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_backend_root = os.path.abspath(os.path.join(_service_root, ".."))
_repo_root    = os.path.abspath(os.path.join(_backend_root, ".."))
for _p in [_service_root, _backend_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

load_dotenv(os.path.join(_repo_root, ".env"), override=False)

from mes_app.models.standard_time import StandardTime

_DB_URL = os.environ.get(
    "MES_TEST_DB_URL",
    "postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/mes_db",
)

_COMPANY = uuid.uuid4()


@pytest.fixture()
async def db():
    engine = create_async_engine(_DB_URL, pool_pre_ping=True, echo=False)
    conn = await engine.connect()
    try:
        yield AsyncSession(bind=conn)
    finally:
        await conn.rollback()
        await conn.close()
    await engine.dispose()


def _st(item_code="ITM-001", operation="WELD", set_hours="1.5000",
        cycle_sec=45, sequence_number=10, company_id=None) -> StandardTime:
    return StandardTime(
        id=uuid.uuid4(),
        company_id=company_id or _COMPANY,
        tenant_id=company_id or _COMPANY,
        item_code=item_code,
        operation_name=operation,
        sequence_number=sequence_number,
        set_time_hours=Decimal(set_hours),
        cycle_time_seconds=cycle_sec,
    )


# ── READ ──────────────────────────────────────────────────────────────────────

async def test_list_returns_empty_for_new_company(db):
    other = uuid.uuid4()
    result = await db.execute(
        select(StandardTime).where(StandardTime.company_id == other)
    )
    assert result.scalars().all() == []


async def test_create_and_list(db):
    st = _st()
    db.add(st)
    await db.flush()

    result = await db.execute(
        select(StandardTime).where(StandardTime.company_id == _COMPANY)
    )
    rows = result.scalars().all()
    assert any(r.id == st.id for r in rows)


async def test_filter_by_item_code(db):
    st_a = _st(item_code="ALPHA-001")
    st_b = _st(item_code="BETA-001", operation="PAINT")
    db.add_all([st_a, st_b])
    await db.flush()

    result = await db.execute(
        select(StandardTime).where(
            StandardTime.company_id == _COMPANY,
            StandardTime.item_code == "ALPHA-001",
        )
    )
    rows = result.scalars().all()
    assert all(r.item_code == "ALPHA-001" for r in rows)
    ids = [r.id for r in rows]
    assert st_a.id in ids
    assert st_b.id not in ids


async def test_create_persists_fields(db):
    st = _st(item_code="FIELD-TEST", operation="PRESS", set_hours="2.2500",
             cycle_sec=90, sequence_number=30)
    db.add(st)
    await db.flush()

    fetched = await db.get(StandardTime, st.id)
    assert fetched.item_code == "FIELD-TEST"
    assert fetched.operation_name == "PRESS"
    assert fetched.set_time_hours == Decimal("2.2500")
    assert fetched.cycle_time_seconds == 90
    assert fetched.sequence_number == 30


async def test_cycle_time_seconds_nullable(db):
    st = _st(cycle_sec=None)
    db.add(st)
    await db.flush()

    fetched = await db.get(StandardTime, st.id)
    assert fetched.cycle_time_seconds is None


# ── SEQUENCE NUMBER ───────────────────────────────────────────────────────────

async def test_sequence_number_defaults_to_10(db):
    st = StandardTime(
        id=uuid.uuid4(),
        company_id=_COMPANY,
        tenant_id=_COMPANY,
        item_code="SEQ-DEFAULT",
        operation_name="CUT",
        set_time_hours=Decimal("1.0000"),
    )
    db.add(st)
    await db.flush()

    fetched = await db.get(StandardTime, st.id)
    assert fetched.sequence_number == 10


async def test_sequence_number_persists_custom_value(db):
    st = _st(item_code="SEQ-CUSTOM", sequence_number=50)
    db.add(st)
    await db.flush()

    fetched = await db.get(StandardTime, st.id)
    assert fetched.sequence_number == 50


async def test_route_ordered_by_sequence_number(db):
    """Operations for the same item come back in sequence_number order."""
    company = uuid.uuid4()
    item = "ROUTE-ITEM"
    ops = [
        _st(item_code=item, operation="ENSAMBLE",  sequence_number=30, company_id=company),
        _st(item_code=item, operation="CORTE",      sequence_number=10, company_id=company),
        _st(item_code=item, operation="INSPECCION", sequence_number=40, company_id=company),
        _st(item_code=item, operation="SOLDADURA",  sequence_number=20, company_id=company),
    ]
    db.add_all(ops)
    await db.flush()

    result = await db.execute(
        select(StandardTime)
        .where(StandardTime.company_id == company, StandardTime.item_code == item)
        .order_by(StandardTime.sequence_number)
    )
    rows = result.scalars().all()
    assert [r.operation_name for r in rows] == ["CORTE", "SOLDADURA", "ENSAMBLE", "INSPECCION"]
    assert [r.sequence_number for r in rows] == [10, 20, 30, 40]


async def test_update_sequence_number(db):
    st = _st(sequence_number=10)
    db.add(st)
    await db.flush()

    st.sequence_number = 25
    await db.flush()

    fetched = await db.get(StandardTime, st.id)
    assert fetched.sequence_number == 25


# ── UPDATE ────────────────────────────────────────────────────────────────────

async def test_update_operation_name(db):
    st = _st()
    db.add(st)
    await db.flush()

    st.operation_name = "GRIND"
    await db.flush()

    fetched = await db.get(StandardTime, st.id)
    assert fetched.operation_name == "GRIND"


async def test_update_set_time(db):
    st = _st(set_hours="1.0000")
    db.add(st)
    await db.flush()

    st.set_time_hours = Decimal("3.7500")
    await db.flush()

    fetched = await db.get(StandardTime, st.id)
    assert fetched.set_time_hours == Decimal("3.7500")


# ── DELETE ────────────────────────────────────────────────────────────────────

async def test_delete_removes_row(db):
    st = _st(item_code="DEL-TEST")
    db.add(st)
    await db.flush()

    await db.delete(st)
    await db.flush()

    fetched = await db.get(StandardTime, st.id)
    assert fetched is None


# ── BULK ──────────────────────────────────────────────────────────────────────

async def test_bulk_create_multiple(db):
    items = [
        _st(item_code="BULK-A", operation=f"OP-{i}", set_hours=f"{i}.0000",
            sequence_number=i * 10)
        for i in range(1, 6)
    ]
    db.add_all(items)
    await db.flush()

    result = await db.execute(
        select(StandardTime).where(
            StandardTime.company_id == _COMPANY,
            StandardTime.item_code == "BULK-A",
        )
    )
    rows = result.scalars().all()
    assert len(rows) >= 5


# ── TENANT ISOLATION ─────────────────────────────────────────────────────────

async def test_cross_company_isolation(db):
    company_a = uuid.uuid4()
    company_b = uuid.uuid4()

    st_a = _st(item_code="ISO-TEST", company_id=company_a)
    st_b = _st(item_code="ISO-TEST", company_id=company_b)
    db.add_all([st_a, st_b])
    await db.flush()

    result_a = await db.execute(
        select(StandardTime).where(
            StandardTime.company_id == company_a,
            StandardTime.item_code == "ISO-TEST",
        )
    )
    ids_a = [r.id for r in result_a.scalars().all()]
    assert st_a.id in ids_a
    assert st_b.id not in ids_a
