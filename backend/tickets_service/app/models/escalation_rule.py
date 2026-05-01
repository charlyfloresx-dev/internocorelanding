from sqlalchemy import String, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

class EscalationRule(MultiTenantBase):
    """
    Configuración dinámica de escalación por empresa y área (Fase 7).
    Permite definir quién recibe notificaciones y cuándo, según el nivel de urgencia.
    """
    __tablename__ = "escalation_rules"

    area: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sla_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Optional: notification channel (Email, Push, SMS) as suggested by user
    notification_channel: Mapped[str] = mapped_column(String(20), default="PUSH")

    __table_args__ = (
        UniqueConstraint("company_id", "area", "level", name="uq_company_area_level"),
    )

    def __repr__(self) -> str:
        return f"<EscalationRule(area='{self.area}', level={self.level}, role='{self.role_name}')>"
