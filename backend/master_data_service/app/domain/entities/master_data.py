import uuid
from typing import List, Optional
from pydantic import BaseModel


class ProductEntity(BaseModel):
    """Pure domain entity for a Product."""
    id: Optional[uuid.UUID] = None
    company_id: uuid.UUID
    group_id: Optional[uuid.UUID] = None
    sku: str
    name: str
    description: Optional[str] = None
    product_type: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None


class ProductVersionEntity(BaseModel):
    """Pure domain entity for a Product Version."""
    id: Optional[uuid.UUID] = None
    company_id: uuid.UUID
    product_id: uuid.UUID
    version_number: int
    um_id: Optional[uuid.UUID] = None
    version_status: Optional[str] = None
    is_active: bool = False
    is_validated: bool = False
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None


class BrandEntity(BaseModel):
    """Pure domain entity for a Product Brand."""
    id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None


class CategoryEntity(BaseModel):
    """Pure domain entity for a Product Category."""
    id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None


class UOMEntity(BaseModel):
    """Pure domain entity for a Unit of Measure."""
    id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None
    name: str
    abbreviation: Optional[str] = None
