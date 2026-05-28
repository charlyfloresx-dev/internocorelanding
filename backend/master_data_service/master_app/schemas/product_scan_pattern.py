import uuid
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class ScanPatternRead(BaseModel):
    id: uuid.UUID
    item_code: str
    pattern_name: str
    regex: str
    error_message: str
    priority: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ScanPatternCreate(BaseModel):
    pattern_name: str = Field(..., min_length=1, max_length=100,
                              description="Label: LOT_REQUIRED, NOMENCLATURE, etc.")
    regex: str = Field(..., min_length=1, max_length=500,
                       description="Python-compatible regex. Applied with re.fullmatch().")
    error_message: str = Field(..., min_length=1, max_length=500)
    priority: int = Field(0, ge=0, description="Lower = evaluated first")
    is_active: bool = True


class ScanPatternUpdate(BaseModel):
    pattern_name: Optional[str] = Field(None, max_length=100)
    regex: Optional[str] = Field(None, max_length=500)
    error_message: Optional[str] = Field(None, max_length=500)
    priority: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
