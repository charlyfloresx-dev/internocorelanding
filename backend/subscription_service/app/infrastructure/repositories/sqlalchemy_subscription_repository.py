import uuid
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.models.subscription import Subscription, Plan, Entitlement, AuditSubscriptionLog


class SQLAlchemySubscriptionRepository(ISubscriptionRepository):
    """Concrete SQLAlchemy implementation for Subscription Repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_subscription_by_company(self, company_id: uuid.UUID) -> Optional[Any]:
        stmt = select(Subscription).where(Subscription.company_id == company_id).options(selectinload(Subscription.plan))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_plan_by_stripe_product(self, stripe_product_id: str, company_id: Optional[uuid.UUID] = None) -> Optional[Any]:
        # En el modelo actual no veo stripe_product_id, asumo que 'name' o una columna similar se mapea
        # Para el refactor usaré una lógica basada en el nombre del plan si el campo no existe.
        stmt = select(Plan).where(Plan.name == stripe_product_id)
        # Plan is global but we accept company_id for compliance consistency
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_subscription_by_stripe_id(self, stripe_subscription_id: str, company_id: Optional[uuid.UUID] = None) -> Optional[Any]:
        stmt = select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id).options(selectinload(Subscription.plan))
        if company_id:
             stmt = stmt.where(Subscription.company_id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_subscription(self, subscription_data: dict) -> Any:
        subscription = Subscription(**subscription_data)
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def update_subscription(self, stripe_subscription_id: str, update_data: dict, company_id: Optional[uuid.UUID] = None) -> Any:
        stmt = select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
        if company_id:
             stmt = stmt.where(Subscription.company_id == company_id)
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()
        if subscription:
            for key, value in update_data.items():
                setattr(subscription, key, value)
            await self.db.commit()
            await self.db.refresh(subscription)
        return subscription

    async def get_active_plans(self, company_id: Optional[uuid.UUID] = None) -> List[Any]:
        stmt = select(Plan)
        # Plan is global but company_id is provided for structural interface consistency
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_entitlements_by_company(self, company_id: uuid.UUID) -> List[Any]:
        stmt = select(Entitlement).where(Entitlement.company_id == company_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_subscription_by_company_and_version(self, company_id: uuid.UUID, version_id: int) -> Optional[Any]:
        stmt = select(Subscription).where(
            Subscription.company_id == company_id,
            Subscription.version_id == version_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def check_active_users_for_module(self, company_id: uuid.UUID, module_code: str) -> bool:
        from sqlalchemy import text
        # Simplificación demo: buscar roles que contengan el nombre del módulo
        check_stmt = text(
            "SELECT COUNT(*) FROM user_company_roles ucr "
            "JOIN roles r ON ucr.role_id = r.id "
            "WHERE ucr.company_id = :cid AND r.name LIKE :mod"
        )
        count_res = await self.db.execute(check_stmt, {"cid": company_id, "mod": f"%{module_code.split('_')[0].lower()}%"})
        return count_res.scalar() > 0

    async def upsert_entitlement(self, company_id: uuid.UUID, module_code: str, is_enabled: bool, subscription_id: uuid.UUID) -> None:
        stmt = select(Entitlement).where(
            Entitlement.company_id == company_id,
            Entitlement.module_code == module_code
        )
        result = await self.db.execute(stmt)
        ent = result.scalar_one_or_none()
        if ent:
            ent.is_enabled = is_enabled
        else:
            ent = Entitlement(
                company_id=company_id,
                module_code=module_code,
                is_enabled=is_enabled,
                source_subscription_id=subscription_id
            )
            self.db.add(ent)
        await self.db.flush()

    async def update_subscription_status(self, company_id: uuid.UUID, new_status: str) -> None:
        stmt = update(Subscription).where(Subscription.company_id == company_id).values(status=new_status)
        await self.db.execute(stmt)
        await self.db.commit()

    async def extend_grace_period(self, company_id: uuid.UUID, days: int) -> Any:
        from datetime import datetime, timedelta, timezone
        sub = await self.get_subscription_by_company(company_id)
        if sub:
            old_grace = sub.grace_period_until or datetime.now(timezone.utc)
            new_grace = old_grace + timedelta(days=days)
            sub.grace_period_until = new_grace
            sub.status = "past_due"
            await self.db.commit()
            await self.db.refresh(sub)
            return sub
        return None

    async def save_audit_log(self, audit_data: dict) -> None:
        log = AuditSubscriptionLog(**audit_data)
        self.db.add(log)
        await self.db.flush() # Flush instead of commit to maintain command transaction
