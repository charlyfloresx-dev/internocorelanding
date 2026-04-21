import asyncio
import logging
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Ajuste de path para encontrar 'app' y 'common'
# Si estamos en backend/master_data_service/scripts/migrate_schema.py
# El root del backend es el padre de master_data_service/
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__)) # scripts
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_PATH)) # backend
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, "master_data_service"))

from master_app.db.db import engine
from common.models import MultiTenantBase
# Import all models to ensure they are registered with MultiTenantBase.metadata
import master_app.models  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_master_data")

async def apply_migrations():
    """
    Ensures all tables defined in models exist in the database.
    This is a safety measure because some Alembic migrations seem to be missing table creations.
    """
    logger.info(">> [MASTER DATA] Checking for missing tables via Base.metadata.create_all...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(MultiTenantBase.metadata.create_all)
        logger.info("✅ Tables synchronized successfully.")
    except Exception as e:
        logger.error(f"❌ Error synchronizing tables: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(apply_migrations())
