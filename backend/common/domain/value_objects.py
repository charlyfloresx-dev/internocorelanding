from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USD"
    def __composite_values__(self):
        return self.amount, self.currency
    def __add__(self, other):
        return Money(self.amount + other.amount, self.currency)
    def __sub__(self, other):
        return Money(self.amount - other.amount, self.currency)

@dataclass(frozen=True)
class UOM:
    code: str
    name: str
    symbol: Optional[str] = None
    conversion_factor: float = 1.0

@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    address_type: str = "Work"
