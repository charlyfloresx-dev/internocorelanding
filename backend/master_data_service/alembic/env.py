import sys
import os
import asyncio # <--- NECESARIO
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine # <--- NECESARIO
from alembic import context

# 1. Configuración de PATHs para Docker
# Usamos rutas relativas para que funcione tanto en local como en Docker
current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # backend/master_data_service
sys.path.insert(0, current_path)
sys.path.insert(0, os.path.join(current_path, '..')) # backend/ (para encontrar common)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 2. IMPORTACIÓN DE LA BASE Y MODELOS
from app.db.db import Base
# Importar modelos para que Alembic los detecte
from app.models.uom import UOM
from app.models.product_category import ProductCategory
from app.models.product_brand import ProductBrand
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

# --- FUNCIÓN AUXILIAR PARA CORRER MIGRACIONES SINCRONAS ---
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

# --- FUNCIÓN ONLINE ASÍNCRONA ---
async def run_migrations_online() -> None:
    # Usamos create_async_engine para asyncpg
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Ejecutamos las migraciones síncronas dentro del contexto asíncrono
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    # Fix para Windows: SelectorEventLoopPolicy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Usamos asyncio.run para ejecutar la función asíncrona
    asyncio.run(run_migrations_online())