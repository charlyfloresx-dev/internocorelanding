from pydantic import BaseModel
from typing import Optional

class Coordinates(BaseModel):
    lat: float
    lng: float

class OwnershipInfo(BaseModel):
    owner_name: str
    property_type: Optional[str] = None
    status: str = "Validated"

class PropertyValidationResponse(BaseModel):
    address: str
    cadastral_key: str
    owner_name: Optional[str] = None
    land_use: Optional[str] = None
    location: Optional[Coordinates] = None
    status: str = "Validated"
