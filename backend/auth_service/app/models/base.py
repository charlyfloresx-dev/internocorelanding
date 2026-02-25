import uuid
from sqlalchemy import Column, DateTime, ForeignKey, func, Integer # Add Integer for clarity
# from sqlalchemy.dialects.postgresql import UUID as PG_UUID # Removed as AgnosticUUID is removed
# from sqlalchemy.types import TypeDecorator, CHAR # Removed as AgnosticUUID is removed
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.orm import DeclarativeBase
# Removed AgnosticUUID as it's no longer used for default IDs

class CustomBase:
    """Base class for all models, provides common auditable fields."""
    # Removed id = Column(AgnosticUUID, primary_key=True, default=uuid.uuid4)
    # Models will define their own ID explicitly (e.g., Column(Integer, ...))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Base(DeclarativeBase, CustomBase):
    pass

# Removed TenantBase as it was causing direct type clashes with Integer company_id/IDs
# It can be re-introduced when UUID migration is fully planned.
