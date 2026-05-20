import asyncio
from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

# ─── Path Normalization (Importante para encontrar app.models) ────────────────
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Interpret the config file for Python logging.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─── Metadata ─────────────────────────────────────────────────────────────────
from common.models import Base
# Importamos todos los modelos para que autogenerate los detecte
import common.models.audit
import inventory_app.models.inventory
import inventory_app.models.inter_company_transfer
import inventory_app.models.warehouse
import inventory_app.models.document
import inventory_app.models.movement
import inventory_app.models.stock
import inventory_app.models.stock_lot
import inventory_app.models.item_variant
import inventory_app.models.bom
import inventory_app.models.backflush_error
import inventory_app.models.customs_pedimento

target_metadata = Base.metadata

# ─── DB Configuration ─────────────────────────────────────────────────────────
def get_url():
    """Transforma la URL usando el sistema de configuración global (lee el .env raíz automáticamente)"""
    from common.config import settings
    return str(settings.DATABASE_URL)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version_inv"
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        version_table="alembic_version_inv"
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = AsyncEngine(
        engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
