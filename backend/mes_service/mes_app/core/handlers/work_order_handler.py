import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from common.exceptions import BusinessRuleException
from mes_app.models.work_order import WorkOrder

logger = logging.getLogger(__name__)

class CreateWorkOrderCommand:
    def __init__(self, order_number: str, item_code: str, order_qty: int, due_date: datetime, company_id: uuid.UUID, alias: str = None):
        self.order_number = order_number
        self.item_code = item_code
        self.order_qty = order_qty
        self.due_date = due_date
        self.company_id = company_id
        self.alias = alias

class WorkOrderHandler:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_create(self, command: CreateWorkOrderCommand) -> dict:
        """
        Orchestrates atomic creation of a WorkOrder using Unit of Work pattern.
        """
        # Unit of Work transaction block
        # Because get_db() provides a session, we can use begin_nested() to manage the exact atomic boundaries 
        # or rely on an explicit transaction.
        async with self.db.begin_nested() as tx:
            try:
                # 1. Validation of Stock (Mocked external call to Inventory Service)
                # In production, this would be an HTTP/gRPC call. 
                # For this CQRS Audit simulation, we reject if order_qty > 1000.
                if command.order_qty > 1000:
                    raise BusinessRuleException(
                        "Not enough stock available for production in Inventory Service.", 
                        code="INSUFFICIENT_STOCK"
                    )

                # 2. Calculation of materials (Domain logic simulation)
                # Here we would resolve the BOM (Bill of Materials)
                
                # 3. Create the WorkOrder
                wo = WorkOrder(
                    id=uuid.uuid4(),
                    company_id=command.company_id,
                    order_number=command.order_number,
                    item_code=command.item_code,
                    order_quantity=command.order_qty,
                    request_date=command.due_date,
                    alias=command.alias,
                    release_date=datetime.now(timezone.utc),
                    status="DRAFT"
                )
                self.db.add(wo)
                
                # 4. Insert Audit Log
                logger.info(f"[AUDIT] WorkOrder {wo.id} created for company {wo.company_id}")
                
                # DB Flushes inside the nested transaction
                await self.db.flush()
                
            except Exception as e:
                # If anything fails, rollback the exact nested transaction
                await tx.rollback()
                raise e

        # If success, the commit is handled downstream or by the nested block.
        # We return the exact strictly-typed DTO expected by CQRS.
        return {
            "id": str(wo.id),
            "status": wo.status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
