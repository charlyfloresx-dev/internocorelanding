from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Usamos la URL de la base de datos configurada en las variables de entorno
# El wms_service usa DATABASE_URL seg\u00fan docker-compose
engine = create_async_engine(settings.DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)