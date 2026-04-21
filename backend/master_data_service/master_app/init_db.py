import asyncio
import sys

# Asegurar que Python encuentre 'app' y 'common'
sys.path.insert(0, "/app")

from master_app.db.session import engine
from common.models import Base
# Importamos los modelos para asegurar que se registren en Base.metadata
# Asumimos que app.models expone los modelos (Product, UM, etc.)
import master_app.models 

async def init_db():
    print("🔄 [INIT DB] Sincronizando esquema de base de datos...")
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Descomentar solo para reset total
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Base de datos sincronizada.")

if __name__ == "__main__":
    asyncio.run(init_db())
