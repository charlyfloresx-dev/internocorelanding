import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import text
from app.db.db import AsyncSessionLocal
from app.models.uom import UOM

async def seed_master_data():
    print("🚀 [SEED] Iniciando carga de datos maestros...")
    
    # ID de empresa para modo DEMO / Pruebas
    demo_company_id = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
    user_id = uuid.UUID("66627167-32d9-4d20-991a-bf3f51cdb18d")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Limpieza (Asegúrate de que el nombre coincide con el __tablename__ de tu modelo UOM)
            # Si tu modelo dice __tablename__ = 'uoms', usa uoms.
            await session.execute(text("TRUNCATE TABLE uoms RESTART IDENTITY CASCADE;"))
            
            # 2. Datos de Unidades de Medida
            uoms = [
                UOM(
                    id=uuid.uuid4(),
                    company_id=demo_company_id,
                    code="UN",
                    name="Unidad",
                    plural="Unidades",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    created_by=user_id,
                    version_id=1
                ),
                UOM(
                    id=uuid.uuid4(),
                    company_id=demo_company_id,
                    code="KG",
                    name="Kilogramo",
                    plural="Kilogramos",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    created_by=user_id,
                    version_id=1
                )
            ]
            
            session.add_all(uoms)
            await session.commit()
            print("✅ Seed finalizado: UOMs (UN, KG) cargadas correctamente.")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error en seed: {e}")
            raise e

if __name__ == "__main__":
    asyncio.run(seed_master_data())