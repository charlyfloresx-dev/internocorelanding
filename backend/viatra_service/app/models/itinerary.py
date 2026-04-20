import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.models import MultiTenantBase, AuditBase

class ItineraryItem(MultiTenantBase):
    __tablename__ = "viatra_itinerary_items"

    package_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("viatra_travel_packages.id"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Enum-like: FLIGHT, HOTEL, ACTIVITY, TRANSPORT
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    start_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Metadata for Sentinel Bots (e.g. flight number)
    provider_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
