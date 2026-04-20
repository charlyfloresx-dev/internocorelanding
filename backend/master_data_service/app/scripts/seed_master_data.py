import asyncio
import os
import sys
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# 1. Path fix for Docker and Local
sys.path.insert(0, "/app")
sys.path.append(os.getcwd())

# 2. Correct Model Import
from app.models.uom import UOM

# 3. Compliance Constants
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/interno_db")

UOM_DATA = [
    {"code": "KG", "name": "KILOGRAM", "factor": 1.0, "key": "uom.kg"},
    {"code": "UN", "name": "UNIT", "factor": 1.0, "key": "uom.unit"},
    {"code": "GL", "name": "GALLON", "factor": 3.78541, "key": "uom.gallon"},
    {"code": "LB", "name": "POUND", "factor": 0.453592, "key": "uom.pound"},
    {"code": "M", "name": "METER", "factor": 1.0, "key": "uom.meter"},
    {"code": "PZA", "name": "PIEZA", "factor": 1.0, "key": "uom.pieza"}
]

async def seed_master_data():
    print(f"🚀 [Interno Core] Remediation Seed: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            for data in UOM_DATA:
                # Global check (company_id is None)
                stmt = select(UOM).where(UOM.code == data["code"], UOM.company_id == None)
                result = await db.execute(stmt)
                exists = result.scalars().first()
                
                if not exists:
                    uom = UOM(
                        company_id=None,
                        code=data["code"],
                        name=data["name"],
                        translation_key=data["key"],
                        conversion_factor=data["factor"],
                        created_by=SYSTEM_USER_ID,
                        updated_by=SYSTEM_USER_ID
                    )
                    db.add(uom)
                    print(f"✅ Created Global UOM: {data['code']}")
                else:
                    # Upgrade existing (ensure system user is owner)
                    exists.created_by = SYSTEM_USER_ID
                    exists.updated_by = SYSTEM_USER_ID
                    exists.translation_key = data["key"]
                    print(f"🆙 Updated Global UOM: {data['code']}")
            
            await db.commit()
            print("🏁 Master Data Remediation Seed complete.")
        except Exception as e:
            await db.rollback()
            print(f"❌ Seed Error: {e}")
        finally:
            await db.close()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_master_data())
