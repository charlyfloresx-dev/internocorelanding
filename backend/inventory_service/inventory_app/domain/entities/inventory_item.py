from datetime import datetime
from uuid import UUID
from typing import Optional, List, Union
from decimal import Decimal
from pydantic import BaseModel, Field
import enum
from common.domain.value_objects import Money

class TransactionType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    BACKFLUSHING = "BACKFLUSHING"

class InventoryLevelEntity(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    uom_id: UUID
    quantity: Decimal
    reserved_quantity: Decimal
    wac: Money = Field(default_factory=lambda: Money(Decimal("0.0"), "USD"))
    last_price: Money = Field(default_factory=lambda: Money(Decimal("0.0"), "USD"))
    replacement_price: Money = Field(default_factory=lambda: Money(Decimal("0.0"), "USD"))
    company_id: UUID

class InventoryTransactionEntity(BaseModel):
    id: UUID
    product_id: UUID
    warehouse_id: UUID
    transaction_type: TransactionType
    quantity_change: Decimal
    previous_balance: Decimal
    new_balance: Decimal
    reference_id: Optional[UUID] = None
    comments: Optional[str] = None
    company_id: UUID

class InventoryLineEntity(BaseModel):
    product_id: UUID
    quantity: Decimal
    warehouse_id: UUID
    uom_id: Optional[UUID] = None # Or inferred

class InventoryDocumentEntity(BaseModel):
    id: UUID
    document_type: str
    status: str
    movement_type: TransactionType
    lines: List[InventoryLineEntity]
    company_id: UUID

class MovementEntity(BaseModel):
    id: Union[UUID, str]
    warehouse_id: Union[UUID, str]
    product_id: Union[UUID, str]
    company_id: Union[UUID, str]
    quantity: Decimal
    uom_id: Union[UUID, str]
    weight: Decimal
    price: Money = Field(default_factory=lambda: Money(Decimal("0.0"), "MXN"))
    movement_type: str
    document_type: str
    document_id: Union[UUID, str]
    concept_id: Optional[Union[UUID, str]] = None
    location: Optional[str] = None
    user_id: Optional[Union[UUID, str]] = None
    
    # FIFO & Compliance (Anexo 24)
    available_quantity: Decimal = Field(default=Decimal("0.0"))
    customs_pedimento_id: Optional[UUID] = None
    source_movement_id: Optional[UUID] = None
    expiry_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    # Fast-Track Validation (Phase 61)
    validation_status: str = "CLEAN" # PENDING, CLEAN, OVERFLOW_ALERT

class MovementSummaryEntity(BaseModel):
    entries_24h: int
    outputs_24h: int
    transfers_24h: int
    pending_docs: int

class DocumentListRowEntity(BaseModel):
    id: UUID
    folio: str
    date: str
    type: str # ENTRY, EXIT, TRANSFER
    origin: str
    destination: str
    items_count: int
    total_weight: Optional[Decimal] = None
    status: str # DRAFT, PROCESSED, CANCELLED
    trace_id: Optional[str] = None  # Correlation ID for forensic view
    external_reference: Optional[str] = None
    validation_status: Optional[str] = "CLEAN"

# ─── Report Entities ──────────────────────────────────────────────────────────

class KardexRowEntity(BaseModel):
    """Running balance row for a single SKU in a warehouse (Kardex)."""
    movement_id: UUID
    date: str
    document_folio: str
    movement_type: str           # IN / OUT / TRANSFER
    quantity_delta: Decimal      # Signed: positive=entry, negative=exit
    uom_id: UUID
    weight: Decimal
    price: Money
    running_balance: Decimal     # Cumulative balance from Window Function
    company_id: UUID
    validation_status: Optional[str] = "CLEAN"

class WACValuationEntity(BaseModel):
    """Weighted Average Cost valuation snapshot for a product/warehouse."""
    product_id: UUID
    warehouse_id: UUID
    as_of_date: str
    total_units: Decimal
    wac: Money
    total_inventory_value: Money  # total_units * WAC
    company_id: UUID

class RotationABCEntity(BaseModel):
    """ABC rotation metric: compares exit volume vs current stock."""
    product_id: UUID
    warehouse_id: UUID
    current_stock: Decimal
    exits_30d: Decimal
    exits_90d: Decimal
    rotation_index_30d: Decimal   # exits_30d / (current_stock + 0.0001)
    abc_class: str                # A / B / C
    company_id: UUID
class InventorySearchRowEntity(BaseModel):
    """Result row for the new real-time SKU search (Phase 29)."""
    id: UUID                      # ItemVariant ID
    sku: str                      # internal_sku
    name: str                     # From variation attributes
    current_stock: Decimal
    uom_id: UUID
    uom_symbol: str = "PZA"        # Fallback for demo
    abc_class: str = "C"           # Default to C, calculated in repo
    company_id: UUID
class StockAlertEntity(BaseModel):
    product_id: UUID
    sku: str
    name: Optional[str] = None
    current_quantity: Decimal
    min_quantity: Decimal = Decimal("0.0")
    warehouse_id: Optional[UUID] = None
    status: str = "NORMAL" # NORMAL, LOW, CRITICAL

class HourlyMovementEntity(BaseModel):
    hour: datetime
    entries: Decimal = Decimal("0.0")
    exits: Decimal = Decimal("0.0")

class DashboardTelemetryEntity(BaseModel):
    valuation_total: Decimal
    critical_alerts_count: int
    alerts: List[StockAlertEntity]
    hourly_series: List[HourlyMovementEntity]
    recent_movements: List[KardexRowEntity] = Field(default_factory=list)
class DocumentItemEntity(BaseModel):
    product_id: UUID
    sku: str
    name: Optional[str] = "Item"
    quantity: Decimal
    uom_id: UUID
    uom_name: Optional[str] = "PZA"
    weight: Decimal
    unit_price: Decimal = Decimal("0.0")
    location: Optional[str] = None
    validation_status: Optional[str] = "CLEAN"

class DocumentDetailEntity(BaseModel):
    id: UUID
    folio: str
    date: str
    type: str
    status: str
    origin: str
    destination: str
    items_count: int
    total_weight: Decimal
    concept_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    notes: Optional[str] = None
    items: List[DocumentItemEntity]
