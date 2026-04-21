import asyncio
import sys
import os
import uuid
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import create_async_engine

# Ajuste de paths
sys.path.append(os.getcwd())
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

from common.domain import Base, ProductType
from master_app.models.product import Product
from master_app.db.session import DATABASE_URL

async def inject_dirty_data():
    print("[Antigravity] Inyectando datos de prueba (Integridad Logica Comprometida)...")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # Inyectar un producto con un estatus inexistente en el Enum
        # Nota: Usamos values() crudos para saltar chequeos de Pydantic/Domain Logic
        await conn.execute(
            insert(Base.metadata.tables["products"]).values(
                id=uuid.uuid4(),
                sku="DIRTY-001",
                name="Dirty Product",
                product_type=ProductType.GOODS,
                status="CORRUPTED_STATUS", # <--- VIOLACION DE ENUM
                company_id=uuid.uuid4(),
                is_active=True,
                version_id=1
            )
        )
        print("  [DIRTY] Insertado producto con estatus 'CORRUPTED_STATUS'.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(inject_dirty_data())
