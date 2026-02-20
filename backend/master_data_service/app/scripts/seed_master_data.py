import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# 1. Ajuste de Path para Docker: /app es la raíz en el contenedor
sys.path.insert(0, "/app")

# 2. Importación corregida: El archivo es 'um.py' y la clase es 'UM'
from app.models.um import UM 

# DATABASE_URL para el contenedor
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@interno-db:5432/interno_db")

UOM_DATA = [
    {"code": "KG", "name": "KILOGRAM", "factor": 1.0},
    {"code": "UN", "name": "UNIT", "factor": 1.0},
    {"code": "GL", "name": "GALLON", "factor": 1.0},
    {"code": "LB", "name": "POUND", "factor": 1.0}
]

async def seed_master_data():
    print(f"🚀 [Interno Core] Iniciando Seed en: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            for data in UOM_DATA:
                # Buscamos registros globales (company_id is None)
                stmt = select(UM).where(UM.code == data["code"], UM.company_id == None)
                result = await db.execute(stmt)
                exists = result.scalars().first()
                
                if not exists:
                    uom = UM(
                        company_id=None, # Registro global para modo demo/base
                        code=data["code"],
                        name=data["name"],
                        conversion_factor=data["factor"]
                        # is_active viene por defecto en True desde BaseDomainEntity
                    )
                    db.add(uom)
                    print(f"✅ Agregado: {data['code']}")
                else:
                    print(f"⏩ Saltando (ya existe): {data['code']}")
            
            await db.commit()
            print("🏁 Seed completado con éxito.")
        except Exception as e:
            await db.rollback()
            print(f"❌ Error durante el seed: {e}")
        finally:
            await db.close()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_master_data())