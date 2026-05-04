"""
CMMS Models — un archivo por entidad para máxima localización.

Import order matters for SQLAlchemy relationship resolution:
  1. Asset (padre de jerarquía)
  2. AssetTransferHistory
  3. MaintenancePlan
  4. WorkOrder
  5. Tool
  6. ToolAssignment
  7. MaintenanceEvidence
  8. StorageQuota (sin relaciones externas)
"""
from .asset import Asset
from .asset_transfer_history import AssetTransferHistory
from .maintenance_plan import MaintenancePlan
from .work_order import MaintenanceWorkOrder
from .tool import Tool
from .tool_assignment import ToolAssignment
from .maintenance_evidence import MaintenanceEvidence
from .storage_quota import StorageQuota

__all__ = [
    "Asset",
    "AssetTransferHistory",
    "MaintenancePlan",
    "MaintenanceWorkOrder",
    "Tool",
    "ToolAssignment",
    "MaintenanceEvidence",
    "StorageQuota",
]

