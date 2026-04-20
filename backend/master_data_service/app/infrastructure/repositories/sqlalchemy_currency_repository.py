import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from common.models import Company
from app.models.currency_exchange_rate import CurrencyExchangeRate
from app.domain.repositories.currency_repository import ICurrencyRepository
from app.domain.entities.currency_exchange_rate import CurrencyExchangeRateEntity

class SQLAlchemyCurrencyRepository(ICurrencyRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_company_base_currency(self, company_id: uuid.UUID) -> str:
        result = await self.session.execute(
            select(Company.base_currency).where(Company.id == company_id)
        )
        base = result.scalar_one_or_none()
        return base or "USD"

    async def get_distinct_target_currencies(self, company_id: uuid.UUID) -> List[str]:
        query = select(CurrencyExchangeRate.target_currency).where(
            CurrencyExchangeRate.company_id == company_id
        ).distinct()
        distinct_targets = (await self.session.execute(query)).scalars().all()
        return list(distinct_targets)

    async def get_latest_exchange_rate(
        self, company_id: uuid.UUID, base_currency: str, target_currency: str
    ) -> Optional[CurrencyExchangeRateEntity]:
        query = select(CurrencyExchangeRate).where(
            CurrencyExchangeRate.company_id == company_id,
            CurrencyExchangeRate.base_currency == base_currency,
            CurrencyExchangeRate.target_currency == target_currency
        ).order_by(desc(CurrencyExchangeRate.captured_at)).limit(1)
        result = await self.session.execute(query)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return CurrencyExchangeRateEntity(
            company_id=record.company_id,
            base_currency=record.base_currency,
            target_currency=record.target_currency,
            rate=record.rate,
            is_suspicious=record.is_suspicious,
            is_verified=record.is_verified,
            captured_at=record.captured_at,
            captured_by=record.captured_by,
            id=record.id
        )

    def save_rate(self, rate: CurrencyExchangeRateEntity) -> None:
        if rate.id:
            # We assume it exists and we're just attaching it or we don't handle updates this way
            # For simplicity, if id exists, we fetch and update (though better done differently in CQRS)
            raise NotImplementedError("Direct update not supported in save_rate without fetching. Use a command.")
        else:
            new_record = CurrencyExchangeRate(
                company_id=rate.company_id,
                base_currency=rate.base_currency,
                target_currency=rate.target_currency,
                rate=rate.rate,
                is_suspicious=rate.is_suspicious,
                is_verified=rate.is_verified,
                captured_at=rate.captured_at,
                captured_by=rate.captured_by
            )
            self.session.add(new_record)

    async def get_rate_by_id(self, rate_id: uuid.UUID) -> Optional[CurrencyExchangeRateEntity]:
        result = await self.session.execute(
            select(CurrencyExchangeRate).where(CurrencyExchangeRate.id == rate_id)
        )
        record = result.scalar_one_or_none()
        if not record:
            return None
        return CurrencyExchangeRateEntity(
            company_id=record.company_id,
            base_currency=record.base_currency,
            target_currency=record.target_currency,
            rate=record.rate,
            is_suspicious=record.is_suspicious,
            is_verified=record.is_verified,
            captured_at=record.captured_at,
            captured_by=record.captured_by,
            id=record.id
        )
