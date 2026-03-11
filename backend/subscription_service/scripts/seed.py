import asyncio
import argparse
import uuid
import logging
import os
import sys

# Ajuste de path para encontrar 'app' y 'common'
sys.path.append(os.getcwd())

from app.infrastructure.database import AsyncSessionLocal
from app.models.subscription import Module, Plan, Subscription, Entitlement
from app.core.enums import ModuleCode, SubscriptionStatus
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

# --- Constantes de Integración ---
CO_LOGISTICS_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seed_subscription")

async def seed_modules(db):
    logger.info("  [SUBS] Cargando módulos core...")
    modules_data = [
        {"code": ModuleCode.AUTH_CORE, "name": "Autenticación Core", "is_core": True},
        {"code": ModuleCode.INVENTORY_CORE, "name": "Inventarios Core", "is_core": True},
        {"code": ModuleCode.MES_CORE, "name": "MES Operational Intelligence", "is_core": False},
        {"code": ModuleCode.WMS_CORE, "name": "WMS Advanced", "is_core": False},
    ]
    
    for m_data in modules_data:
        stmt = select(Module).where(Module.code == m_data["code"])
        if not (await db.execute(stmt)).scalars().first():
            db.add(Module(**m_data))
            logger.info(f"    ➕ Módulo: {m_data['code']}")
    await db.flush()

async def seed_plans(db):
    logger.info("  [SUBS] Cargando planes de suscripción...")
    plans_data = [
        {
            "name": "Plan Básico",
            "description": "Acceso a servicios core de la plataforma",
            "modules": [ModuleCode.AUTH_CORE, ModuleCode.INVENTORY_CORE],
            "trial_days": 14,
            "storage_limit": 5*1024*1024*1024, # 5GB
            "allow_overage": False
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
            "trial_days": 30,
            "storage_limit": 50*1024*1024*1024, # 50GB
            "allow_overage": True
        }
    ]

    for p_data in plans_data:
        stmt = select(Plan).where(Plan.name == p_data["name"])
        if not (await db.execute(stmt)).scalars().first():
            db.add(Plan(**p_data))
            logger.info(f"    ➕ Plan: {p_data['name']}")

async def seed_entitlements(db):
    logger.info("  [SUBS] Cargando suscripciones de prueba...")
    
    # 1. Obtener Plan Pro
    stmt_plan = select(Plan).where(Plan.name == "Plan Pro")
    plan_pro = (await db.execute(stmt_plan)).scalars().first()
    
    if plan_pro:
        # 2. Crear Suscripción para Interno Logistics
        stmt_sub = select(Subscription).where(Subscription.company_id == CO_LOGISTICS_ID)
        exists_sub = (await db.execute(stmt_sub)).scalars().first()
        
        if not exists_sub:
            sub = Subscription(
                company_id=CO_LOGISTICS_ID,
                plan_id=plan_pro.id,
                status=SubscriptionStatus.ACTIVE,
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc) + timedelta(days=365)
            )
            db.add(sub)
            logger.info(f"    ➕ Suscripción creada para: {CO_LOGISTICS_ID}")
            await db.flush() # Para obtener el ID

        # 3. Habilitar Entitlements basados en Plan Pro
        for module_code in plan_pro.modules:
            stmt_ent = select(Entitlement).where(
                Entitlement.company_id == CO_LOGISTICS_ID,
                Entitlement.module_code == module_code
            )
            if not (await db.execute(stmt_ent)).scalars().first():
                ent = Entitlement(
                    company_id=CO_LOGISTICS_ID,
                    module_code=module_code,
                    is_enabled=True
                )
                db.add(ent)
                logger.info(f"    ➕ Entitlement [{module_code}] creado para: {CO_LOGISTICS_ID}")


async def main():
    async with AsyncSessionLocal() as db:
        try:
            logger.info("🌱 Iniciando Seeding para Subscription Service")
            
            # Garantizar que las tablas existan
            async with AsyncSessionLocal().bind.begin() as conn:
                from app.models import Base
                await conn.run_sync(Base.metadata.create_all)
            
            await seed_modules(db)
            await seed_plans(db)
            await seed_entitlements(db)
            await db.commit()
            logger.info("✅ Seeding Subscription completado.")
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error en seeding Subscription: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
