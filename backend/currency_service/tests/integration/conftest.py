import os
import sys
import pytest
import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# root de /app
sys.path.append("/app")

from app.models.exchange_rate import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@postgres-db:5432/currency_db")

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest.fixture
def anyio_backend():
    return 'asyncio'
