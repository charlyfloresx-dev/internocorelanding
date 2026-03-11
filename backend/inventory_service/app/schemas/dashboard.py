from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import List, Optional
import uuid

class StockDashboardRow(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    # Physical Location Fields
    total_quantity: Decimal
    reserved_quantity: Decimal
    # Computed dynamically at Query Level to ensure SSOT
    available_quantity: Decimal 
    
    # Virtual Transfer State (Transit computed dynamically from sibling transit warehouse)
    in_transit_quantity: Decimal = Decimal("0.0")

    model_config = ConfigDict(from_attributes=True)

class ForceReleaseCmd(BaseModel):
    warehouse_id: uuid.UUID
    product_id: uuid.UUID
    release_qty: Decimal
