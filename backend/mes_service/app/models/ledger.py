import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Numeric, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models.base_models import MultiTenantBase

class ManufacturingLedger(MultiTenantBase):
    """El libro mayor de piezas (Manufacturing Ledger)."""
    __tablename__ = "mes_manufacturing_ledger"

    resource_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resource_results.id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=1.0)
    transaction_type: Mapped[str] = mapped_column(String(20), default="SCAN") # SCAN, ADJ, SCRAP
    external_folio: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=True) # Secuencia por turno/recurso
    local_txn_id: Mapped[Optional[uuid.UUID]] = mapped_column(unique=True, index=True, nullable=True)
    is_synced: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relaciones
    production_result: Mapped["ResourceResult"] = relationship(back_populates="ledger_entries")

class Tracking(MultiTenantBase):
    """Trazabilidad granular (PO/MO/CO/WO) por pieza."""
    __tablename__ = "mes_tracking"

    reference: Mapped[str] = mapped_column(String(100)) # PO/WO/etc
    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resources.id"), nullable=False)
    item_sku: Mapped[str] = mapped_column(String(100))
    
    series: Mapped[Optional[str]] = mapped_column(String(100)) # Lote/Serial
    folio: Mapped[Optional[str]] = mapped_column(String(100))
    
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    responsible: Mapped[Optional[str]] = mapped_column(String(100))
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    close_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)

    @property
    def transcurred_seconds(self) -> float:
        end = self.close_time or datetime.now()
        return (end - self.start_time).total_seconds()
