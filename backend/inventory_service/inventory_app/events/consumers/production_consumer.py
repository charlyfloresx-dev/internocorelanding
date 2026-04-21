import uuid
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from inventory_app.models.bom import BOM
from inventory_app.models.backflush_error import BackflushError, BackflushErrorType, BackflushStatus
from inventory_app.models.inventory import InventoryLevel, InventoryTransaction, TransactionType
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.domain.entities.inventory_item import MovementEntity

logger = logging.getLogger(__name__)

class ProductionReportedConsumer:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = SQLAlchemyInventoryRepository(session)

    async def consume(self, event_data: dict):
        """
        Processes a ProductionReported event with high resilience:
        1. Explodes the BOM for the finished good.
        2. Deducts components from stock, allowing negative balance if needed.
        3. Tracks errors (Missing BOM/Stock) in BackflushError table.
        4. Notifies via event emission.
        """
        company_id = uuid.UUID(event_data["company_id"])
        parent_item_code = event_data["item_code"]
        produced_qty = event_data["qty"]
        event_id = uuid.UUID(event_data["event_id"])
        production_run_id = uuid.UUID(event_data["production_run_id"])

        logger.info(f"RESILIENT_BACKFLUSH: Processing {parent_item_code} (Qty: {produced_qty}, Event: {event_id})")

        # 1. Fetch BOM for the parent item
        stmt = select(BOM).where(BOM.parent_item_code == parent_item_code, BOM.company_id == company_id)
        result = await self.session.execute(stmt)
        bom_items = result.scalars().all()

        if not bom_items:
            await self._log_error(
                event_id=event_id,
                run_id=production_run_id,
                item_code=parent_item_code,
                req_qty=produced_qty,
                err_type=BackflushErrorType.MISSING_BOM,
                company_id=company_id,
                details=f"No Bill of Materials found for item {parent_item_code}"
            )
            return

        # 2. Process each component in BOM
        for bom_line in bom_items:
            required_qty = produced_qty * bom_line.quantity_per_unit
            
            # Map item_code to product_id (Simplified: assuming item_code exists or resolved via master data)
            # In this MVP, we use a placeholder lookup or assuming the item_code IS the product reference for now
            # FIXME: Real product_id resolution required
            component_product_id = uuid.uuid5(uuid.NAMESPACE_OID, bom_line.component_item_code)
            
            # 3. Attempt Stock Deduction
            try:
                # We use a default warehouse for now (e.g., MAIN)
                # In production, this should come from the ProductionRun or Resource config
                warehouse_id = uuid.uuid5(uuid.NAMESPACE_OID, "MAIN_WAREHOUSE")
                
                # Create movement record
                movement = MovementEntity(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    product_id=component_product_id,
                    warehouse_id=warehouse_id,
                    quantity=-required_qty, # Negative for deduction
                    movement_type="BACKFLUSHING",
                    document_type="PRODUCTION_RUN",
                    document_id=production_run_id
                )

                # Atomically record movement, allowing negative to NOT block production
                stock = await self.repository.record_movement(
                    movement=movement, 
                    allow_negative=True # INDUSTRIAL RESILIENCE: Never block the line
                )

                # Check if we broke stock parameters to log an INSUFFICIENT_STOCK warning
                if stock.quantity < 0:
                    await self._log_error(
                        event_id=event_id,
                        run_id=production_run_id,
                        item_code=bom_line.component_item_code,
                        req_qty=required_qty,
                        err_type=BackflushErrorType.INSUFFICIENT_STOCK,
                        company_id=company_id,
                        details=f"Stock became negative ({stock.quantity}) for component {bom_line.component_item_code}"
                    )

            except Exception as e:
                logger.error(f"Failed to backflush component {bom_line.component_item_code}: {str(e)}")
                # We log the error but don't abort the entire event processing
                await self._log_error(
                    event_id=event_id,
                    run_id=production_run_id,
                    item_code=bom_line.component_item_code,
                    req_qty=required_qty,
                    err_type=BackflushErrorType.INSUFFICIENT_STOCK,
                    company_id=company_id,
                    details=f"Unexpected error: {str(e)}"
                )

        await self.session.commit()
        logger.info(f"RESILIENT_BACKFLUSH: Completed for event {event_id}")

    async def _log_error(self, event_id, run_id, item_code, req_qty, err_type, company_id, details):
        """Internal helper to log backflush failures and emit alerts."""
        error_log = BackflushError(
            event_id=event_id,
            production_run_id=run_id,
            item_code=item_code,
            required_qty=req_qty,
            error_type=err_type,
            company_id=company_id,
            status=BackflushStatus.PENDING,
            error_details=details
        )
        self.session.add(error_log)
        
        # Emit Notification Event
        alert_payload = {
            "title": f"Backflushing Alert: {err_type}",
            "description": details,
            "company_id": str(company_id),
            "production_run_id": str(run_id)
        }
        logger.warning(f"EVENT_EMISSION: InventoryAlertGenerated -> {alert_payload}")
