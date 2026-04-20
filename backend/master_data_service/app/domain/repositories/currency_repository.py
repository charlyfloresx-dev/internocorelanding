from abc import ABC, abstractmethod
from decimal import Decimal
import uuid
from typing import Dict, List, Optional
from app.domain.entities.currency_exchange_rate import CurrencyExchangeRateEntity

class ICurrencyClient(ABC):
    @abstractmethod
    async def get_latest_rates(self, base_currency: str, targets: List[str]) -> Dict[str, Decimal]:
        pass

class ICurrencyRepository(ABC):
    @abstractmethod
    async def get_company_base_currency(self, company_id: uuid.UUID) -> str:
        pass

    @abstractmethod
    async def get_distinct_target_currencies(self, company_id: uuid.UUID) -> List[str]:
        pass

    @abstractmethod
    async def get_latest_exchange_rate(self, company_id: uuid.UUID, base_currency: str, target_currency: str) -> Optional[CurrencyExchangeRateEntity]:
        pass

    @abstractmethod
    def save_rate(self, rate: CurrencyExchangeRateEntity) -> None:
        """Adds a rate to the tracking scope (without committing)"""
        pass

    @abstractmethod
    async def get_rate_by_id(self, rate_id: uuid.UUID) -> Optional[CurrencyExchangeRateEntity]:
        pass
