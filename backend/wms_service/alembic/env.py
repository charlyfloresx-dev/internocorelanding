import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# ------------------------------------------------------------------------
# CONFIGURACIÓN DE PATHS (Resolución para Interno Core)
# ------------------------------------------------------------------------
# 1. Ruta de este archivo: /app/wms_service/alembic/env.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Subimos niveles:
# /app/wms_service
wms_service_dir = os.path.abspath(os.path.join(current_dir, ".."))
# /app (RAÍZ donde reside 'common' y 'wms_service')
root_dir = os.path.abspath(os.path.join(wms_service_dir, ".."))

# 3. Inyectamos en sys.path con prioridad máxima
sys.path.insert(0, root_dir)
sys.path.insert(0, wms_service_dir)

# --- BLOQUE DE DEPURACIÓN ---
print("\n" + "="*50)
print("ALEMBIC DEBUG")
print(f"Ruta Root detectada: {root_dir}")
common_path = os.path.join(root_dir, "common")
if os.path.exists(common_path):
    print(f"Contenido de common: {os.listdir(common_path)}")
print("="*50 + "\n")

# ------------------------------------------------------------------------
# Importación de Modelos y Metadata
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
try:
    from common.infrastructure.models.base import Base
    import app.models 
except ImportError as e:
    print(f"❌ Error de Importación en auditoría: {e}")
    raise

# ------------------------------------------------------------------------
# Configuración de Alembic
# ------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    """Transforma la URL para usar el driver psycopg2 (síncrono) o asyncpg dependendiendo de Alembic"""
    url = os.environ.get("DATABASE_URL")
    if not url:
        url = "postgresql+asyncpg://user:password@localhost:5433/wms_db"
    return str(url)

def run_migrations_offline() -> None:
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
    from sqlalchemy.ext.asyncio import create_async_engine
    url = get_url()
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_migrations_online())