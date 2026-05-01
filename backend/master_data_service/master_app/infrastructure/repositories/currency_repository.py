from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from master_app.domain.repositories.currency import ICurrencyRepository
from master_app.domain.entities.currency import CurrencyRate
from master_app.models.exchange_rate import CurrencyExchangeRate
from common.models import Company

class SQLAlchemyCurrencyRepository(ICurrencyRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, orm: CurrencyExchangeRate) -> Optional[CurrencyRate]:
        if not orm: return None
        return CurrencyRate(
            id=orm.id,
            company_id=orm.company_id,
            base_currency=orm.base_currency,
            target_currency=orm.target_currency,
            rate=orm.rate,
            source=orm.source,
            is_suspicious=orm.is_suspicious,
            is_verified=orm.is_verified,
            captured_at=orm.captured_at,
            captured_by=orm.captured_by
        )

    async def get_latest_verified_rate(self, company_id: UUID, base: str, target: str, since: Optional[datetime] = None) -> Optional[CurrencyRate]:
        zero_uuid = UUID(int=0)
        
        conditions = [
            or_(
                CurrencyExchangeRate.company_id == company_id,
                CurrencyExchangeRate.company_id == zero_uuid
            ),
            CurrencyExchangeRate.base_currency == base.upper(),
            CurrencyExchangeRate.target_currency == target.upper(),
            CurrencyExchangeRate.is_verified == True
        ]
        
        if since:
            conditions.append(CurrencyExchangeRate.captured_at >= since)
            
        stmt = (
            select(CurrencyExchangeRate)
            .where(*conditions)
            .order_by(
                desc(CurrencyExchangeRate.company_id == company_id),
                desc(CurrencyExchangeRate.captured_at)
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        orm = result.scalars().first()
        return self._to_domain(orm)

    async def save_rate(self, company_id: UUID, base: str, target: str, rate: Decimal, source: str, is_suspicious: bool, is_verified: bool, captured_by: Optional[UUID] = None) -> CurrencyRate:
        new_record = CurrencyExchangeRate(
            company_id=company_id,
            base_currency=base.upper(),
            target_currency=target.upper(),
            rate=rate,
            source=source,
            is_suspicious=is_suspicious,
            is_verified=is_verified,
            captured_by=captured_by
        )
        self.session.add(new_record)
        await self.session.flush()
        return self._to_domain(new_record)

    async def get_by_id(self, rate_id: UUID, company_id: Optional[UUID] = None) -> Optional[CurrencyRate]:
        stmt = select(CurrencyExchangeRate).where(CurrencyExchangeRate.id == rate_id)
        if company_id:
            stmt = stmt.where(CurrencyExchangeRate.company_id == company_id)
        result = await self.session.execute(stmt)
        orm = result.scalars().first()
        return self._to_domain(orm)

    async def verify_rate(self, rate_id: UUID, company_id: Optional[UUID] = None) -> bool:
        stmt = select(CurrencyExchangeRate).where(CurrencyExchangeRate.id == rate_id)
        if company_id:
            stmt = stmt.where(CurrencyExchangeRate.company_id == company_id)
        result = await self.session.execute(stmt)
        orm = result.scalars().first()
        if orm:
            orm.is_verified = True
            await self.session.flush()
            return True
        return False

    async def has_automatic_rates_today(self, company_id: UUID) -> bool:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(CurrencyExchangeRate.id)
            .where(
                CurrencyExchangeRate.company_id == company_id,
                CurrencyExchangeRate.captured_at >= today_start,
                CurrencyExchangeRate.source != "manual"
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    # Legacy implementations
    async def get_company_base_currency(self, company_id: UUID) -> str:
        result = await self.session.execute(
            select(Company.base_currency).where(Company.id == company_id)
        )
        base = result.scalar_one_or_none()
        return base or "USD"

    async def get_distinct_target_currencies(self, company_id: UUID) -> List[str]:
        query = select(CurrencyExchangeRate.target_currency).where(
            CurrencyExchangeRate.company_id == company_id
        ).distinct()
        distinct_targets = (await self.session.execute(query)).scalars().all()
        return list(distinct_targets)
