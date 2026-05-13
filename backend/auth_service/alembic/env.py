import asyncio
import asyncio
from logging.config import fileConfig
import sys
import os

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. Configurar el Path para encontrar 'app' y 'common'
# Usamos rutas relativas para compatibilidad con ejecución local y Docker
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_path)
sys.path.append(os.path.abspath(os.path.join(base_path, "..")))

# 2. Importar Configuración y Modelos
from auth_app.core.config import settings # type: ignore
# Al importar 'Base' desde el paquete 'app.models', el __init__.py se encarga
# de cargar todos los modelos y registrarlos en la metadata.
from auth_app.models import Base # type: ignore

# 3. Configuración de Alembic
config = context.config

# Interpretar el archivo de configuración de log
# if config.config_file_name is not None:
#     # Comentado para evitar el KeyError: 'formatters' y usar el logging por defecto.
#     fileConfig(config.config_file_name)
# Sobrescribir la URL de la base de datos con la variable de entorno
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version_auth"
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        version_table="alembic_version_auth"
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    
    # Asegurar que usamos la URL correcta
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
