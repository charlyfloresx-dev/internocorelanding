import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import BaseEntity

class UserCredential(BaseEntity):
    __tablename__ = "user_credentials"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    email = Column(sa.String(255), unique=True, nullable=False, index=True)
    credential_type = Column(sa.String(50), nullable=False) # 'PASSWORD' or 'WEBAUTHN'
    
    # Password Flow
    hashed_password = Column(sa.String(255), nullable=True)
    
    # WebAuthn Flow
    public_key = Column(postgresql.BYTEA, nullable=True) # Binary storage for public key
    device_fingerprint = Column(sa.String(255), nullable=True)
    
    # Relations
    user: Mapped["User"] = relationship("User", back_populates="credentials")
