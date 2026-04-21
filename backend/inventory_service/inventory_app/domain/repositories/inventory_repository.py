from abc import ABC, abstractmethod
from typing import Optional, List, Any
from uuid import UUID
from decimal import Decimal

from inventory_app.domain.entities.inventory_item import (
    InventoryLevelEntity, 
    InventoryTransactionEntity,
    MovementEntity,
    MovementSummaryEntity,
    DocumentListRowEntity,
    KardexRowEntity,
    WACValuationEntity,
    RotationABCEntity,
    InventorySearchRowEntity,
    DashboardTelemetryEntity,
    StockAlertEntity,
    HourlyMovementEntity,
    DocumentDetailEntity,
    DocumentItemEntity
)

class IInventoryRepository(ABC):
    @abstractmethod
    async def get_stock(self, warehouse_id: UUID, product_id: UUID, company_id: UUID) -> Optional[InventoryLevelEntity]:
        """Obtiene el stock actual de un producto en un almacén para un tenant."""
        pass

    @abstractmethod
    async def record_movement(self, movement: MovementEntity, allow_negative: bool = False, from_reservation: bool = False, client_request_id: Optional[str] = None) -> InventoryLevelEntity:
        """Registra un movimiento atómicamente y actualiza el balance de stock."""
        pass

    @abstractmethod
    async def reserve_stock(self, warehouse_id: UUID, product_id: UUID, quantity: Decimal, company_id: UUID) -> InventoryLevelEntity:
        """Reserva stock en un almacén. Rechaza si no hay suficiente available_quantity."""
        pass

    @abstractmethod
    async def list_warehouses(self, company_id: UUID) -> List[Any]:
        """Obtiene la lista de almacenes de una compañía."""
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

    @abstractmethod
    async def get_inventory_summary(self, company_id: UUID, warehouse_id: Optional[UUID] = None) -> MovementSummaryEntity:
        """Resumen de movimientos de las últimas 24h y pendientes."""
        pass

    @abstractmethod
    async def list_movements(
        self,
        company_id: UUID,
        limit: int = 50,
        offset: int = 0,
        movement_type: Optional[str] = None,
        warehouse_id: Optional[UUID] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> tuple[List[DocumentListRowEntity], int]:
        """Listado paginado de documentos con filtro por tipo y rango de fechas. Retorna (lista, total)."""
        pass

    @abstractmethod
    async def get_kardex(
        self,
        product_id: UUID,
        warehouse_id: UUID,
        company_id: UUID,
        limit: int = 200
    ) -> List[KardexRowEntity]:
        """Kardex: running balance por SKU/Almacén usando Window Function SQL."""
        pass

    @abstractmethod
    async def get_wac_valuation(
        self,
        product_id: UUID,
        warehouse_id: UUID,
        company_id: UUID,
        as_of_date: Optional[str] = None
    ) -> Optional[WACValuationEntity]:
        """Valoración por Costo Promedio Ponderado (CPP/WAC) sobre el ledger inmutable."""
        pass

    @abstractmethod
    async def get_abc_rotation(
        self,
        company_id: UUID,
        warehouse_id: Optional[UUID] = None
    ) -> List[RotationABCEntity]:
        """Analítica de rotación ABC: clasifica SKUs por velocidad de salida (30/90d)."""
        pass

    @abstractmethod
    async def search_inventory_products(
        self,
        query: str,
        company_id: UUID,
        warehouse_id: UUID,
        limit: int = 10
    ) -> List[InventorySearchRowEntity]:
        """Búsqueda avanzada de productos con stock, UOM y clase ABC."""
        pass
    @abstractmethod
    async def get_dashboard_telemetry(self, warehouse_id: UUID, company_id: UUID) -> DashboardTelemetryEntity:
        """
        Calcula métricas clave para el dashboard: valoración total, alertas y serie temporal.
        """
        pass

    @abstractmethod
    async def get_warehouse_owner_id(self, warehouse_id: UUID) -> Optional[UUID]:
        """Recupera el company_id propietario de un almacén."""
        pass
    @abstractmethod
    async def get_document_by_id(self, document_id: UUID, company_id: UUID) -> Optional[DocumentDetailEntity]:
        """Recupera los detalles completos de un documento, incluyendo sus partidas."""
        pass

    @abstractmethod
    async def create_inventory_document(self, document_entity: dict, company_id: UUID) -> Any:
        """Crea un nuevo documento de inventario aglutinante."""
        pass

    @abstractmethod
    async def ensure_transit_warehouse(self, to_warehouse_id: UUID, company_id: UUID) -> UUID:
        """Asegura que el almacén de tránsito (virtual) para el destino exista localmente."""
        pass
    
    @abstractmethod
    async def get_customs_balances(
        self, 
        company_id: UUID, 
        warehouse_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
        query: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """
        Customs Balance Report (Phase 42.3 / Anexo 24).
        Retorna agregación por SKU y Pedimento con saldo residual y vencimientos.
        Soporta paginación y búsqueda para escalabilidad (industrial scale).
        """
        pass

    @abstractmethod
    async def get_available_movements_fifo(
        self,
        product_id: UUID,
        warehouse_id: UUID,
        company_id: UUID
    ) -> List[MovementEntity]:
        """
        Calculates the available stock-bearing movements (IN, TRANSFER_IN, etc.)
        sorted by FIFO (Customs Date or Created At).
        """
        pass

    @abstractmethod
    async def get_warehouse_entity(self, warehouse_id: UUID) -> Any:
        """
        Recupera los detalles de un almacén como Entidad de Dominio.
        """
        pass

    @abstractmethod
    async def consume_movement_balance(self, movement_id: UUID, quantity: Decimal):
        """
        Decrements the available_quantity of a specific movement record (FIFO consumption).
        """
        pass

    @abstractmethod
    async def get_variants_by_product(self, product_id: UUID, company_id: UUID) -> List[Any]:
        """Recupera todas las variantes registradas para un producto."""
        pass

    @abstractmethod
    async def upsert_variant(self, variant_data: dict, company_id: UUID) -> Any:
        """Crea o actualiza una variante de producto."""
        pass

    @abstractmethod
    async def get_quick_catalog(self, company_id: UUID) -> List[dict]:
        """
        Recupera una lista ligera de todos los productos (SKU + Nombre) para caché local.
        """
        pass

    @abstractmethod
    async def get_location_occupancy(self, warehouse_id: UUID, location_code: str, company_id: UUID) -> Decimal:
        """
        Calcula la cantidad total de piezas actualmente en una ubicación.
        """
        pass

    @abstractmethod
    async def get_location_capacity(self, warehouse_id: UUID, location_code: str, company_id: UUID) -> Decimal:
        """
        Recupera la capacidad máxima configurada para una ubicación.
        """
        pass

    @abstractmethod
    async def get_detailed_stock_report(self, warehouse_id: UUID, company_id: UUID) -> List[dict]:
        """
        Genera el listado detallado de existencias para auditoría física (Cycle Count).
        Incluye Ubicación, SKU, Pedimento y Cantidad Disponible.
        """
        pass

