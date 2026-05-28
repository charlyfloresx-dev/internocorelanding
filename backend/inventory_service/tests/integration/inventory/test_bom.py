"""
UC-INV-BOM: BOM creation — validates model fields fixed in Phase 149.

Bugs fixed:
  - BOM.__repr__ referenced self.parent_item_code which didn't exist → AttributeError
  - endpoint passed parent_item_code + is_active to constructor but model lacked both columns
  - consumer queried BOM.parent_item_code → AttributeError

These tests run against PostgreSQL (inventory_db) to confirm the migration 005 was applied.
"""
import pytest
import uuid
import sys, os
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, text

# ── Path resolution ───────────────────────────────────────────────────────────
_tests_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_service_root = os.path.abspath(os.path.join(_tests_root, ".."))
_backend_root = os.path.abspath(os.path.join(_service_root, ".."))
for _p in [_service_root, _backend_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from inventory_app.models.bom import BOM  # noqa: F401

# ── DB connection (real PostgreSQL) ──────────────────────────────────────────
_DB_URL = os.environ.get(
    "INVENTORY_TEST_DB_URL",
    "postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/inventory_db"
)


@pytest.fixture()
async def db_session():
    """Session contra PostgreSQL real; hace rollback al finalizar — no persiste datos."""
    engine = create_async_engine(_DB_URL, pool_pre_ping=True, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
    await engine.dispose()


def _make_bom(company_id: uuid.UUID, parent_item_code: str = "PROD-001") -> BOM:
    return BOM(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        product_id=uuid.uuid4(),
        uom_id=uuid.uuid4(),
        parent_item_code=parent_item_code,
        component_item_code="COMP-001",
        quantity=Decimal("2.0"),
        uom="PCS",
        level=1,
        is_active=True,
    )


async def test_bom_column_exists_in_db(db_session):
    """Verifica que parent_item_code exista en la tabla real (migration 005 aplicada)."""
    result = await db_session.execute(
        text("SELECT column_name FROM information_schema.columns "
             "WHERE table_name='inventory_boms' AND column_name='parent_item_code'")
    )
    row = result.fetchone()
    assert row is not None, "Migration 005 no aplicada — columna parent_item_code faltante"


async def test_bom_repr_no_attribute_error():
    """repr(bom) no lanza AttributeError — parent_item_code existe como atributo."""
    bom = _make_bom(uuid.uuid4())
    text_repr = repr(bom)
    assert "PROD-001" in text_repr
    assert "COMP-001" in text_repr


async def test_bom_insert_and_query(db_session):
    """INSERT y SELECT de un BOM con parent_item_code en PostgreSQL real."""
    company_id = uuid.uuid4()
    bom = _make_bom(company_id, parent_item_code="MOTOR-SKU")

    db_session.add(bom)
    await db_session.flush()  # hit DB without commit

    result = await db_session.execute(
        select(BOM).where(BOM.id == bom.id)
    )
    fetched = result.scalar_one_or_none()

    assert fetched is not None
    assert fetched.parent_item_code == "MOTOR-SKU"
    assert fetched.is_active is True
    assert fetched.component_item_code == "COMP-001"
    assert repr(fetched)  # no AttributeError


async def test_bom_query_by_parent_item_code(db_session):
    """BOM.parent_item_code puede usarse en WHERE — lo que el consumer hace."""
    company_id = uuid.uuid4()
    bom = _make_bom(company_id, parent_item_code="TURBO-X")
    db_session.add(bom)
    await db_session.flush()

    result = await db_session.execute(
        select(BOM).where(
            BOM.parent_item_code == "TURBO-X",
            BOM.company_id == company_id,
        )
    )
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].parent_item_code == "TURBO-X"


async def test_bom_is_active_default_true(db_session):
    """is_active default es True — nuevo BOM es activo por defecto."""
    bom = BOM(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        uom_id=uuid.uuid4(),
        component_item_code="FILTER-001",
        quantity=Decimal("1.0"),
    )
    db_session.add(bom)
    await db_session.flush()

    result = await db_session.execute(select(BOM).where(BOM.id == bom.id))
    fetched = result.scalar_one()
    assert fetched.is_active is True
