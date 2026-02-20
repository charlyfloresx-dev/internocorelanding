from pydantic import BaseModel, Field, condecimal
from typing import Optional
from wms_service.app.models import InventoryDocumentStatus

class CreateInventoryDocumentCommand(BaseModel):
    folio: str
    warehouse_id: str
    concept_id: str
    
class AddMovementCommand(BaseModel):
    document_id: str
    product_id: str
    warehouse_id: str
    quantity: condecimal(gt=0, decimal_places=2)
    unit_cost: condecimal(ge=0, decimal_places=2)

class ConfirmDocumentCommand(BaseModel):
    document_id: str
