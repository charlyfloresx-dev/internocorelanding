import sys
import os
import pytest
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# ── Path resolution ────────────────────────────────────────────────────────────
_tests_root   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_service_root = os.path.abspath(os.path.join(_tests_root, ".."))
_backend_root = os.path.abspath(os.path.join(_service_root, ".."))
_repo_root    = os.path.abspath(os.path.join(_backend_root, ".."))

for _p in [_service_root, _backend_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Load root .env before importing common (which validates config at import time)
load_dotenv(os.path.join(_repo_root, ".env"), override=False)

# Force all MES models to register with Base.metadata
import mes_app.models.facility                 # noqa: F401
import mes_app.models.production_area          # noqa: F401
import mes_app.models.resource                 # noqa: F401
import mes_app.models.resource_support_member  # noqa: F401
import mes_app.models.shift                    # noqa: F401
import mes_app.models.shift_break              # noqa: F401
import mes_app.models.work_order               # noqa: F401
import mes_app.models.work_order_line          # noqa: F401
import mes_app.models.production_run           # noqa: F401
import mes_app.models.production_snapshot      # noqa: F401
import mes_app.models.standard_time            # noqa: F401

# ── Real PostgreSQL (mes_db) ───────────────────────────────────────────────────
MES_TEST_DB_URL = os.environ.get(
    "MES_TEST_DB_URL",
    "postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/mes_db",
)


@pytest.fixture()
async def db_session():
    """Session contra mes_db real; rollback al finalizar — no contamina datos."""
    engine = create_async_engine(MES_TEST_DB_URL, pool_pre_ping=True, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
    await engine.dispose()
