import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

# 1. Configuración de la conexión a la base de datos (Docker Network)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@postgres-db:5432/master_data_db"
)

# 2. Motor asíncrono de SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False)

# 3. Fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 4. Dependencia para inyectar sesiones en los endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session