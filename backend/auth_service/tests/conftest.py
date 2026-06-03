import asyncio
import pytest
import uuid
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
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
from auth_app.models import Base, User, Company, Role, UserCompanyRole, RefreshTokenFamily, RefreshTokenRotationAudit
from auth_app.core.database import get_db
from auth_app.core.config import settings
from auth_app.core.security import hash_password

# DB de prueba en PostgreSQL real (no SQLite en memoria)
DATABASE_URL = "postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/dbname"

import time

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

@pytest.fixture(scope="session")
def event_loop():
    """Create and provide event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db(db_engine, event_loop):
    """Inyecta la sesión de DB y maneja transacciones limpias por test (Connection-level Transaction)."""
    connection = await db_engine.connect()
    transaction = await connection.begin()

    # expire_on_commit=False es vital para acceder a objetos tras el flush/commit manual en tests
    session = AsyncSession(bind=connection, expire_on_commit=False)

    # Override de la dependencia de FastAPI
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    # Limpieza: Cierra sesión, revierte transacción y libera conexión
    await session.close()
    await transaction.rollback()
    await connection.close()
    app.dependency_overrides.clear()

@pytest.fixture
def redis_mock():
    mock = RedisMock()
    with patch("app.core.middleware.redis_client", mock):
        yield mock

@pytest.fixture
async def company_factory(db):
    async def _create(name: str = "Test Company"):
        company = Company(name=name)
        db.add(company)
        await db.flush()
        return company
    return _create

@pytest.fixture
async def user_factory(db):
    async def _create(email: str = None, company_id: uuid.UUID = None):
        if not email:
            email = f"user_{uuid.uuid4().hex[:6]}@example.com"
        user = User(
            email=email,
            hashed_password=hash_password("password123"),
            is_active=True
        )
        db.add(user)
        await db.flush()
        return user
    return _create

@pytest.fixture
async def role_factory(db):
    async def _create(name: str = "operator"):
        role = Role(name=name)
        db.add(role)
        await db.flush()
        return role
    return _create

@pytest.fixture
async def async_client(db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures para Refresh Token Rotation (FASE C)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def secret_key():
    """Secret key para JWT signing."""
    return "test_secret_key_for_jwt_signing_12345"


@pytest.fixture
async def test_company(db):
    """Crear empresa de test."""
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
async def test_user(db, test_company):
    """Crear usuario de test."""
    user = User(
        id=uuid.uuid4(),
        email=f"test-rtr-{uuid.uuid4().hex[:6]}@example.com",
        first_name="Test",
        last_name_pat="User",
        is_active=True
    )
    db.add(user)
    await db.flush()

    # Link user to company via UserCompanyRole
    user_company_role = UserCompanyRole(
        user_id=user.id,
        company_id=test_company.id,
        role_id=None  # Can be null for test purposes
    )
    db.add(user_company_role)
    await db.flush()

    return user


@pytest.fixture
async def test_family(db, test_user, test_company):
    """Crear refresh token family de test."""
    from datetime import datetime, timedelta
    family = RefreshTokenFamily(
        id=uuid.uuid4(),
        company_id=test_company.id,
        user_id=test_user.id,
        family_salt="a" * 64,  # 64 hex chars
        current_generation=0,
        revoked_at=None,
        last_refresh_at=datetime.utcnow(),
        refresh_window_expires_at=datetime.utcnow() + timedelta(seconds=2)
    )
    db.add(family)
    await db.flush()
    return family

from auth_app.models import Base, User, Company, Role, UserCompanyRole, RefreshTokenFamily, RefreshTokenRotationAudit
from auth_app.core.database import get_db
from auth_app.core.config import settings
from auth_app.core.security import hash_password

# DB de prueba en PostgreSQL real (no SQLite en memoria)
DATABASE_URL = "postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/dbname"

import time

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

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db(db_engine):
    """Inyecta la sesión de DB y maneja transacciones limpias por test (Connection-level Transaction)."""
    connection = await db_engine.connect()
    transaction = await connection.begin()

    # expire_on_commit=False es vital para acceder a objetos tras el flush/commit manual en tests
    session = AsyncSession(bind=connection, expire_on_commit=False)

    # Override de la dependencia de FastAPI
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    # Limpieza: Cierra sesión, revierte transacción y libera conexión
    await session.close()
    await transaction.rollback()
    await connection.close()
    app.dependency_overrides.clear()

@pytest.fixture
def redis_mock():
    mock = RedisMock()
    with patch("app.core.middleware.redis_client", mock):
        yield mock

@pytest.fixture
async def company_factory(db):
    async def _create(name: str = "Test Company"):
        company = Company(name=name)
        db.add(company)
        await db.flush()
        return company
    return _create

@pytest.fixture
async def user_factory(db):
    async def _create(email: str = None, company_id: uuid.UUID = None):
        if not email:
            email = f"user_{uuid.uuid4().hex[:6]}@example.com"
        user = User(
            email=email,
            hashed_password=hash_password("password123"),
            company_id=company_id,
            is_active=True
        )
        db.add(user)
        await db.flush()
        return user
    return _create

@pytest.fixture
async def role_factory(db):
    async def _create(name: str = "operator"):
        role = Role(name=name)
        db.add(role)
        await db.flush()
        return role
    return _create

@pytest.fixture
async def async_client(db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures para Refresh Token Rotation (FASE C)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def secret_key():
    """Secret key para JWT signing."""
    return "test_secret_key_for_jwt_signing_12345"


@pytest.fixture
async def test_company(db):
    """Crear empresa de test."""
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
async def test_user(db, test_company):
    """Crear usuario de test."""
    from auth_app.core.security import hash_password
    user = User(
        id=uuid.uuid4(),
        company_id=test_company.id,
        email=f"test-rtr-{uuid.uuid4().hex[:6]}@example.com",
        full_name="Test User RTR",
        hashed_password=hash_password("password123"),
        status="ACTIVE"
    )
    db.add(user)
    await db.flush()
    return user


@pytest.fixture
async def test_family(db, test_user, test_company):
    """Crear refresh token family de test."""
    from datetime import datetime, timedelta
    family = RefreshTokenFamily(
        id=uuid.uuid4(),
        company_id=test_company.id,
        user_id=test_user.id,
        family_salt="a" * 64,  # 64 hex chars
        current_generation=0,
        revoked_at=None,
        last_refresh_at=datetime.utcnow(),
        refresh_window_expires_at=datetime.utcnow() + timedelta(seconds=2)
    )
    db.add(family)
    await db.flush()
    return family
