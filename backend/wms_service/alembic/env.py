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
try:
    from common.models.base_models import Base
    import app.models 
    from app.core.config import settings
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
    """Transforma la URL para usar el driver psycopg2 (síncrono)"""
    return settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

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

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()