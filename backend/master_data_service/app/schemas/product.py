import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from common.domain import ProductType, ProductStatus, VersionStatus

class ProductVersionRead(BaseModel):
    id: uuid.UUID
    version_number: int
    version_status: VersionStatus
    is_active: bool
    is_validated: bool
    change_reason: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProductRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    sku: str
    description: Optional[str] = None
    product_type: ProductType
    status: ProductStatus
    group_id: Optional[uuid.UUID] = None
    
    # Auditoría
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    version_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class ProductReadWithVersions(ProductRead):
    versions: List[ProductVersionRead] = []

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Nombre del producto")
    sku: str = Field(..., min_length=1, description="SKU único por empresa")
    description: Optional[str] = None
    product_type: ProductType
    uom_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    group_id: Optional[uuid.UUID] = None