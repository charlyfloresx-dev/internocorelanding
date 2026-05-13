from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from asset_app.core.config import settings
from asset_app.domain.models.opportunity import Base
from common.logger import get_logger

logger = get_logger(__name__)


engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False,
    pool_size=5,
    max_overflow=10,)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncSession:
    """Dependency de FastAPI que provee una sesión de base de datos por request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Crea las tablas al arrancar el servicio (solo para desarrollo local)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Asset Manager DB: tablas creadas/verificadas correctamente.")
