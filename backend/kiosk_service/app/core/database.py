from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from common.infrastructure.models.base import Base
from app.core.config import settings

engine = create_async_engine(settings.CORE_DATABASE_URL, pool_pre_ping=True, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def create_tables():
    """
    Tables are now managed by Alembic. 
    This function remains as a placeholder for model registration.
    """
    import app.models.event_photo  # noqa
    import app.models.payment_order  # noqa
    import app.models.event  # noqa
    import app.models.photo_approval  # noqa
    # Base.metadata.create_all is no longer used here.
