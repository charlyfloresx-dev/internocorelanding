"""
UC-MES-WO: WorkOrder handler — core field mapping (Phase 149 regression guard).

These tests validate the handler↔model mapping that was broken before Phase 149:
  - handler used order_qty/due_date (wrong) → model uses order_quantity/request_date
  - handler used status="PLANNED" (wrong) → model defaults to "DRAFT"

Runs against real PostgreSQL (mes_db) — SQLite incompatible with PostgreSQL-specific
column types (UUID, JSONB) present in shared models.
"""
import sys
import os
import pytest
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

# ── Path resolution ────────────────────────────────────────────────────────────
_service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_backend_root = os.path.abspath(os.path.join(_service_root, ".."))
_repo_root    = os.path.abspath(os.path.join(_backend_root, ".."))
for _p in [_service_root, _backend_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

load_dotenv(os.path.join(_repo_root, ".env"), override=False)

# ── Imports (after path + env setup) ──────────────────────────────────────────
import mes_app.models.work_order       # noqa: F401
import mes_app.models.work_order_line  # noqa: F401
from mes_app.models.work_order import WorkOrder
from mes_app.core.handlers.work_order_handler import WorkOrderHandler, CreateWorkOrderCommand
from unittest.mock import AsyncMock, patch

_DB_URL = os.environ.get(
    "MES_TEST_DB_URL",
    "postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/mes_db",
)


@pytest.fixture()
async def db_session():
    engine = create_async_engine(_DB_URL, pool_pre_ping=True, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
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
    """Handler persiste WorkOrder con los campos correctos del modelo."""
    handler = WorkOrderHandler(db_session)
    cmd = _make_command()

    with patch.object(handler, "_fetch_bom", new=AsyncMock(return_value=[])):
        result = await handler.handle_create(cmd)

    assert "id" in result
    assert result["status"] == "DRAFT"

    wo = await db_session.get(WorkOrder, uuid.UUID(result["id"]))
    assert wo is not None
    assert wo.order_quantity == 50
    assert wo.request_date == cmd.due_date
    assert wo.alias == "Lote Verano"
    assert wo.release_date is not None
    assert wo.status == "DRAFT"
    assert wo.item_code == "PROD-SKU-001"
    assert wo.company_id == cmd.company_id


async def test_work_order_repr_does_not_raise(db_session):
    """repr() no lanza AttributeError — todos los atributos del modelo existen."""
    handler = WorkOrderHandler(db_session)
    cmd = _make_command(order_qty=10, order_number="WO-TEST-REPR")

    with patch.object(handler, "_fetch_bom", new=AsyncMock(return_value=[])):
        result = await handler.handle_create(cmd)

    wo = await db_session.get(WorkOrder, uuid.UUID(result["id"]))
    text = repr(wo)
    assert wo.order_number in str(wo.__dict__)


async def test_alias_is_optional(db_session):
    """alias=None es válido — el campo es nullable."""
    handler = WorkOrderHandler(db_session)
    cmd = _make_command(alias=None, order_number="WO-TEST-NOALIAS")

    with patch.object(handler, "_fetch_bom", new=AsyncMock(return_value=[])):
        result = await handler.handle_create(cmd)

    wo = await db_session.get(WorkOrder, uuid.UUID(result["id"]))
    assert wo.alias is None
    assert wo.status == "DRAFT"
