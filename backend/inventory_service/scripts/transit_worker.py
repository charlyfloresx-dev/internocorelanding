import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.movement import Movement
from app.infrastructure.tickets_client import TicketsClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("transit_age_worker")

class TransitWorker:
    """
    Background worker that scans the Movement ledger looking for
    dispatched transfers (OUTs mapped to a Transit Warehouse UUID)
    that have aged beyond SLAs (24h warning, 48h critical).
    """

    WARNING_THRESHOLD_HOURS = 24
    CRITICAL_THRESHOLD_HOURS = 48

    @classmethod
    async def evaluate_transit_ages(cls):
        logger.info("[START] Evaluating prolonged transit ages...")
        
        async with SessionLocal() as db:
            # Step 1: Query all OUT movements pointing to transit locations
            # Usually, source_warehouse dispatch adds OUT, and destination adds IN.
            # However, during Transit, the destination warehouse UUID is virtual.
            # In our system, `transfer_dispatch` makes an OUT on source, IN on transit.
            # BUT the virtual Transit warehouse is actually a real hash UUID5.
            # So we look for IN movements occurring on a Transit Warehouse 
            # (which means stock entered Transit) that do not have a corresponding OUT yet 
            # (meaning it hasn't left Transit).
            # For simplicity in this worker logic: we will scan ALL movements that have "document_type" == "TRANSFER_DISPATCH"
            
            stmt = select(Movement).where(
                Movement.document_type == "TRANSFER_DISPATCH",
                Movement.movement_type == "OUT"
            )
            
            result = await db.execute(stmt)
            dispatches = result.scalars().all()
            
            evaluated = 0
            for dispatch in dispatches:
                # 1. Check if it was received (Look for TRANSFER_RECEIVE with same document_id)
                receive_stmt = select(Movement).where(
                    Movement.document_id == dispatch.document_id,
                    Movement.document_type == "TRANSFER_RECEIVE"
                )
                rx_result = await db.execute(receive_stmt)
                receipt = rx_result.scalar_one_or_none()
                
                if receipt:
                    continue # Already received, ignore
                
                # 2. It is still in transit. Let's check age.
                # NOTE: SQLAlchemy DateTime depends on server timezone. Assuming UTC timezone for created_at.
                # If created_at is naive, we give it UTC timezone.
                created_at = dispatch.created_at
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                    
                age = datetime.now(timezone.utc) - created_at
                
                if age > timedelta(hours=cls.CRITICAL_THRESHOLD_HOURS):
                    logger.error(f"[!] CRITICAL: Dispatch {dispatch.document_id} has been in transit for > 48 hours.")
                    await TicketsClient.post_system_alert(
                        title="MEDIUM: Prolonged Transit Latency",
                        description=f"Transfer {dispatch.document_id} has been in transit for {age.total_seconds() / 3600:.1f} hours without receipt.",
                        priority="P3_MEDIUM",
                        company_id=dispatch.company_id,
                        product_id=dispatch.product_id,
                        warehouse_id=dispatch.warehouse_id,
                        transaction_id=dispatch.document_id
                    )
                elif age > timedelta(hours=cls.WARNING_THRESHOLD_HOURS):
                    # Internal Logging only as requested
                    logger.warning(f"[*] WARNING: Dispatch {dispatch.document_id} has been in transit for > 24 hours.")
                
                evaluated += 1

        logger.info(f"[END] Evaluated {evaluated} pending transit movements.")

if __name__ == "__main__":
    asyncio.run(TransitWorker.evaluate_transit_ages())
