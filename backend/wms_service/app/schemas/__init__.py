# backend/wms_service/app/schemas/__init__.py

from .inventory import (
    InventoryDocumentCreate,
    InventoryDocumentRead,
    InventoryMovementCreate,
    InventorySnapshotRead,
    WarehouseCreate,
    WarehouseRead,
    ConceptCreate,    # <--- Agregado para resolver el último error
    ConceptRead       # <--- Agregado para visualización en respuestas
)

# Alias para compatibilidad con el router de inventory.py
InventoryDocumentResponse = InventoryDocumentRead

__all__ = [
    "InventoryDocumentCreate",
    "InventoryDocumentRead",
    "InventoryDocumentResponse",
    "InventoryMovementCreate",
    "InventorySnapshotRead",
    "WarehouseCreate",
    "WarehouseRead",
    "ConceptCreate",
    "ConceptRead"
]