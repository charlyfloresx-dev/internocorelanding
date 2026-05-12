from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from common.infrastructure.database import get_db

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session
