import uuid
from datetime import datetime
from sqlalchemy import (
    String, Text, ForeignKey, Integer, UniqueConstraint, 
    Enum, Boolean, Numeric, DateTime, JSON, UUID
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
# JSONB solo se usa si es estrictamente necesario, para compatibilidad cruzada usamos JSON

from common.domain import MultiTenantBase
from common.domain import ProductStatus, VersionStatus, ProductType

class Product(MultiTenantBase):
    __tablename__ = "products"

    # En Clean Architecture, el sku debe ser unico por empresa (multitenancy)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    product_type: Mapped[ProductType] = mapped_column(Enum(ProductType), nullable=False)
    
    # Estatus del Producto (activo comercialmente o no)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus), 
        default=ProductStatus.DRAFT, 
        nullable=False
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("product_categories.id"), 
        nullable=True
    )
    category = relationship("ProductCategory")

    versions: Mapped[list["ProductVersion"]] = relationship(
        "ProductVersion", 
        back_populates="product", 
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint('sku', 'company_id', name='_company_sku_uc'),
    )

class ProductVersion(MultiTenantBase):
    __tablename__ = "product_versions"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("products.id"), 
        nullable=False
    )
    product = relationship("Product", back_populates="versions")

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Estatus del ciclo de vida de la versión (Ingeniería/Diseño)
    version_status: Mapped[VersionStatus] = mapped_column(
        Enum(VersionStatus), 
        default=VersionStatus.DESIGN, # Inician en diseño
        nullable=False
    )
    
    # Campos técnicos de ingeniería
    weight: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    dimensions: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    um_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("ums.id"), 
        nullable=False
    )
    um = relationship("UM")

    # Auditoría técnica y aprobación
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    change_reason: Mapped[str] = mapped_column(Text, nullable=True) # Por qué cambió
    
    # Link a planos, CAD, PDFs
    technical_specs: Mapped[dict] = mapped_column(JSON, nullable=True) 
    
    # Quién aprueba técnicamente la versión
    approved_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('product_id', 'version_number', name='_product_version_uc'),
    )