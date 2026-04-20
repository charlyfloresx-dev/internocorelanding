import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.models import MultiTenantBase, AuditBase

class TravelerGroup(MultiTenantBase):
    __tablename__ = "viatra_traveler_groups"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("viatra_travel_packages.id"), nullable=False)
    leader_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Sentinel Monitoring Assets
    flight_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, info={"description": "Vuelo principal del grupo para SkySentinel"})
    
    # Financial Hygiene (Stripe Lifecycle)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", info={"description": "Estatus del grupo: PENDING, PAID, GRACE_PERIOD, CANCELLED"})
    grace_period_until: Mapped[Optional[datetime]] = mapped_column(info={"description": "Fecha límite de rescate financiero"})

