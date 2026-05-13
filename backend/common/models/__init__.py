from common.infrastructure.models.base import Base, BaseDomainEntity, AuditBase, MultiTenantBase
BaseEntity = BaseDomainEntity
from common.models.user_context import UserContext
from common.models.business_group import BusinessGroup
from common.models.company import Company
from common.models.audit import AuditLog
from common.models.idempotency_key import IdempotencyKey
from common.repository import BaseRepository
from common.models.file_metadata import FileMetadata
from common.models.catalogs import BaseProduct, BaseWarehouse, BaseMovementConcept
from common.models.location import InventoryLocation
from common.models.location import ZoneType, StorageType
from common.models.work_order_base import (
    WorkOrderBase,
    WorkOrderType,
    WorkOrderBaseStatus,
    WorkOrderBasePriority,
)
from common.models.enumeration import Enumeration
from common.models.security_audit_log import SecurityAuditLog
# from common.models.external_contact import ExternalContact

__all__ = [
    "Base", 
    "BaseDomainEntity", 
    "AuditBase", 
    "MultiTenantBase", 
    "UserContext", 
    "BusinessGroup", 
    "Company", 
    "AuditLog", 
    "BaseRepository", 
    "FileMetadata",
    "IdempotencyKey",
    "BaseProduct", 
    "BaseWarehouse", 
    "BaseMovementConcept",
    "InventoryLocation",
    "ZoneType",
    "StorageType",
    # DDD Shared Kernel — Work Orders
    "WorkOrderBase",
    "WorkOrderType",
    "WorkOrderBaseStatus",
    "WorkOrderBasePriority",
    # Catalogs / Lookups
    "Enumeration",
    "SecurityAuditLog",
    # Providers
    # "ExternalContact",
]