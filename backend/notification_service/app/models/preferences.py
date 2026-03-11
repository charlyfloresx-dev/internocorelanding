from sqlalchemy import String, Boolean, UUID as sqlalchemy_UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase
import uuid

class UserPreferences(MultiTenantBase):
    __tablename__ = "user_notification_preferences"

    # A single user can have multiple preferences per tenant
    user_id: Mapped[uuid.UUID] = mapped_column(sqlalchemy_UUID(as_uuid=True), index=True)
    
    receive_in_app: Mapped[bool] = mapped_column(Boolean, default=True)
    receive_email: Mapped[bool] = mapped_column(Boolean, default=True)
    receive_push: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Optional webhook URL for advanced integrations per user/tenant
    webhook_url: Mapped[str] = mapped_column(String(255), nullable=True)
