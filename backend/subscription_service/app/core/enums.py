from enum import Enum

class SubscriptionStatus(str, Enum):
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"

class ModuleCode(str, Enum):
    AUTH_CORE = "AUTH_CORE"
    INVENTORY_CORE = "INVENTORY_CORE"
    MES_CORE = "MES_CORE"
    WMS_CORE = "WMS_CORE"
