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
    DESIGN = "DESIGN"
    EXPERIMENTAL = "EXPERIMENTAL"
    UNDER_REVIEW = "UNDER_REVIEW"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"
    DRAFT = "DRAFT"

class ProductType(str, Enum):
    GOODS = "GOODS"
    SERVICE = "SERVICE"

class CurrencyType(str, Enum):
    USD = "USD"
    MXN = "MXN"
    EUR = "EUR"

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
    DRAFT = "DRAFT"
