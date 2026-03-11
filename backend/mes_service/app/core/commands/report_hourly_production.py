import uuid
import logging
from sqlalchemy import update, func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.production_run import ProductionRun
from app.models.production_snapshot import HourlyProductionSnapshot
from app.models.resource import Resource

logger = logging.getLogger(__name__)

class ReportHourlyProductionCommand:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, company_id: uuid.UUID, production_run_id: uuid.UUID, 
                hour: int, quantity: int) -> bool:
        """
        Records hourly production using atomic SQL increments and UPSERT for snapshots.
        """
        if not (0 <= hour <= 23):
            raise ValueError("Hour must be between 0 and 23.")

        # 1. Fetch Production Run to check existence and get metadata
        run = self.db.query(ProductionRun).filter_by(id=production_run_id, company_id=company_id).first()
        if not run:
            raise ValueError(f"Production Run {production_run_id} not found.")

        # 2. Atomic Increment of Total Quantity
        stmt = (
            update(ProductionRun)
            .where(ProductionRun.id == production_run_id)
            .where(ProductionRun.company_id == company_id)
            .values(actual_quantity=ProductionRun.actual_quantity + quantity)
        )
        self.db.execute(stmt)

        # 3. UPSERT for HourlyProductionSnapshot
        # Calculate goal per hour (very simplified: total_goal / 8 hours typical shift)
        # In a real system, this would be more complex based on specific shift hours
        hourly_goal = run.planned_quantity // 8 if run.planned_quantity > 0 else 0
        
        # We need the item_code for the snapshot. We can get it from the WorkOrder via the Run.
        # For efficiency, we assume the run has a way to get the item_code or we fetch it.
        from app.models.work_order import WorkOrder
        wo = self.db.query(WorkOrder).filter_by(id=run.work_order_id).first()
        item_code = wo.item_code if wo else "UNKNOWN"

        upsert_stmt = insert(HourlyProductionSnapshot).values(
            id=uuid.uuid4(),
            company_id=company_id,
            resource_id=run.resource_id,
            production_run_id=production_run_id,
            date=run.date,
            hour=hour,
            goal_quantity=hourly_goal,
            actual_quantity=quantity,
            item_code=item_code,
            efficiency_percentage=float((quantity / hourly_goal) * 100) if hourly_goal > 0 else 0.0
        )

        upsert_stmt = upsert_stmt.on_conflict_do_update(
            constraint="uq_hourly_snapshot",
            set_={
                "actual_quantity": upsert_stmt.excluded.actual_quantity,
                "efficiency_percentage": upsert_stmt.excluded.efficiency_percentage
            }
        )

        self.db.execute(upsert_stmt)
        self.db.flush()

        # 4. Emit ProductionReported Event (Backflushing Trigger)
        # In a full system, this would go to RabbitMQ/NATS via an Outbox or Event Bus
        event_payload = {
            "event_id": str(uuid.uuid4()),
            "production_run_id": str(production_run_id),
            "item_code": item_code,
            "qty": quantity,
            "company_id": str(company_id),
            "timestamp": func.now()
        }
        logger.info(f"EVENT_EMISSION: ProductionReported -> {event_payload}")

        logger.info(f"Reported {quantity} units for Run {production_run_id} at hour {hour}.")
        return True
