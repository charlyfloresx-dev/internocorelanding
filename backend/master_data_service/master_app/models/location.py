from common.models.location import InventoryLocation, ZoneType, StorageType

# [Phase 84] Alias for backwards compatibility in the Monolith
# The master definition now lives in common.models.location
__all__ = ["InventoryLocation", "ZoneType", "StorageType"]
