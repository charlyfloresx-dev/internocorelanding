import uuid
from decimal import Decimal
from typing import List, Optional
from app.domain.repositories.inventory_repository import IInventoryRepository
from app.domain.interfaces.master_data_client import IMasterDataClient
from app.domain.entities.inventory_item import MovementEntity, InventoryLevelEntity
from app.schemas.stock import MovementCreate

class InventoryTransactionService:
    def __init__(self, repo: IInventoryRepository, md_client: IMasterDataClient):
        self.repository = repo
        self.md_client = md_client

    async def register_movement(self, cmd: MovementCreate, company_id: uuid.UUID) -> MovementEntity:
        """
        Orchestrates the registration of an inventory movement.
        """
        # 1. Cross-service validation
        if not await self.md_client.validate_product(cmd.product_id, company_id):
            raise ValueError("ERR_INVALID_PRODUCT: Product not found in Master Data.")

        # 2. Create Movement Entity
        movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=cmd.warehouse_id,
            product_id=cmd.product_id,
            company_id=company_id,
            quantity=cmd.quantity,
            movement_type=cmd.movement_type,
            document_type=cmd.document_type,
            document_id=cmd.document_id
        )
        
        # 3. Atomically update stock via Repository
        await self.repository.record_movement(movement)
        
        return movement

    async def reconcile_stock(self, warehouse_id: uuid.UUID, product_id: uuid.UUID, physical_qty: Decimal, company_id: uuid.UUID):
        """
        Reconciliation Workflow: Physical Count vs System Balance.
        """
        stock = await self.repository.get_stock(warehouse_id, product_id, company_id)
        current_qty = stock.quantity if stock else Decimal(0)
        
        diff = physical_qty - current_qty
        
        if diff == 0:
            return None

        adjustment = MovementCreate(
            warehouse_id=warehouse_id,
            product_id=product_id,
            quantity=diff,
            movement_type="ADJUSTMENT",
            document_type="RECONCILIATION",
            document_id=uuid.uuid4()
        )
        
        return await self.register_movement(adjustment, company_id)

    async def search_variants(self, query: str, company_id: uuid.UUID, limit: int = 10) -> List[dict]:
        """
        Specialized search for Typeahead.
        """
        return await self.repository.search_items_and_variants(query, company_id, limit)
