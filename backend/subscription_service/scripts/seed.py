import asyncio
import argparse
import uuid
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

# Ajuste de path para encontrar 'app' y 'common'
sys.path.append(os.getcwd())

from app.infrastructure.database import AsyncSessionLocal
from app.models.subscription import Module, Plan, Subscription, Entitlement
from app.core.enums import ModuleCode, SubscriptionStatus
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seed_subscription")

LOGISTICS_ID   = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")

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
    plans_data = [
        {
            "name": "Plan Pro",
            "description": "Acceso total a todos los módulos",
            "modules": [
                ModuleCode.AUTH_CORE, ModuleCode.INVENTORY_CORE, 
                ModuleCode.MES_CORE, ModuleCode.WMS_CORE
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
    await db.flush()

async def seed_entitlements(db, company_id: uuid.UUID):
    logger.info(f"  [SUBS] Cargando suscripciones para: {company_id}")
    stmt_plan = select(Plan).where(Plan.name == "Plan Pro")
    plan_pro = (await db.execute(stmt_plan)).scalars().first()
    
    if plan_pro:
        stmt_sub = select(Subscription).where(Subscription.company_id == company_id)
        exists_sub = (await db.execute(stmt_sub)).scalars().first()
        if not exists_sub:
            sub = Subscription(
                company_id=company_id, tenant_id=company_id,
                plan_id=plan_pro.id,
                status=SubscriptionStatus.ACTIVE,
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc) + timedelta(days=3650)
            )
            db.add(sub)
            logger.info(f"    ➕ Suscripción creada para: {company_id}")
            await db.flush()

        for module_code in plan_pro.modules:
            stmt_ent = select(Entitlement).where(
                Entitlement.company_id == company_id,
                Entitlement.module_code == module_code
            )
            if not (await db.execute(stmt_ent)).scalars().first():
                ent = Entitlement(
                    company_id=company_id, tenant_id=company_id,
                    module_code=module_code, is_enabled=True
                )
                db.add(ent)
                logger.info(f"    ➕ Entitlement [{module_code}] para: {company_id}")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--company-id", help="Company ID to seed")
    parser.add_argument("--wipe", action="store_true")
    args = parser.parse_args()

    async with AsyncSessionLocal() as db:
        try:
            logger.info("🌱 Iniciando Seeding de Subscripciones")
            if args.wipe:
                 from sqlalchemy import text
                 await db.execute(text("DROP TABLE IF EXISTS audit_subscription_logs, entitlements, subscriptions, plans, modules CASCADE"))
                 await db.commit()

            # Asegurar esquema
            async with AsyncSessionLocal().bind.begin() as conn:
                from app.models import Base
                await conn.run_sync(Base.metadata.create_all)
            
            await seed_modules(db)
            await seed_plans(db)
            cid = uuid.UUID(args.company_id) if args.company_id else LOGISTICS_ID
            await seed_entitlements(db, cid)
            await db.commit()
            logger.info("✅ Seeding Subscription completado.")
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error en seeding Subscription: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
