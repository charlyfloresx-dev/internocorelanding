import uuid
from typing import Optional
from sqlalchemy import String, UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase

class HrTenantConfig(MultiTenantBase):
    """
    Tenant-specific HR rules.
    Used to enforce custom validations per company.
    """
    __tablename__ = "hr_tenant_configs"

    # Regex pattern to validate employee ID (internal_id)
    # Example: ^[0-9]{6}[A-Z]$ for 123456A
    internal_id_pattern: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Custom message to show when validation fails
    pattern_error_message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
