import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from common.models import MultiTenantBase, AuditBase
from app.core.enums import SubscriptionStatus, ModuleCode

class Module(AuditBase):
    """Catálogo global de módulos disponibles en el sistema."""
    __tablename__ = "modules"

    code: Mapped[ModuleCode] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(255))
    is_core: Mapped[bool] = mapped_column(Boolean, default=False)
    translation_key: Mapped[Optional[str]] = mapped_column(String(100))

class Plan(AuditBase):
    """Definición de paquetes de suscripción (Basic, Pro, etc.)."""
    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    trial_days: Mapped[int] = mapped_column(Integer, default=14)
    
    # Relación con módulos incluidos en el plan
    # (Podríamos usar una tabla intermedia si un plan tiene muchos módulos)
    modules: Mapped[List[str]] = mapped_column(JSONB, default=list)

class Subscription(MultiTenantBase):
    """Estado de suscripción por empresa (Tenant)."""
    __tablename__ = "subscriptions"

    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plans.id"))
    status: Mapped[SubscriptionStatus] = mapped_column(
        String(20), default=SubscriptionStatus.TRIAL
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    grace_period_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relación con el plan
    plan = relationship("Plan")

class Entitlement(MultiTenantBase):
    """Tabla de verdad para el acceso efectivo a módulos por company_id."""
    __tablename__ = "entitlements"

    module_code: Mapped[ModuleCode] = mapped_column(String(50), index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source_subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("subscriptions.id"), nullable=True
    )

class AuditSubscriptionLog(MultiTenantBase):
    """Registro inmutable de cambios de estado en suscripciones."""
    __tablename__ = "audit_subscription_logs"

    subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscriptions.id"))
    event_type: Mapped[str] = mapped_column(String(50)) # STATUS_CHANGE, PLAN_UPGRADE, etc.
    before_state: Mapped[dict] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict] = mapped_column(JSONB, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255))
