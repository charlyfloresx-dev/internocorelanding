import uuid
from typing import Optional
from sqlalchemy import String, Boolean, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase
from ..enums import WarehouseType, MovementType, ProductStatus

class BaseCatalogEntity(MultiTenantBase):
    """
    Abstract base for entities that act as Reference/Master data.
    Provides standard code and name fields.
    """
    __abstract__ = True

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class BaseWarehouse(BaseCatalogEntity):
    """
    Base definition for a Warehouse/Location.
    Used by MasterData, Inventory, and WMS.
    """
    __abstract__ = True

    type: Mapped[WarehouseType] = mapped_column(
        Enum(WarehouseType),
        default=WarehouseType.PHYSICAL,
        nullable=False
    )
    country_code: Mapped[str] = mapped_column(String(2), default="MX", nullable=False)

class BaseProduct(BaseCatalogEntity):
    """
    Base definition for an Item/Product.
    Note: 'sku' is often used as the 'code'.
    """
    __abstract__ = True

    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus),
        default=ProductStatus.DRAFT,
        nullable=False
    )
    
    photo_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Standard compliance (optional at base level)
    sat_product_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

class BaseMovementConcept(BaseCatalogEntity):
    """
    Base definition for Movement Reasons (Concepts).
    """
    __abstract__ = True

    type: Mapped[MovementType] = mapped_column(
        Enum(MovementType),
        nullable=False
    )
