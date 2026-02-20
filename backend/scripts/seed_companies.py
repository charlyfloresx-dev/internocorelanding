import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, cast, String
from app.core.database import engine
from app.models import Company

async def seed_companies():
    async with AsyncSession(engine) as session:
        # ID Fijo para la demo
        demo_id = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
        
        print("🔍 Verificando existencia de la empresa...")
        stmt = select(Company).where(cast(Company.id, String) == str(demo_id))
        result = await session.execute(stmt)
        
        if result.scalar_one_or_none():
            print("🏢 Empresa Demo ya existe.")
            return

        print("🚀 Creando Empresa Demo...")
        # Usamos solo los campos que existen en tu modelo actual: id y name
        demo_company = Company(
            id=str(demo_id), 
            name="Empresa Demo Interno Core"
        )
        
        session.add(demo_company)
        try:
            await session.commit()
            print(f"✅ Empresa Demo creada con ID: {demo_id}")
        except Exception as e:
            await session.rollback()
            print(f"❌ Error al crear empresa: {e}")

if __name__ == "__main__":
    asyncio.run(seed_companies())