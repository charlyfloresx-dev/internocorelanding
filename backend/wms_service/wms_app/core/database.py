import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from .config import settings
from common.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL

def get_corrected_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if "postgresql" in url and "asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

# Base.metadata.clear() ya no es necesario y puede causar problemas de registro

engine = create_async_engine(
    get_corrected_url(DATABASE_URL),
    pool_pre_ping=True,
    echo=settings.ENV_MODE == "local"
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"❌ WMS DB Error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
