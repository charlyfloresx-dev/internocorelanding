import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from common.infrastructure.database import (
    engine as common_engine,
    AsyncSessionLocal as CommonAsyncSessionLocal,
    get_db as common_get_db
)

logger = logging.getLogger(__name__)

# Re-exportamos para mantener compatibilidad con el resto del auth_service
engine = common_engine
AsyncSessionLocal = CommonAsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Proxy dependency para usar el get_db de common.
    """
    async for session in common_get_db():
        yield session
