from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List, Optional

# Shared properties
class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    logo: Optional[str] = None # Added logo field
    base_currency: str = Field("USD", min_length=3, max_length=3)
    default_tax_rate: Decimal = 0.16

# Properties to receive on company creation
class CompanyCreate(CompanyBase):
    pass

# Properties to receive on company update
class CompanyUpdate(CompanyBase):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    logo: Optional[str] = None
    timezone: Optional[str] = Field(None, max_length=50)
    internal_id_pattern: Optional[str] = Field(
        None, max_length=200,
        description="Regex para validar internal_id en login kiosko. Ej: ^EMP-\\\\d{4}$"
    )

# Properties to return to client
class CompanyResponse(CompanyBase):
    id: UUID
    logo: Optional[str] = None
    timezone: Optional[str] = None
    internal_id_pattern: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
