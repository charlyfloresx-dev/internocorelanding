import uuid
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional

class ProductPriceRead(BaseModel):
    amount: Decimal
    currency: str

    class Config:
        from_attributes = True

class MockProductPrice:
    def __init__(self, a, c):
        self._amount = a
        self._currency = c
    
    @property
    def amount(self):
        return self._amount
    
    @property
    def currency(self):
        return self._currency

obj = MockProductPrice(Decimal("10.50"), "USD")
print(f"Attr amount: {getattr(obj, 'amount')}")
try:
    read = ProductPriceRead.model_validate(obj)
    print(f"Pydantic: {read}")
except Exception as e:
    print(f"Error: {e}")
