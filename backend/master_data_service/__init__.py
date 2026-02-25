import asyncio
import logging
from app.db.db import engine
from common.domain.entities import MultiTenantBase

# IMPORTANTE: Importar todos los modelos para que SQLAlchemy los registre en la metadata
from app.models.uom import UOM
from app.models.product_category import ProductCategory
from app.models.product_brand import ProductBrand
# Si tienes más modelos (ej. Product), impórtalos aquí

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    logger.info("🔄 [INIT DB] Sincronizando esquema de base de datos...")
    try:
        async with engine.begin() as conn:
            # Crea todas las tablas que heredan de MultiTenantBase
            await conn.run_sync(MultiTenantBase.metadata.create_all)
        logger.info("✅ Base de datos sincronizada exitosamente.")
    except Exception as e:
        logger.error(f"❌ Error sincronizando la base de datos: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(init_db())