from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List, Optional

# Shared properties
class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    logo: Optional[str] = None # Added logo field
    base_currency: str = Field("USD", min_length=3, max_length=3)
    default_tax_rate: float = 0.16

# Properties to receive on company creation
class CompanyCreate(CompanyBase):
    pass

# Properties to receive on company update
class CompanyUpdate(CompanyBase):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    logo: Optional[str] = None # Explicitly add to allow updating logo

# Properties to return to client
class CompanyResponse(CompanyBase):
    # CORRECCIÓN: Tipo UUID en lugar de int
    id: UUID
    logo: Optional[str] = None # Include logo in response
    
    model_config = ConfigDict(from_attributes=True)
