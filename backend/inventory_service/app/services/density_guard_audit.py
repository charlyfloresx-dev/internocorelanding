import uuid
import logging
from decimal import Decimal
from typing import Optional

from app.db.session import AsyncSessionLocal
from app.infrastructure.clients.master_data import MasterDataClient
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository

logger = logging.getLogger(__name__)

async def run_density_guard_audit(
    warehouse_id: uuid.UUID,
    location_code: str,
    quantity_moved: Decimal,
    movement_id: uuid.UUID,
    company_id: uuid.UUID,
    repository: Optional[SQLAlchemyInventoryRepository] = None,
    md_client: Optional[MasterDataClient] = None
):
    """
    [Phase 63] Asynchronous Density Guard Audit.
    Runs in the background after 202 Accepted response.
    Never blocks or reverts the movement.
    """
    logger.info(f"🔍 Background Audit: Checking location {location_code} in WH {warehouse_id} (Movement: {movement_id})")
    
    # 1. Use injected dependencies or create new ones
    if repository and md_client:
        # Use existing ones (for testing)
        await _execute_audit(warehouse_id, location_code, quantity_moved, movement_id, company_id, repository, md_client, repository.session)
    else:
        # Standard production flow: new isolated session
        async with AsyncSessionLocal() as session:
            repo = SQLAlchemyInventoryRepository(session)
            client = MasterDataClient()
            await _execute_audit(warehouse_id, location_code, quantity_moved, movement_id, company_id, repo, client, session)

async def _execute_audit(warehouse_id, location_code, quantity_moved, movement_id, company_id, repository, md_client, session):
    try:
        # 2. Fetch Capacity from Master Data (Source of Truth)
        capacity = await md_client.get_location_capacity(warehouse_id, location_code, company_id)
        
        # 3. Fetch current occupancy from local Ledger
        occupancy = await repository.get_location_occupancy(warehouse_id, location_code, company_id)
        
        # 4. Validation Logic
        is_overflow = False
        if capacity > 0 and occupancy > capacity:
            is_overflow = True
            logger.warning(f"⚠️ DENSITY_OVERFLOW: Location {location_code} is at {occupancy}/{capacity} capacity.")
        
        # 5. Update Movement Status
        status = "OVERFLOW_CONFIRMED" if is_overflow else "CLEAN"
        
        import sqlalchemy as sa
        from app.models.movement import Movement
        
        stmt = (
            sa.update(Movement)
            .where(Movement.id == movement_id)
            .values(validation_status=status)
        )
        await session.execute(stmt)
        await session.commit()
        
        # 6. Notify Notification Service if overflow
        if is_overflow:
            await notify_overflow(warehouse_id, location_code, occupancy, capacity, company_id)

    except Exception as e:
        if session:
            await session.rollback()
        logger.error(f"❌ Density Guard Audit Failed for movement {movement_id}: {str(e)}")

async def notify_overflow(warehouse_id, location_code, occupancy, capacity, company_id):
    """
    Sends event to Notification Service.
    """
    import httpx
    from common.config import settings

    # Centralized URL for notification service
    notify_url = f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/events/"
    
    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "CapacityViolationEvent",
        "warehouse_id": str(warehouse_id),
        "location_code": location_code,
        "current_occupancy": float(occupancy),
        "max_capacity": float(capacity),
        "severity": "YELLOW"
    }
    
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                notify_url,
                json=payload,
                headers={"X-Company-ID": str(company_id)}
            )
            logger.info(f"📢 Overflow notification sent for {location_code}")
    except Exception as e:
        logger.error(f"Fail-Safe: Could not notify notification service: {str(e)}")
