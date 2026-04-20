import uuid
from decimal import Decimal
from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.domain.entities.inventory_item import (
    StockAlertEntity, 
    HourlyMovementEntity, 
    KardexRowEntity
)

# --- Legacy Dashboard Schemas (Restored to fix ImportErrors) ---

class StockDashboardRow(BaseModel):
    product_id: Union[uuid.UUID, str]
    sku: str
    name: str = "Unspecified"
    quantity: Decimal
    reserved: Decimal
    available: Decimal
    uom: str = "PZA"
    
    model_config = ConfigDict(from_attributes=True)

class ForceReleaseCmd(BaseModel):
    warehouse_id: Union[uuid.UUID, str]
    product_id: Union[uuid.UUID, str]
    release_qty: Decimal

class InventorySummary(BaseModel):
    entries_24h: int
    outputs_24h: int
    transfers_24h: int
    pending_docs: int

class MovementDocumentRow(BaseModel):
    id: Union[uuid.UUID, str]
    folio: str
    date: str
    type: str
    origin: str
    destination: str
    items_count: int
    total_weight: Decimal = Decimal("0.0")
    status: str
    external_reference: Optional[str] = None
    validation_status: Optional[str] = "CLEAN"

class KardexRow(BaseModel):
    movement_id: Union[uuid.UUID, str]
    date: str
    document_folio: str
    movement_type: str
    quantity_delta: Decimal
    running_balance: Decimal
    uom_symbol: str = "PZA"

class WACValuationRow(BaseModel):
    product_id: Union[uuid.UUID, str]
    total_units: Decimal
    weighted_average_cost: Decimal
    total_inventory_value: Decimal
    currency_code: str = "USD"

class ABCRotationRow(BaseModel):
    product_id: Union[uuid.UUID, str]
    current_stock: Decimal
    exits_30d: Decimal
    rotation_index_30d: Decimal
    abc_class: str

# --- New Mission Control Dashboard Schemas (Phase 30) ---

class ValuationSummary(BaseModel):
    total_usd: Decimal
    variation_percentage: Decimal = Field(default=Decimal("0.0"))
    stock_yesterday: Decimal
    current_total_stock: Decimal = Field(default=Decimal("0.0"))

class DashboardDTO(BaseModel):
    valuation: ValuationSummary
    critical_alerts: List[StockAlertEntity]
    movement_series: List[HourlyMovementEntity]
    recent_activity: List[KardexRowEntity]
    meta: dict = Field(default_factory=dict)
