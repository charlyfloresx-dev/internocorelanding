import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import os
import sys

# Asegurar que el path incluya la raíz para importar 'common' y 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.uom import UOM
from common.domain.entities import MultiTenantBase

# URL de base de datos desde entorno (conecto a master_data_db)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@postgres-db:5432/master_data_db")

async def seed_data():
    print("🚀 Iniciando Seed de Master Data...")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 1. Crear tablas si no existen (alternativa a alembic para el seed)
            async with engine.begin() as conn:
                await conn.run_sync(MultiTenantBase.metadata.create_all)
            
            # 2. Definir datos de UOM Globales
            uoms_to_seed = [
                UOM(code="KG", name="Kilogramo", plural="Kilogramos", translation_key="uom_kg", company_id=None),
                UOM(code="UN", name="Unidad", plural="Unidades", translation_key="uom_un", company_id=None),
                UOM(code="LB", name="Libra", plural="Libras", translation_key="uom_lb", company_id=None),
                UOM(code="M", name="Metro", plural="Metros", translation_key="uom_m", company_id=None),
            ]

            # 3. Insertar datos evitando duplicados (UniqueConstraint code+company_id)
            for uom in uoms_to_seed:
                result = await session.execute(
                    select(UOM).where(UOM.code == uom.code, UOM.company_id == None)
                )
                existing = result.scalars().first()
                
                if not existing:
                    session.add(uom)
                    print(f"✅ UOM {uom.code} agregada.")
                else:
                    print(f"ℹ️ UOM {uom.code} ya existe.")

            await session.commit()
            print("🎉 Seed de Master Data finalizado exitosamente.")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error durante el seed: {e}")
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_data())