from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from common.domain import MultiTenantBase

class ProductCategory(MultiTenantBase):
    __tablename__ = "product_categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True
    )
    children = relationship("ProductCategory")