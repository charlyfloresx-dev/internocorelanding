import uuid
from datetime import date
from sqlalchemy.orm import Session
from mes_app.models.production_run import ProductionRun
from mes_app.models.work_order import WorkOrder
from mes_app.models.resource import Resource

class ScheduleProductionCommand:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, company_id: uuid.UUID, work_order_id: uuid.UUID, resource_id: uuid.UUID, 
                shift_id: uuid.UUID, schedule_date: date, planned_qty: int) -> ProductionRun:
        """
        Schedules a production run, ensuring multi-tenant consistency and preventing resource conflicts.
        """
        # 1. Verify Company Consistency & Existence
        wo = self.db.query(WorkOrder).filter_by(id=work_order_id, company_id=company_id).first()
        if not wo:
            raise ValueError(f"Work Order {work_order_id} not found or belongs to another company.")

        res = self.db.query(Resource).filter_by(id=resource_id, company_id=company_id).first()
        if not res:
            raise ValueError(f"Resource {resource_id} not found or belongs to another company.")

        # 2. Conflict Check: Verify Resource/Shift/Date availability
        existing = self.db.query(ProductionRun).filter_by(
            resource_id=resource_id,
            date=schedule_date,
            shift_id=shift_id,
            company_id=company_id
        ).first()
        
        if existing:
            raise ValueError(f"Resource {resource_id} already has a Production Run scheduled for {schedule_date} on Shift {shift_id}.")

        # 3. Create scheduled run
        new_run = ProductionRun(
            company_id=company_id,
            work_order_id=work_order_id,
            resource_id=resource_id,
            shift_id=shift_id,
            date=schedule_date,
            planned_quantity=planned_qty,
            actual_quantity=0,
            status="SCHEDULED"
        )
        
        self.db.add(new_run)
        self.db.flush() # Ensure ID is generated
        
        return new_run
