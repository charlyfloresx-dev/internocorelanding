from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List

class IRateProvider(ABC):
    @abstractmethod
    async def get_rates(self, base: str, targets: List[str]) -> Dict[str, Decimal]:
        ...

    @abstractmethod
    async def get_all_market_rates(self) -> Dict[str, Decimal]:
        ...
