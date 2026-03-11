import uuid
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.work_order import WorkOrder
from app.models.standard_time import StandardTime
import logging

logger = logging.getLogger(__name__)

class CreateWorkOrderCommand:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, company_id: uuid.UUID, order_number: str, item_code: str, order_quantity: int) -> WorkOrder:
        """
        Creates a WorkOrder. 
        If standard_time for the item_code exists, calculate estimated duration (not actually stored in WorkOrder yet, but logged or available for logic).
        """
        # Look up standard time
        standard_time = self.db.query(StandardTime).filter(
            StandardTime.company_id == company_id,
            StandardTime.item_code == item_code
        ).first()

        # Create WorkOrder
        work_order = WorkOrder(
            company_id=company_id,
            order_number=order_number,
            item_code=item_code,
            order_quantity=order_quantity,
            manufactured_quantity=0,
            status="DRAFT",
            start_date=None,
            request_date=None,
        )

        # Logic for estimating duration based on standard time
        if standard_time:
            # set_time_hours is Numeric, we can treat it as float for calculation
            estimated_duration_hours = float(standard_time.set_time_hours) * order_quantity
            logger.info(f"Work order {order_number} estimated to take {estimated_duration_hours} hours according to standard time.")
            # Depending on model if there's a field for it, we would save it here.
            # E.g., if there's an estimated_hours field added later.
            
        self.db.add(work_order)
        self.db.flush() # ensure ID is generated but don't commit yet to allow atomic operations
        
        return work_order
