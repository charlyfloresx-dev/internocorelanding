from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from app.domain.entities.inventory_item import (
    InventoryLevelEntity, 
    InventoryTransactionEntity,
    MovementEntity
)

class IInventoryRepository(ABC):
    @abstractmethod
    async def get_stock(self, warehouse_id: UUID, product_id: UUID, company_id: UUID) -> Optional[InventoryLevelEntity]:
        """Obtiene el stock actual de un producto en un almacén para un tenant."""
        pass

    @abstractmethod
    async def record_movement(self, movement: MovementEntity, allow_negative: bool = False, from_reservation: bool = False) -> InventoryLevelEntity:
        """Registra un movimiento atómicamente y actualiza el balance de stock."""
        pass

    @abstractmethod
    async def reserve_stock(self, warehouse_id: UUID, product_id: UUID, quantity: Decimal, company_id: UUID) -> InventoryLevelEntity:
        """Reserva stock en un almacén. Rechaza si no hay suficiente available_quantity."""
        pass

    @abstractmethod
    async def force_release_orphan(self, warehouse_id: UUID, product_id: UUID, release_qty: Decimal, company_id: UUID) -> InventoryLevelEntity:
        """Libera stock previamente reservado (operación administrativa)."""
        pass

    @abstractmethod
    async def get_dashboard_stock(self, company_id: UUID) -> List[dict]:
        """Resumen de stock para dashboard."""
        pass

    @abstractmethod
    async def find_pending_for_reconciliation(self, max_retries: int = 10) -> List[dict]:
        """Obtiene registros de BackflushError pendientes."""
        pass

    @abstractmethod
    async def update_reconciliation_status(self, error_id: UUID, success: bool, details: Optional[str] = None):
        """Actualiza el estado de conciliación."""
        pass

    @abstractmethod
    async def has_processed_document(self, document_type: str, document_id: UUID, company_id: UUID) -> bool:
        """Verifica si un documento ya fue procesado (Idempotency Check)."""
        pass

    @abstractmethod
    async def get_backflush_error(self, error_id: UUID, company_id: UUID) -> Optional[dict]:
        """Recupera un error de conciliación por ID y Compañía."""
        pass

    @abstractmethod
    async def search_items_and_variants(self, query: str, company_id: UUID, limit: int = 10) -> List[dict]:
        """
        Búsqueda optimizada para Typeahead (SKU, Brand, MPN).
        """
        pass
