from pydantic import BaseModel, Field, condecimal
from typing import Optional

class CreateInventoryDocumentCommand(BaseModel):
    folio: str
    company_id: str
    warehouse_id: str
    concept_id: str
    target_company_id: Optional[str] = None
    target_warehouse_id: Optional[str] = None

class AddMovementCommand(BaseModel):
    document_id: str
    company_id: str
    product_id: str
    warehouse_id: str
    quantity: condecimal(gt=0, decimal_places=2)
    unit_cost: condecimal(ge=0, decimal_places=2)
    location_id: Optional[str] = None

class ConfirmDocumentCommand(BaseModel):
    document_id: str

class CreateSalesOrderCommand(BaseModel):
    folio: str
    product_id: str
    warehouse_id: str
    uom_id: str
    quantity: float = Field(..., gt=0)
    comments: Optional[str] = None

class DispatchSalesOrderCommand(BaseModel):
    sales_order_id: str
    warehouse_id: str # Almacén desde donde se despacha
    location_id: Optional[str] = None # Ubicación física de picking
