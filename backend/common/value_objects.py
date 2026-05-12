from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import re

@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        # Enforce Decimal at initialization
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
        # Enforce exact 2-decimal precision with C# standard ROUND_HALF_UP
        rounded_amount = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, 'amount', rounded_amount)
        
    def __composite_values__(self):
        return self.amount, self.currency
        
    def __add__(self, other):
        if not isinstance(other, Money):
            raise TypeError("Cannot add Money to non-Money")
        if self.currency != other.currency:
            from common.exceptions import BusinessRuleException
            raise BusinessRuleException(f"Currency mismatch: {self.currency} != {other.currency}", code="CURRENCY_MISMATCH")
        return Money(self.amount + other.amount, self.currency)
        
    def __sub__(self, other):
        if not isinstance(other, Money):
            raise TypeError("Cannot subtract Money from non-Money")
        if self.currency != other.currency:
            from common.exceptions import BusinessRuleException
            raise BusinessRuleException(f"Currency mismatch: {self.currency} != {other.currency}", code="CURRENCY_MISMATCH")
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
    external_number: Optional[str] = None
    internal_number: Optional[str] = None
    neighborhood: Optional[str] = None
    cadastral_key: Optional[str] = None  # Ejemplo: PK020119
    property_type: Optional[str] = None  # R = Residencial, C = Comercial, I = Industrial
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def __post_init__(self):
        # Validate postal code structure (5 digits, optional 4 digit extension) to match .NET constraints
        if self.postal_code and not re.match(r"^\d{5}(-\d{4})?$", self.postal_code):
            from common.exceptions import ValidationException
            raise ValidationException(f"Invalid postal code format: {self.postal_code}", code="INVALID_POSTAL_CODE")