import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# ------------------------------------------------------------------------
# CONFIGURACIÓN DE PATHS (Resolución para Interno Core)
# ------------------------------------------------------------------------
# 1. Ruta de este archivo: /app/alembic/env.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Subimos niveles:
# /app
root_dir = os.path.abspath(os.path.join(current_dir, ".."))

# 3. Inyectamos en sys.path con prioridad máxima
sys.path.insert(0, root_dir)

# ------------------------------------------------------------------------
# Importación de Modelos y Metadata
# ------------------------------------------------------------------------
from common.infrastructure.models.base import Base
import mes_app.models

# ------------------------------------------------------------------------
# Configuración de Alembic
# ------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    """Transforma la URL usando el sistema de configuración global (lee el .env raíz automáticamente)"""
    from common.config import settings
    return str(settings.DATABASE_URL)

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version_mes",
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version_mes",
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine
    url = get_url()
    connectable = create_async_engine(url, pool_pre_ping=True, poolclass=pool.NullPool,)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
