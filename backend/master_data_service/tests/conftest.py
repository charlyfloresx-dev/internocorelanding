import asyncio
import pytest
import uuid
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from common.domain import Base
from app.db.session import get_db

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
    from app.models.um import UM
    from app.models.category import ProductCategory
    from app.models.product import Product, ProductVersion
    
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
async def um_factory(db):
    from app.models.um import UM
    async def _create(code: str = "EA", name: str = "Each"):
        um = UM(code=code, name=name, company_id=uuid.uuid4())
        db.add(um)
        await db.flush()
        return um
    return _create

@pytest.fixture
async def category_factory(db):
    from app.models.category import ProductCategory
    async def _create(name: str = "Electronics"):
        cat = ProductCategory(name=name, company_id=uuid.uuid4())
        db.add(cat)
        await db.flush()
        return cat
    return _create
