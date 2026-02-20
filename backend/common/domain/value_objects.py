from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from .enums import CurrencyType

@dataclass(frozen=True)
class Money:
    """
    Value Object para manejo monetario seguro.
    Evita errores de punto flotante usando Decimal.
    """
    amount: Decimal
    currency: CurrencyType = CurrencyType.USD

    def __add__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            raise TypeError("Operands must be of type Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} vs {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            raise TypeError("Operands must be of type Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} vs {other.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)

@dataclass(frozen=True)
class UOM:
    """
    Unit of Measure (Unidad de Medida) para WMS/MES.
    Ejemplo: code='EA', name='Each', conversion_factor=1.0
    """
    code: str
    name: str
    symbol: Optional[str] = None
    conversion_factor: float = 1.0 

@dataclass(frozen=True)
class Address:
    """
    Value Object para direcciones f\u00edsicas.
    """
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    address_type: str = "Work"
