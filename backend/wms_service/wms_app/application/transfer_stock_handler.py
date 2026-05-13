import uuid
from decimal import Decimal
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from common.exceptions import BusinessRuleException, NotFoundException
from wms_app.models.location import Location
from wms_app.models.inventory_movement import InventoryMovement
from wms_app.models.concept import Concept, ConceptType
from wms_app.models.inventory_document import InventoryDocument, DocumentStatus
from datetime import datetime

logger = logging.getLogger(__name__)

class TransferStockCommand:
    def __init__(self, product_id: str, source_location_id: str, target_location_id: str, quantity: Decimal, warehouse_id: str):
        self.product_id = product_id
        self.source_location_id = source_location_id
        self.target_location_id = target_location_id
        self.quantity = quantity
        self.warehouse_id = warehouse_id

class TransferStockHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def handle(self, command: TransferStockCommand) -> dict:
        """
        Atómicamente transfiere stock de una ubicación a otra.
        """
        async with self.session.begin_nested() as tx:
            # 1. Lock Source Location
            stmt_src = select(Location).filter_by(id=uuid.UUID(command.source_location_id)).with_for_update()
            source_loc = (await self.session.execute(stmt_src)).scalar_one_or_none()
            
            if not source_loc:
                raise NotFoundException("Source location not found.")
                
            # 2. Lock Target Location
            stmt_tgt = select(Location).filter_by(id=uuid.UUID(command.target_location_id)).with_for_update()
            target_loc = (await self.session.execute(stmt_tgt)).scalar_one_or_none()

            if not target_loc:
                raise NotFoundException("Target location not found.")

            # Validations
            if not target_loc.is_active:
                raise BusinessRuleException("Target location is blocked.")
                
            if target_loc.max_capacity and target_loc.max_capacity > 0:
                if (target_loc.current_capacity or 0) + command.quantity > target_loc.max_capacity:
                    raise BusinessRuleException("Target location is full. Cannot transfer stock.")

            # Modify capacities
            source_loc.current_capacity = (source_loc.current_capacity or 0) - command.quantity
            target_loc.current_capacity = (target_loc.current_capacity or 0) + command.quantity

            # Document generation for Kardex
            doc = InventoryDocument(
                folio=f"TRF-{uuid.uuid4().hex[:6].upper()}",
                warehouse_id=uuid.UUID(command.warehouse_id),
                status=DocumentStatus.CONFIRMED,
                date=datetime.utcnow()
            )
            self.session.add(doc)
            await self.session.flush()

            # OUT Movement
            mov_out = InventoryMovement(
                document_id=doc.id,
                product_id=uuid.UUID(command.product_id),
                warehouse_id=uuid.UUID(command.warehouse_id),
                sequence_number=1,
                quantity=-command.quantity,
                location_id=source_loc.id
            )
            
            # IN Movement
            mov_in = InventoryMovement(
                document_id=doc.id,
                product_id=uuid.UUID(command.product_id),
                warehouse_id=uuid.UUID(command.warehouse_id),
                sequence_number=2,
                quantity=command.quantity,
                location_id=target_loc.id
            )
            
            self.session.add(mov_out)
            self.session.add(mov_in)
            
            return {
                "id": str(doc.id),
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }
