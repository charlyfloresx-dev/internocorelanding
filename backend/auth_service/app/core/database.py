import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# Importamos settings desde la ruta correcta dentro del contenedor
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL

def get_corrected_url(url: str) -> str:
    """
    Asegura compatibilidad con SQLAlchemy 2.0 y drivers asíncronos.
    Convierte postgresql:// en postgresql+asyncpg:// si es necesario.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    if "postgresql" in url and "asyncpg" not in url:
        logger.info("📡 Configurando driver asíncrono asyncpg para PostgreSQL")
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return url

# Creamos el motor asíncrono
engine = create_async_engine(
    get_corrected_url(DATABASE_URL),
    pool_pre_ping=True,
    echo=True  # Muestra el SQL generado en los logs de Docker
)

# SQLAlchemy 2.0 recomienda async_sessionmaker para flujos asíncronos
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para inyectar la sesión en los endpoints de FastAPI.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"❌ Error de DB detectado: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
