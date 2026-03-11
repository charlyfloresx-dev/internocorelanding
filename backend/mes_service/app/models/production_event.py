import uuid
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ProductionEventType
from common.models import MultiTenantBase

class ProductionEvent(MultiTenantBase):
    __tablename__ = "mes_production_events"

    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resources.id"), nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_work_orders.id"), nullable=False, index=True)
    event_type: Mapped[ProductionEventType] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    reason_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    def __repr__(self):
        return f"<ProductionEvent(id={self.id}, resource={self.resource_id}, event={self.event_type})>"
