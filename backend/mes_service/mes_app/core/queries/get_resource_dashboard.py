import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from mes_app.models.production_snapshot import HourlyProductionSnapshot
from datetime import date

class GetResourceDashboardQuery:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, company_id: uuid.UUID, resource_id: uuid.UUID, dashboard_date: date) -> List[Dict[str, Any]]:
        """
        Retrieves the dashboard metrics for a specific resource and date.
        Thanks to the CQRS event-driven architecture, this is an O(1) query against
        the HourlyProductionSnapshot table which is automatically updated when production is reported.
        """
        snapshots = self.db.query(HourlyProductionSnapshot).filter(
            HourlyProductionSnapshot.company_id == company_id,
            HourlyProductionSnapshot.resource_id == resource_id,
            HourlyProductionSnapshot.date == dashboard_date
        ).order_by(HourlyProductionSnapshot.hour).all()

        # Format the result directly for the frontend graphing component
        result = []
        for snap in snapshots:
            result.append({
                "hour": snap.hour,
                "goal": snap.goal_quantity,
                "actual": snap.actual_quantity,
                "efficiency": float(snap.efficiency_percentage),
                "item_code": snap.item_code
            })
            
        return result
