import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database import AsyncSessionLocal
from app.models.subscription import Module, Plan
from app.core.enums import ModuleCode

async def seed_data():
    async with AsyncSessionLocal() as db:
        # 1. Seed Modules
        modules_data = [
            {"code": ModuleCode.AUTH_CORE, "name": "Autenticación Core", "is_core": True},
            {"code": ModuleCode.INVENTORY_CORE, "name": "Inventarios Core", "is_core": True},
            {"code": ModuleCode.MES_CORE, "name": "MES Operational Intelligence", "is_core": False},
            {"code": ModuleCode.WMS_CORE, "name": "WMS Advanced", "is_core": False},
        ]
        
        for m_data in modules_data:
            stmt = select(Module).where(Module.code == m_data["code"])
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                db.add(Module(**m_data))
        
        await db.flush()

        # 2. Seed Plans
        plans_data = [
            {
                "name": "Plan Básico",
                "description": "Acceso a servicios core de la plataforma",
                "modules": [ModuleCode.AUTH_CORE, ModuleCode.INVENTORY_CORE],
                "trial_days": 14
            },
            {
                "name": "Plan Pro",
                "description": "Acceso total a todos los módulos",
                "modules": [
                    ModuleCode.AUTH_CORE, 
                    ModuleCode.INVENTORY_CORE, 
                    ModuleCode.MES_CORE, 
                    ModuleCode.WMS_CORE
                ],
                "trial_days": 30
            }
        ]

        for p_data in plans_data:
            stmt = select(Plan).where(Plan.name == p_data["name"])
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                db.add(Plan(**p_data))
        
        await db.commit()
        print("✅ Seeding completed!")

if __name__ == "__main__":
    asyncio.run(seed_data())
