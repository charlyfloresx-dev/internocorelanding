import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from common.domain import ProductType, ProductStatus, VersionStatus
from master_app.schemas.product_scan_pattern import ScanPatternRead

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
    base_uom_id: Optional[uuid.UUID] = None
    group_id: Optional[uuid.UUID] = None
    
    # Auditoría
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    version_id: int
    is_active: bool
    
    # Media Assets (Phase 44)
    photo_path: Optional[str] = None
    product_url: Optional[str] = None # Virtual field for frontend
    
    # Financial Metadata (Phase 33.5)
    last_price: Optional[Decimal] = None
    currency: Optional[str] = None
    
    # Enriched Fields for Barcode / POS Lookup
    brand_name: Optional[str] = None
    category_name: Optional[str] = None
    uom_name: Optional[str] = None
    current_stock: Optional[Decimal] = None

    # Per-item scan validation patterns (Phase 152)
    scan_patterns: List[ScanPatternRead] = []

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
    brand_id: Optional[uuid.UUID] = None
    group_id: Optional[uuid.UUID] = None
    # Physical tracking
    requires_batch: bool = False
    requires_expiration: bool = False
    # Fiscal compliance (Phase 33.5)
    sat_product_code: Optional[str] = Field(None, max_length=20)
    hts_code: Optional[str] = Field(None, max_length=20)
    is_taxable: bool = True
    allow_price_override: bool = True
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    product_type: Optional[ProductType] = None
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    status: Optional[ProductStatus] = None
    is_active: Optional[bool] = None
    photo_path: Optional[str] = None
    # Physical
    requires_batch: Optional[bool] = None
    requires_expiration: Optional[bool] = None
    # Fiscal
    sat_product_code: Optional[str] = Field(None, max_length=20)
    hts_code: Optional[str] = Field(None, max_length=20)
    is_taxable: Optional[bool] = None
    allow_price_override: Optional[bool] = None


# ── Bulk Import (Onboarding Wizard Phase 168) ────────────────────────────────

class ProductBulkItem(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=250)
    description: Optional[str] = None
    category_tag: Optional[str] = None
    uom_code: str = "PZ"
    unit_price: Optional[Decimal] = None
    currency: str = Field(default="MXN", max_length=3)

class ProductBulkResult(BaseModel):
    created: int = 0
    skipped: int = 0
    errors: List[str] = []
