import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, cast, String
from app.core.database import engine
from app.models import Warehouse, Company

async def seed_warehouses():
    async with AsyncSession(engine) as session:
        # Buscamos nuestra Empresa Demo
        demo_company_id = "eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e"
        
        # 1. Verificar que el almacén no exista ya
        print("🔍 Verificando Almacén Central...")
        stmt = select(Warehouse).where(
            Warehouse.company_id == uuid.UUID(demo_company_id),
            Warehouse.code == "CENTRAL"
        )
        result = await session.execute(stmt)
        
        if result.scalar_one_or_none():
            print("📦 El Almacén Central ya existe.")
            return

        # 2. Crear Almacén
        print("🚀 Creando Almacén Central para la Demo...")
        central_wh = Warehouse(
            id=uuid.uuid4(),
            company_id=uuid.UUID(demo_company_id),
            code="CENTRAL",
            name="Almacén Central Principal",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            version_id=1
        )
        
        session.add(central_wh)
        try:
            await session.commit()
            print(f"✅ Almacén Central creado con éxito.")
        except Exception as e:
            await session.rollback()
            print(f"❌ Error al crear almacén: {e}")

if __name__ == "__main__":
    asyncio.run(seed_warehouses())