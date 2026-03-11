import uuid
from decimal import Decimal
from app.domain.repositories.inventory_repository import IInventoryRepository
from app.domain.entities.inventory_item import MovementEntity

class TransferService:
    def __init__(self, repo: IInventoryRepository):
        self.repository = repo

    async def dispatch_transfer(self, from_warehouse_id: uuid.UUID, to_warehouse_id: uuid.UUID, product_id: uuid.UUID, quantity: Decimal, company_id: uuid.UUID, transfer_id: uuid.UUID) -> MovementEntity:
        """
        Moves stock from source to IN_TRANSIT virtual warehouse.
        """
        # 1. OUT from source warehouse
        out_movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=from_warehouse_id,
            product_id=product_id,
            company_id=company_id,
            quantity=-quantity,
            movement_type="OUT",
            document_type="TRANSFER_DISPATCH",
            document_id=transfer_id
        )
        await self.repository.record_movement(out_movement)
        
        # 2. IN to IN_TRANSIT virtual warehouse 
        # Deterministic UUID for the transit location of the destination warehouse
        transit_warehouse_id = uuid.uuid5(uuid.NAMESPACE_OID, f"{to_warehouse_id}_transit")
        
        in_transit_movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=transit_warehouse_id,
            product_id=product_id,
            company_id=company_id,
            quantity=quantity,
            movement_type="IN",
            document_type="TRANSFER_IN_TRANSIT",
            document_id=transfer_id
        )
        await self.repository.record_movement(in_transit_movement, allow_negative=True)
        
        return out_movement
    async def receive_transfer(self, from_warehouse_id: uuid.UUID, to_warehouse_id: uuid.UUID, product_id: uuid.UUID, quantity: Decimal, company_id: uuid.UUID, transfer_id: uuid.UUID) -> MovementEntity:
        """
        Moves stock from IN_TRANSIT to final destination.
        Implements Idempotency to prevent double-receiving.
        """
        # 1. Idempotency Check: Already received?
        if await self.repository.has_processed_document("TRANSFER_RECEIVE", transfer_id, company_id):
            return None # Already processed
            
        transit_warehouse_id = uuid.uuid5(uuid.NAMESPACE_OID, f"{to_warehouse_id}_transit")

        # 2. OUT from IN_TRANSIT
        out_transit_movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=transit_warehouse_id,
            product_id=product_id,
            company_id=company_id,
            quantity=-quantity,
            movement_type="OUT",
            document_type="TRANSFER_RECEIVE_TRANSIT",
            document_id=transfer_id
        )
        await self.repository.record_movement(out_transit_movement, allow_negative=True)
        
        # 3. IN to destination warehouse
        in_movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=to_warehouse_id,
            product_id=product_id,
            company_id=company_id,
            quantity=quantity,
            movement_type="IN",
            document_type="TRANSFER_RECEIVE",
            document_id=transfer_id
        )
        await self.repository.record_movement(in_movement)
        
        return in_movement
