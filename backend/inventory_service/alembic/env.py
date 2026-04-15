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
import app.models.inventory
import app.models.inter_company_transfer
import app.models.warehouse
import app.models.document
import app.models.movement
import app.models.stock
import app.models.stock_lot
import app.models.item_variant
import app.models.concept
import app.models.bom
import app.models.backflush_error
import app.models.customs_pedimento

target_metadata = Base.metadata

# ─── DB Configuration ─────────────────────────────────────────────────────────
def get_url():
    return os.getenv("CORE_DATABASE_URL") or os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

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
