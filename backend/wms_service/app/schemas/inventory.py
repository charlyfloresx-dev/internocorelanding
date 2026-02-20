import uuid
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# --- Master Data Sync Schemas ---

class ProductVersionSyncData(BaseModel):
    version_number: int

class ProductSyncData(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    versions: List[ProductVersionSyncData]

class MasterDataSyncPayload(BaseModel):
    products: List[ProductSyncData]

class SyncResult(BaseModel):
    processed: int
    created: int
    updated: int

# --- WMS Core Schemas ---

class InventoryMovementBase(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="USD", max_length=3)

class InventoryMovementCreate(InventoryMovementBase):
    pass

class InventoryMovementRead(InventoryMovementBase):
    id: uuid.UUID
    
    class Config:
        from_attributes = True

class InventoryDocumentBase(BaseModel):
    concept_code: str = Field(..., description="Código del concepto (ej: ENT, SAL)")
    description: Optional[str] = None
    reference: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)

class InventoryDocumentCreate(InventoryDocumentBase):
    movements: List[InventoryMovementCreate]

class InventoryDocumentRead(InventoryDocumentBase):
    id: uuid.UUID
    company_id: uuid.UUID
    status: str
    sequence_number: int
    folio: str
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[uuid.UUID] = None
    movements: List[InventoryMovementRead] = []
    total_amount: Decimal = Field(default=0)

    class Config:
        from_attributes = True

# --- Stock & Snapshot Schemas (El que faltaba) ---

class InventorySnapshotRead(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity_on_hand: Decimal
    
    class Config:
        from_attributes = True

# --- Catalog Schemas ---

class WarehouseCreate(BaseModel):
    code: str
    name: str

class WarehouseRead(WarehouseCreate):
    id: uuid.UUID
    company_id: uuid.UUID

class ConceptCreate(BaseModel):
    code: str
    name: str

class ConceptRead(ConceptCreate):
    id: uuid.UUID