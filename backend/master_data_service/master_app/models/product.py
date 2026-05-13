from decimal import Decimal
import uuid
from sqlalchemy import String, Text, ForeignKey, Integer, UniqueConstraint, Boolean, Numeric, JSON, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from common.models import MultiTenantBase
from common.enums import ProductType, ProductStatus, VersionStatus

if TYPE_CHECKING:
    from master_app.models.product_price import ProductPrice

from common.models import BaseProduct

class Product(BaseProduct):
    __tablename__ = "products"

    code: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True) # Legacy Code
    
    # Flags de Control Forense
    requires_batch: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_expiration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Cumplimiento Fiscal (Phase 33.5) ─────────────────────────────────────────
    # hts_code: Código arancelario US de 10 dígitos (ej. 1601.00.4000)
    # is_taxable: Flag para calcular IVA/Sales Tax al final del movimiento
    # allow_price_override: Permite al usuario editar el precio en la transacción
    hts_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=False)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_price_override: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Parámetros de Control de Inventario (Legacy Migration) ───────────────────
    # Alineados con MinOrderQty / MaxOrderQty / SafetyStock del código legacy C#
    min_order_qty: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=0.0, server_default=text('0'), nullable=False)
    max_order_qty: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=0.0, server_default=text('0'), nullable=False)
    safety_stock: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=0.0, server_default=text('0'), nullable=False)

    # ── Relaciones de Precios ─────────────────────────────────────────────────────
    prices: Mapped[List["ProductPrice"]] = relationship(
        "ProductPrice", back_populates="product", cascade="all, delete-orphan", lazy="select"
    )

    # Atributos Físicos (Master Data Level)
    base_uom_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("uoms.id"), nullable=True)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    dimensions_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    product_type: Mapped[ProductType] = mapped_column(
        postgresql.ENUM(ProductType, name="producttype", create_type=True),
        nullable=False
    )

    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("product_brands.id"), nullable=True)
    
    category: Mapped[Optional["ProductCategory"]] = relationship("ProductCategory")
    brand: Mapped[Optional["ProductBrand"]] = relationship("ProductBrand")
    
    versions: Mapped[List["ProductVersion"]] = relationship("ProductVersion", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('sku', 'company_id', name='_company_sku_uc'),
        UniqueConstraint('code', 'company_id', name='_company_code_uc'),
    )
    
    
    # Enable Standard Optimistic Locking (version_id in MultiTenantBase)

class ProductVersion(MultiTenantBase):
    __tablename__ = "product_versions"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    product: Mapped["Product"] = relationship("Product", back_populates="versions")
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_status: Mapped[VersionStatus] = mapped_column(
        postgresql.ENUM(VersionStatus, name="versionstatus", create_type=True),
        default=VersionStatus.DESIGN,
        nullable=False
    )
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
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
