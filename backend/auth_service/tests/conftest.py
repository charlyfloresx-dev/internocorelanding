import pytest
import uuid
import sys
import time
from pathlib import Path
from typing import Dict
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from unittest.mock import patch
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Add backend to path for imports
sys.path.insert(0, str(project_root / "backend"))
sys.path.insert(0, str(project_root / "backend" / "auth_service"))

from auth_app.main import app
from auth_app.models import Base, User, Company, Role, RefreshTokenFamily, RefreshTokenRotationAudit
from auth_app.core.database import get_db
from auth_app.core.config import settings

DATABASE_URL = "postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/dbname"


class RedisMock:
    """Mock de Redis con soporte para TTL real."""
    def __init__(self):
        self.storage: Dict[str, str] = {}
        self.expirations: Dict[str, float] = {}

    def _is_expired(self, key: str) -> bool:
        if key not in self.expirations:
            return False
        if time.time() > self.expirations[key]:
            del self.storage[key]
            del self.expirations[key]
            return True
        return False

    async def get(self, key: str):
        if self._is_expired(key):
            return None
        return self.storage.get(key)

    async def setex(self, key: str, ttl: int, value: str):
        self.storage[key] = value
        self.expirations[key] = time.time() + ttl
        return True

    async def exists(self, key: str):
        if self._is_expired(key):
            return 0
        return 1 if key in self.storage else 0


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    with patch.object(settings, "SECRET_KEY", "test_secret_key_interno_core"), \
         patch.object(settings, "ALGORITHM", "HS256"), \
         patch.object(settings, "SELECTION_TOKEN_EXPIRE_MINUTES", 10):
        yield


@pytest.fixture
async def db():
    """
    Función-scoped: cada test obtiene su propio engine (NullPool) + transacción
    que se revierte al finalizar. NullPool evita conflictos de event loop entre tests.
    """
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool, echo=False)
    async with engine.begin() as setup_conn:
        await setup_conn.run_sync(Base.metadata.create_all)

    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest.fixture
def redis_mock():
    mock = RedisMock()
    with patch("auth_app.core.middleware.redis_client", mock):
        yield mock


@pytest.fixture
async def async_client(db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─────────────────────────────────────────────────────────────────────────────
# RTR Phase C Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def secret_key():
    """Secret key para JWT signing en tests RTR."""
    return "test_secret_key_for_jwt_signing_12345"


@pytest.fixture
async def test_company(db):
    """Empresa de test para RTR."""
    from datetime import datetime
    company = Company(
        id=uuid.uuid4(),
        name="Test Company RTR",
        status="ACTIVE",
        default_tax_rate=0.16,
        created_at=datetime.utcnow()
    )
    db.add(company)
    await db.flush()
    return company


@pytest.fixture
async def test_user(db):
    """Usuario de test. email vive en UserCredential (modelo separado)."""
    user = User(
        id=uuid.uuid4(),
        first_name="Test",
        last_name_pat="User",
        is_active=True
    )
    db.add(user)
    await db.flush()
    return user


@pytest.fixture
async def test_family(db, test_user, test_company):
    """Familia RTR gen=0, ventana de idempotencia ya expirada."""
    import os
    from datetime import datetime, timedelta
    family = RefreshTokenFamily(
        id=uuid.uuid4(),
        company_id=test_company.id,
        tenant_id=test_company.id,
        user_id=test_user.id,
        family_salt=os.urandom(32).hex(),  # único por test — evita conflicto en UNIQUE constraint
        current_generation=0,
        revoked_at=None,
        last_refresh_at=datetime.utcnow(),
        refresh_window_expires_at=datetime.utcnow() - timedelta(seconds=10)
    )
    db.add(family)
    await db.flush()
    return family
