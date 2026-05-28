"""
UC-MES-WO: WorkOrder creation — validates the handler↔model mapping fixed in Phase 149.

Bugs fixed:
  - handler used order_qty/due_date/alias/release_date/status="PLANNED"
  - model has order_quantity/request_date/alias/release_date/status default "DRAFT"
"""
import sys
import os
import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# ── Path resolution ───────────────────────────────────────────────────────────
_service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_backend_root = os.path.abspath(os.path.join(_service_root, ".."))
for _p in [_service_root, _backend_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from common.infrastructure.models.base import Base
import mes_app.models.work_order  # noqa: F401 — registers table with Base.metadata

from mes_app.models.work_order import WorkOrder
from mes_app.core.handlers.work_order_handler import WorkOrderHandler, CreateWorkOrderCommand
from sqlalchemy import select

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def _make_command(**overrides) -> CreateWorkOrderCommand:
    defaults = dict(
        order_number="WO-TEST-001",
        item_code="PROD-SKU-001",
        order_qty=50,
        due_date=datetime(2026, 6, 30, tzinfo=timezone.utc),
        company_id=uuid.uuid4(),
        alias="Lote Verano",
    )
    defaults.update(overrides)
    return CreateWorkOrderCommand(**defaults)


async def test_handler_creates_work_order(db_session):
    """Handler persiste un WorkOrder con los campos correctos del modelo."""
    handler = WorkOrderHandler(db_session)
    cmd = _make_command()

    result = await handler.handle_create(cmd)
    await db_session.commit()

    assert "id" in result
    assert result["status"] == "DRAFT"

    wo = await db_session.get(WorkOrder, uuid.UUID(result["id"]))
    assert wo is not None
    assert wo.order_quantity == 50          # mapping: order_qty → order_quantity
    assert wo.request_date == cmd.due_date  # mapping: due_date → request_date
    assert wo.alias == "Lote Verano"        # new column added in migration 007
    assert wo.release_date is not None      # new column added in migration 007
    assert wo.status == "DRAFT"             # was "PLANNED" before fix
    assert wo.item_code == "PROD-SKU-001"
    assert wo.company_id == cmd.company_id


async def test_handler_rejects_qty_over_1000(db_session):
    """BusinessRuleException cuando order_qty > 1000 (mock stock check)."""
    from common.exceptions import BusinessRuleException
    handler = WorkOrderHandler(db_session)
    cmd = _make_command(order_qty=1500)

    with pytest.raises(BusinessRuleException, match="INSUFFICIENT_STOCK"):
        await handler.handle_create(cmd)


async def test_work_order_repr_does_not_raise(db_session):
    """repr() no lanza AttributeError — todos los campos del modelo existen."""
    handler = WorkOrderHandler(db_session)
    cmd = _make_command(order_qty=10)
    result = await handler.handle_create(cmd)
    await db_session.commit()

    wo = await db_session.get(WorkOrder, uuid.UUID(result["id"]))
    text = repr(wo)  # no AttributeError
    assert "mes_work_orders" not in text or wo.order_number in str(wo.__dict__)


async def test_alias_is_optional(db_session):
    """alias=None es válido — el campo es nullable."""
    handler = WorkOrderHandler(db_session)
    cmd = _make_command(alias=None)
    result = await handler.handle_create(cmd)
    await db_session.commit()

    wo = await db_session.get(WorkOrder, uuid.UUID(result["id"]))
    assert wo.alias is None
    assert wo.status == "DRAFT"
