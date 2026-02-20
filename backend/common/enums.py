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
    # Ciclo de Vida de Ingeniería y Diseño
    DESIGN = "DESIGN"             # Etapa inicial de dibujo/especificación
    EXPERIMENTAL = "EXPERIMENTAL" # Prototipos y pruebas técnicas
    UNDER_REVIEW = "UNDER_REVIEW" # En proceso de validación/QA
    PUBLISHED = "PUBLISHED"       # Versión oficial para producción/ventas
    DEPRECATED = "DEPRECATED"     # Versión antigua, se mantiene por stock pero no se fabrica
    ARCHIVED = "ARCHIVED"         # Fuera de uso total
    DRAFT = "DRAFT"               # Borrador inicial

class ProductType(str, Enum):
    GOODS = "GOODS"
    SERVICE = "SERVICE"

class CurrencyType(str, Enum):
    USD = "USD"
    MXN = "MXN"
    EUR = "EUR"

# --- Agregados desde Interno.Domain.Enum (.NET) ---

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