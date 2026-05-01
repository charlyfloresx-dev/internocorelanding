import uuid
import logging
from sqlalchemy.orm import Session
from mes_app.models.production_run import ProductionRun
from mes_app.models.downtime_event import DowntimeEvent
from mes_app.models.labor_allocation import LaborAllocation
from mes_app.models.run_metrics_snapshot import RunMetricsSnapshot
from mes_app.models.scrap_entry import ScrapEntry
from mes_app.core.services.manufacturing_math import ManufacturingMath

logger = logging.getLogger(__name__)

class CloseProductionRunCommand:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, company_id: uuid.UUID, production_run_id: uuid.UUID, available_mins: float) -> RunMetricsSnapshot:
        """
        Closes a production run, calculating the definitive KPIs based on reported events
        (downtimes, pieces, labor) and saves the immutable snapshot.
        """
        # 1. Fetch the shift header
        run = self.db.query(ProductionRun).filter_by(id=production_run_id, company_id=company_id).first()
        if not run:
            raise ValueError("Production Run not found")

        # 2. Extract Planned Downtimes
        downtimes = self.db.query(DowntimeEvent).filter_by(production_run_id=production_run_id).all()
        planned_downtime_mins = sum(float(d.duration_minutes) for d in downtimes if d.is_planned)
        
        # 3. Calculate Productive Time
        productive_mins = ManufacturingMath.calculate_productive_time(available_mins, planned_downtime_mins)

        # 4. Extract Manpower
        labor = self.db.query(LaborAllocation).filter_by(production_run_id=production_run_id).first()
        operator_count = labor.operator_count if labor else 1

        # 5. Core Math and Financial Metric (LMPU)
        actual_qty = run.actual_quantity
        planned_qty = run.planned_quantity

        lmpu = ManufacturingMath.calculate_lmpu(productive_mins, operator_count, actual_qty)
        tak_time = ManufacturingMath.calculate_tak_time_seconds(productive_mins, actual_qty)

        # 6. Extract Scrap and Calculate Quality
        scrap_entries = self.db.query(ScrapEntry).filter_by(production_run_id=production_run_id).all()
        total_scrap = sum(s.quantity for s in scrap_entries)
        quality = ManufacturingMath.calculate_quality(actual_qty, total_scrap)

        # 7. OEE Breakdown
        availability = (productive_mins / available_mins) if available_mins > 0 else 0.0
        efficiency = (actual_qty / planned_qty) if planned_qty > 0 else 0.0
        
        oee = ManufacturingMath.calculate_oee(availability, efficiency, quality)

        # 7. Persist Read Model
        snapshot = self.db.query(RunMetricsSnapshot).filter_by(production_run_id=production_run_id).first()
        if not snapshot:
            snapshot = RunMetricsSnapshot(
                company_id=company_id,
                production_run_id=production_run_id
            )
            self.db.add(snapshot)

        snapshot.availability = availability
        snapshot.efficiency = efficiency
        snapshot.quality = quality
        snapshot.oee = oee
        snapshot.tak_time_seconds = tak_time
        snapshot.lmpu_minutes = lmpu

        self.db.flush()
        
        logger.info(f"Production Run {production_run_id} closed. OEE: {oee:.2f}, LMPU: {lmpu:.2f} min/unit")
        
        # Here we would normally emit a Domain Event for the system bus
        # event_bus.publish("ProductionRunClosed", {"run_id": str(production_run_id), "oee": oee})

        return snapshot
