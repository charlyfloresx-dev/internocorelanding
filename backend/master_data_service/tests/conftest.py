import asyncio
import pytest
import uuid
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from unittest.mock import patch
with patch("common.config.settings.DATABASE_URL", "sqlite+aiosqlite:///:memory:"):
    from master_app.main import master_app
    from common.domain import Base
    from master_app.db.session import get_db

# Patch UUID for SQLite tests
import sqlalchemy
from sqlalchemy.types import TypeDecorator, CHAR
import uuid

class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(CHAR(36))
        else:
            return dialect.type_descriptor(sqlalchemy.types.UUID())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)

# Patch both sqlalchemy.types and sqlalchemy.dialects.postgresql
sqlalchemy.types.UUID = GUID
import sqlalchemy.dialects.postgresql
sqlalchemy.dialects.postgresql.UUID = GUID

# DB de prueba en memoria
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Configuraci\u00f3n del event loop para evitar DeprecationWarning."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(DATABASE_URL)
    
    # IMPORTANTE: Asegurar el orden para que las FKs se resuelvan al cargar el metadata
    from master_app.models.uom import UOM
    from master_app.models.product_category import ProductCategory
    from master_app.models.product import Product, ProductVersion
    from master_app.models.product_price import ProductPrice
    from master_app.models.price_agreement import PriceAgreement
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Inyecta la sesi\u00f3n de DB con aislamiento por test via transacciones."""
    connection = await db_engine.connect()
    transaction = await connection.begin()
    
    session = AsyncSession(bind=connection, expire_on_commit=False)
    
    # Override de la dependencia de FastAPI
    async def override_get_db():
        yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    await session.close()
    await transaction.rollback()
    await connection.close()
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# --- Factories ---

@pytest.fixture
async def uom_factory(db):
    from master_app.models.uom import UOM
    async def _create(code: str = "EA", name: str = "Each"):
        uom = UOM(code=code, name=name, company_id=uuid.uuid4())
        db.add(uom)
        await db.flush()
        return uom
    return _create

@pytest.fixture
async def category_factory(db):
    from master_app.models.product_category import ProductCategory
    async def _create(name: str = "Electronics"):
        cat = ProductCategory(name=name, company_id=uuid.uuid4())
        db.add(cat)
        await db.flush()
        return cat
    return _create

@pytest.fixture
def mock_user():
    from common.domain.entities.user_context import UserContext
    return UserContext(
        user_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        role_names=["admin"],
        scopes=["*"],
        status="ACTIVE"
    )
