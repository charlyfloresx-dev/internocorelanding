import asyncio
import os
import sys
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Path fix
sys.path.insert(0, "/app")
sys.path.append(os.getcwd())

from master_app.models.product_category import ProductCategory
from master_app.models.movement_concept import MovementConcept, MovementType
from master_app.models.uom import UOM

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/master_data_db")
COMPANY_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

CATEGORIES = [
    {"code": "RAW", "name": "Materias Primas"},
    {"code": "WIP", "name": "Trabajo en Proceso"},
    {"code": "FIN", "name": "Producto Terminado"},
    {"code": "MRO", "name": "Mantenimiento y Operación"}
]

async def seed_charly():
    print(f"🌱 Seeding Master Data for Charly Company: {COMPANY_ID}")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # Seed Categories
            for cat in CATEGORIES:
                db_cat = ProductCategory(
                    id=uuid.uuid4(),
                    company_id=COMPANY_ID,
                    code=cat["code"],
                    name=cat["name"],
                    created_by=SYSTEM_USER_ID,
                    updated_by=SYSTEM_USER_ID
                )
                db.add(db_cat)
                print(f"✅ Category added: {cat['name']}")

            await db.commit()
            print("🏁 Seeding complete.")
        except Exception as e:
            await db.rollback()
            print(f"❌ Error: {e}")
        finally:
            await db.close()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_charly())
