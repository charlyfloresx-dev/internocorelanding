from enum import Enum

class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"

class CompanyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DELINQUENT = "DELINQUENT"

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

class CurrencyType(str, Enum):
    USD = "USD"
    MXN = "MXN"
    EUR = "EUR"

class PartnerType(str, Enum):
    CUSTOMER = "CUSTOMER"
    SUPPLIER = "SUPPLIER"
    BOTH = "BOTH"

# --- Added from Interno.Domain.Enum (.NET) ---

class AddressType(str, Enum):
    Home = "Home"
    Work = "Work"
    Mobile = "Mobile"
    Fax = "Fax"
    Other = "Other"

class PriorityLevel(str, Enum):
    Minor = "Minor"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"

class StatusType(str, Enum):
    StandBy = "StandBy"
    Released = "Released"
    Received = "Received"
    InProgress = "InProgress"
    InPart = "InPart"
    Complete = "Complete"
    Rejected = "Rejected"
    Canceled = "Canceled"
    Damaged = "Damaged"
    Closed = "Closed"

class MovementType(str, Enum):
    ENTRY = "ENTRY"
    OUTPUT = "OUTPUT"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"

class WarehouseType(str, Enum):
    PHYSICAL = "PHYSICAL"
    VIRTUAL = "VIRTUAL"
    TRANSIT = "TRANSIT"
    RESOURCE = "RESOURCE"  # Machine/station acting as WIP warehouse
    EXT_PARTNER = "EXT_PARTNER" # Customer/Supplier managed location

class PaymentMethod(str, Enum):
    CASH = "CASH"
    CARD = "CARD"
    TRANSFER = "TRANSFER"
    STRIPE = "STRIPE"
    WALLET = "WALLET"