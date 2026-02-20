import os
import sys
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# 1. Asegurar que Python encuentre la carpeta 'app'
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
# Importamos Base y todos los modelos para que Alembic los detecte
from app.models import Base, User, Company, Role, Permission, RolePermission, UserCompanyRole

# Interpret config file for Python logging
config = context.config
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception as e:
        print(f"⚠️ Warning: No se pudo cargar la config de logging: {e}")

target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        # 'typing.' para Mapped[List[str]] y 'postgresql.' para JSONB
        user_module_prefix="typing.",
        include_object=None,
        render_as_batch=False  # En Postgres no es necesario batch
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Modo Online: Conecta a la base de datos usando el driver asíncrono."""
    url = settings.DATABASE_URL
    
    # Inyectar asyncpg si no está presente (AWS/Local compatibility)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_offline() -> None:
    """Modo Offline."""
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        user_module_prefix="typing."
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())