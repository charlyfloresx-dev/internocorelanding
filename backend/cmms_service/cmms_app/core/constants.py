import enum


# ─────────────────────────────────────────────
# ASSET ENUMS
# ─────────────────────────────────────────────

class AssetCategory(str, enum.Enum):
    MACHINERY = "MACHINERY"
    VEHICLE = "VEHICLE"
    FACILITY = "FACILITY"
    IT_EQUIPMENT = "IT_EQUIPMENT"
    TOOLING = "TOOLING"
    OTHER = "OTHER"


class AssetCriticality(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    MISSION_CRITICAL = "MISSION_CRITICAL"


class AssetStatus(str, enum.Enum):
    OPERATIONAL = "OPERATIONAL"
    DOWN = "DOWN"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    RETIRED = "RETIRED"
    STANDBY = "STANDBY"


# ─────────────────────────────────────────────
# TOOL ENUMS
# ─────────────────────────────────────────────

class ToolStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    IN_MAINTENANCE = "IN_MAINTENANCE"
    DAMAGED = "DAMAGED"
    RETIRED = "RETIRED"


class ToolCondition(str, enum.Enum):
    NEW = "NEW"
    GOOD = "GOOD"
    FAIR = "FAIR"
    DAMAGED = "DAMAGED"


# ─────────────────────────────────────────────
# MAINTENANCE ENUMS
# ─────────────────────────────────────────────

class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    PREDICTIVE = "PREDICTIVE"
    CONDITION_BASED = "CONDITION_BASED"


class MaintenanceFrequencyUnit(str, enum.Enum):
    DAYS = "DAYS"
    HOURS = "HOURS"
    CYCLES = "CYCLES"
    KILOMETERS = "KILOMETERS"





# ─────────────────────────────────────────────
# STORAGE / BILLING ENUMS
# ─────────────────────────────────────────────

class StorageTier(str, enum.Enum):
    BASIC = "BASIC"       # 2 GB included
    INDUSTRIAL = "INDUSTRIAL"  # 20 GB included
    ENTERPRISE = "ENTERPRISE"  # 100 GB included


class QuotaApprovalStatus(str, enum.Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


# ─────────────────────────────────────────────
# TRANSFER ENUMS
# ─────────────────────────────────────────────

class TransferType(str, enum.Enum):
    PERMANENT = "PERMANENT"
    TEMPORARY = "TEMPORARY"
