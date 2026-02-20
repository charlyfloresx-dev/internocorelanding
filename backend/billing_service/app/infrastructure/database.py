import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from common.domain import MultiTenantBase

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/billing_db")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Factory de sesiones async
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

Base = MultiTenantBase


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
