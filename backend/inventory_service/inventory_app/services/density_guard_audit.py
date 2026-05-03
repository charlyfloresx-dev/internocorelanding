import uuid
import logging
from decimal import Decimal
from typing import Optional

from inventory_app.db.session import AsyncSessionLocal
from inventory_app.infrastructure.clients.master_data import MasterDataClient
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from notification_app.services.notification_service import NotificationService, NotificationCategory, NotificationPriority

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
    [Phase 64] Monolith-Integrated Density Guard Audit.
    Runs in the background. Uses internal NotificationService for high-availability alerting.
    """
    logger.info("Background Audit: Checking location %s in WH %s (Movement: %s)", location_code, warehouse_id, movement_id)
    
    if repository and md_client:
        await _execute_audit(warehouse_id, location_code, quantity_moved, movement_id, company_id, repository, md_client, repository.session)
    else:
        async with AsyncSessionLocal() as session:
            repo = SQLAlchemyInventoryRepository(session)
            client = MasterDataClient()
            await _execute_audit(warehouse_id, location_code, quantity_moved, movement_id, company_id, repo, client, session)

async def _execute_audit(warehouse_id, location_code, quantity_moved, movement_id, company_id, repository, md_client, session):
    try:
        # 1. Fetch Capacity from Master Data
        capacity = await md_client.get_location_capacity(warehouse_id, location_code, company_id)
        
        # 2. Fetch current occupancy from local Ledger
        occupancy = await repository.get_location_occupancy(warehouse_id, location_code, company_id)
        
        # 3. Validation Logic
        is_overflow = False
        if capacity > 0 and occupancy > capacity:
            is_overflow = True
            logger.warning("DENSITY_OVERFLOW: Location %s is at %s/%s capacity.", location_code, occupancy, capacity)
        
        # 4. Update Movement Status
        status = "OVERFLOW_CONFIRMED" if is_overflow else "CLEAN"
        
        import sqlalchemy as sa
        from inventory_app.models.movement import Movement
        
        stmt = (
            sa.update(Movement)
            .where(Movement.id == movement_id)
            .values(validation_status=status)
        )
        await session.execute(stmt)
        
        # 5. Notify via INTERNAL Service if overflow
        if is_overflow:
            from common.services.audit_service import AuditService
            await AuditService.log_action(
                db=session,
                user_id="SYSTEM_DENSITY_GUARD",
                action="DENSITY_OVERFLOW",
                entity_name="inventory_locations",
                entity_id=location_code,
                company_id=company_id,
                details=f"Overflow detected: {occupancy}/{capacity}",
                new_value={
                    "loc": location_code,
                    "occupancy": float(occupancy),
                    "capacity": float(capacity),
                    "movement_id": str(movement_id)
                }
            )
            
            # Injecting the notification service with the active session
            notif_service = NotificationService(session)
            await notif_service.notify_role(
                company_id=company_id,
                role_name="OPERATIONS_MANAGER", # Broadcast to tactical managers
                title="ALERTA DE DENSIDAD",
                message=f"La ubicacion {location_code} ha excedido su capacidad maxima ({occupancy}/{capacity}).",
                category=NotificationCategory.INVENTORY,
                priority=NotificationPriority.HIGH,
                metadata={
                    "warehouse_id": str(warehouse_id),
                    "location_code": location_code,
                    "occupancy": float(occupancy),
                    "capacity": float(capacity),
                    "movement_id": str(movement_id)
                }
            )
        
        # Final Commit (Status + Notifications)
        await session.commit()

    except Exception as e:
        if session:
            await session.rollback()
        logger.error("Density Guard Audit Failed for movement %s: %s", movement_id, e)
