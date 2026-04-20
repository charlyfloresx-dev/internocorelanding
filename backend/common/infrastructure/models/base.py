import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Boolean, Integer, UUID, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr

class Base(DeclarativeBase):
    """Base declarativa para todos los modelos de SQLAlchemy."""
    pass

class BaseDomainEntity(Base):
    """
    Entidad raíz del dominio.
    Incluye:
    - ID (UUIDv4)
    - Soft Delete (is_active)
    - Optimistic Locking (version_id)
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 🔐 Optimistic Locking
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    __mapper_args__ = {
        "version_id_col": version_id
    }

class AuditBase(BaseDomainEntity):
    """
    Añade campos de auditoría estándar.
    """
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        onupdate=func.now(), 
        nullable=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

class MultiTenantBase(AuditBase):
    """
    Clase base para entidades que pertenecen a un Tenant específico.
    Fuerza la existencia de company_id sin acoplamiento de FK.
    """
    __abstract__ = True

    @declared_attr
    def company_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    @declared_attr
    def tenant_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    @declared_attr
    def group_id(cls) -> Mapped[Optional[uuid.UUID]]:
        return mapped_column(UUID(as_uuid=True), nullable=True, index=True)
