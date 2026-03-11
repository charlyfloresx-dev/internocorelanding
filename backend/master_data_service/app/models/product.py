import uuid
from sqlalchemy import String, Text, ForeignKey, Integer, UniqueConstraint, Boolean, Numeric, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from common.models import MultiTenantBase
from common.enums import ProductType, ProductStatus, VersionStatus

class Product(MultiTenantBase):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_type: Mapped[ProductType] = mapped_column(
        postgresql.ENUM(ProductType, name="producttype", create_type=False),
        nullable=False
    )
    status: Mapped[ProductStatus] = mapped_column(
        postgresql.ENUM(ProductStatus, name="productstatus", create_type=False),
        default=ProductStatus.DRAFT,
        nullable=False
    )

    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    category: Mapped[Optional["ProductCategory"]] = relationship("ProductCategory")
    versions: Mapped[List["ProductVersion"]] = relationship("ProductVersion", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('sku', 'company_id', name='_company_sku_uc'),
    )
    
    __mapper_args__ = {"version_id_col": None}

class ProductVersion(MultiTenantBase):
    __tablename__ = "product_versions"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    product: Mapped["Product"] = relationship("Product", back_populates="versions")
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_status: Mapped[VersionStatus] = mapped_column(
        postgresql.ENUM(VersionStatus, name="versionstatus", create_type=False),
        default=VersionStatus.DESIGN,
        nullable=False
    )
    weight: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    dimensions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    um_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("uoms.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    technical_specs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) 
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('product_id', 'version_number', name='_product_version_uc'),
    )
    
    __mapper_args__ = {"version_id_col": None}