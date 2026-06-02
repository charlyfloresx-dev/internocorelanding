from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
import uuid
from common.enums import PartnerType

class PartnerBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=250)
    tax_id: Optional[str] = Field(None, max_length=20)
    type: PartnerType = PartnerType.BOTH
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    is_active: bool = True

class PartnerCreate(PartnerBase):
    pass

class PartnerUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=250)
    tax_id: Optional[str] = Field(None, max_length=20)
    type: Optional[PartnerType] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class PartnerResponse(PartnerBase):
    id: uuid.UUID
    company_id: uuid.UUID

    class Config:
        from_attributes = True


# ── Bulk Import (Onboarding Wizard Phase 168) ────────────────────────────────

class PartnerBulkItem(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=250)
    type: PartnerType = PartnerType.BOTH
    tax_id: Optional[str] = Field(None, max_length=20)
    rfc: Optional[str] = Field(None, max_length=20)   # alias for tax_id (CSV template uses rfc)
    email: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = None  # appended to address when address is absent

class PartnerBulkResult(BaseModel):
    created: int = 0
    skipped: int = 0
    errors: List[str] = []
