import enum
from enum import Enum

class ProductStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISCONTINUED = "DISCONTINUED"

class VersionStatus(str, Enum):
    # Engineering and Design Life Cycle
    DESIGN = "DESIGN"             # Initial drawing/specification stage
    EXPERIMENTAL = "EXPERIMENTAL" # Prototypes and technical testing
    UNDER_REVIEW = "UNDER_REVIEW" # In validation/QA process
    PUBLISHED = "PUBLISHED"       # Official version for production/sales
    DEPRECATED = "DEPRECATED"     # Old version, maintained for stock but not manufactured
    ARCHIVED = "ARCHIVED"         # Out of use entirely
    DRAFT = "DRAFT"               # Initial draft

class ProductType(str, Enum):
    GOODS = "GOODS"
    SERVICE = "SERVICE"

class DocumentStatus(str, enum.Enum):
    """
    Standardizing document lifecycle based on legacy Interno.Domain.Enum.StatusType.
    Ensures 1:1 mapping for migration and cross-service consistency.
    """
    STANDBY = "STANDBY"         # Legacy: 0
    RELEASED = "RELEASED"        # Legacy: 1 (Confirmed/Authorized)
    RECEIVED = "RECEIVED"        # Legacy: 2
    IN_PROGRESS = "IN_PROGRESS"  # Legacy: 3
    IN_PART = "IN_PART"          # Legacy: 4
    COMPLETE = "COMPLETE"        # Legacy: 5
    REJECTED = "REJECTED"        # Legacy: 6
    CANCELED = "CANCELED"        # Legacy: 7
    DAMAGED = "DAMAGED"          # Legacy: 8
    CLOSED = "CLOSED"            # Legacy: 9

class InventoryTransactionType(str, enum.Enum):
    """Unified movement types for all inventory layers."""
    IN = "IN"
    OUT = "OUT"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER = "TRANSFER"
