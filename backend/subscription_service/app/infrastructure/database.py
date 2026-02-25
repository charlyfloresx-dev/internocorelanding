import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
