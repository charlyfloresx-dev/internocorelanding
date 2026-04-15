import sys
import os
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# ── Path Resolution ──────────────────────────────────────────────────────────
# Adds both the inventory_service root AND the backend root (where /common lives)
service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_root = os.path.abspath(os.path.join(service_root, ".."))

for path in [service_root, backend_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

# ── Import the unified SQLAlchemy Base ───────────────────────────────────────
# Base lives in common.infrastructure.models.base (exported via common.models)
from common.infrastructure.models.base import Base

# Force all models to register with Base.metadata before create_all
import app.models.inventory          # noqa: F401
import app.models.warehouse          # noqa: F401
import app.models.document           # noqa: F401
import app.models.inter_company_transfer  # noqa: F401
import app.models.movement           # noqa: F401
import app.models.stock              # noqa: F401
import common.models.audit_log       # noqa: F401

# ── SQLite In-Memory Engine ──────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    return create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="function")
async def db_session(engine):
    """
    Creates a fresh database schema for every test and drops it afterward.
    Provides a clean AsyncSession with no side effects between tests.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
