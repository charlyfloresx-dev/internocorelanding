from pydantic import BaseModel, Field, validator
from uuid import UUID

from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class InventoryMovementBase(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    quantity: Decimal = Field(..., gt=0, description="Cantidad física del movimiento")
    # Price-Ready: Precios transaccionales obligatorios
    unit_price: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="USD", max_length=3)

class InventoryMovementCreate(InventoryMovementBase):
    pass

# class InventoryMovementRead(InventoryMovementBase):
#    id: UUID4
#    
#    class Config:
#        from_attributes = True

class InventoryDocumentBase(BaseModel):
    concept_code: str = Field(..., description="Código del concepto (ej: ENT, SAL)")
    description: Optional[str] = None
    reference: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)

class InventoryDocumentCreate(InventoryDocumentBase):
    movements: List[InventoryMovementCreate]

# class InventoryDocumentRead(InventoryDocumentBase):
#    id: UUID4
#    company_id: UUID4
#    status: str
#    
#    # 🛡️ Identidad Triple
#    sequence_number: int = Field(..., description="ID secuencial interno por empresa")
#    folio: str = Field(..., description="Folio comercial (ej: MEX-ENT-001)")
#    
#    # Auditoría
#    created_by: Optional[UUID4]
#    created_at: datetime
#    confirmed_at: Optional[datetime]
#    confirmed_by: Optional[UUID4]
#    
#    # Relaciones
#    movements: List[InventoryMovementRead] = []
#    total_amount: Decimal = Field(default=0, description="Suma total valorizada (informativo)")
#
#    class Config:
#        from_attributes = True