import sys
import os
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# 1. Setup path
sys.path.append(os.getcwd())

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 2. Metadata
from app.models.exchange_rate import Base
target_metadata = Base.metadata

def get_url():
    return os.environ.get("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/currency_db")

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    url = get_url()
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    # Simple case
    context.configure(url=get_url(), target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(run_migrations_online())
