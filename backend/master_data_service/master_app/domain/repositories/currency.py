from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from master_app.domain.entities.currency import CurrencyRate

class ICurrencyRepository(ABC):
    @abstractmethod
    async def get_latest_verified_rate(self, company_id: UUID, base: str, target: str, since: Optional[datetime] = None) -> Optional[CurrencyRate]:
        ...

    @abstractmethod
    async def save_rate(self, company_id: UUID, base: str, target: str, rate: Decimal, source: str, is_suspicious: bool, is_verified: bool, captured_by: Optional[UUID] = None) -> CurrencyRate:
        ...

    @abstractmethod
    async def get_by_id(self, rate_id: UUID, company_id: Optional[UUID] = None) -> Optional[CurrencyRate]:
        ...

    @abstractmethod
    async def verify_rate(self, rate_id: UUID, company_id: Optional[UUID] = None) -> bool:
        ...

    @abstractmethod
    async def has_automatic_rates_today(self, company_id: UUID) -> bool:
        ...

    # Legacy methods from master_app
    @abstractmethod
    async def get_company_base_currency(self, company_id: UUID) -> str:
        ...

    @abstractmethod
    async def get_distinct_target_currencies(self, company_id: UUID) -> List[str]:
        ...

class IRateProvider(ABC):
    @abstractmethod
    async def get_rates(self, base: str, targets: List[str]) -> Dict[str, Decimal]:
        ...

    @abstractmethod
    async def get_all_market_rates(self) -> Dict[str, Decimal]:
        ...
