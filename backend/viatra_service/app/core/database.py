import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

# NOTE: Use the service-specific config wrapper
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
DATABASE_URL = os.getenv("CORE_DATABASE_URL") or os.getenv("DATABASE_URL") or settings.DATABASE_URL

def get_corrected_url(url: str) -> str:
    """
    Ensures compatibility with asyncpg driver.
    """
    if not url:
        return "sqlite+aiosqlite:///:memory:"
        
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    if "postgresql" in url and "asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return url

# Engine setup
engine = create_async_engine(get_corrected_url(DATABASE_URL),
    pool_pre_ping=True,
    echo=True
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
            logger.error(f"❌ DB Error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
