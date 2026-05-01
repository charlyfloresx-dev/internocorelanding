import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, List
from mes_app.domain.repositories.interfaces import (
    IProductionRunRepository, IManufacturingLedgerRepository,
    IDowntimeRepository, ILaborRepository, IGoalRepository
)
from common.exceptions import NotFoundException

class KPIService:
    """
    Servicio encargado de los cálculos de OEE y KPIs en tiempo real.
    Shielded from SQLAlchemy.
    """
    
    def __init__(
        self, 
        run_repo: IProductionRunRepository,
        ledger_repo: IManufacturingLedgerRepository,
        downtime_repo: IDowntimeRepository,
        labor_repo: ILaborRepository,
        goal_repo: IGoalRepository
    ):
        self.run_repo = run_repo
        self.ledger_repo = ledger_repo
        self.downtime_repo = downtime_repo
        self.labor_repo = labor_repo
        self.goal_repo = goal_repo

    async def calculate_oee(self, resource_result_id: uuid.UUID) -> Dict[str, Any]:
        result = await self.run_repo.get_by_id(resource_result_id)
        if not result:
            raise NotFoundException("ProductionRun not found")

        start_time = result.created_at
        end_time = datetime.now()
        shift_duration_minutes = (end_time - start_time).total_seconds() / 60

        downtime_minutes = await self._get_total_downtime(resource_result_id)
        if shift_duration_minutes > 0:
            availability = (shift_duration_minutes - downtime_minutes) / shift_duration_minutes
        else:
            availability = 0.0

        total_produced = await self.ledger_repo.get_total_produced(resource_result_id)
        total_labor_minutes = await self._get_total_labor_minutes(resource_result_id)
        
        if total_labor_minutes > 0:
            efficiency = float(total_produced) / (total_labor_minutes / 60.0) / 60.0
            efficiency = min(1.0, efficiency) 
        else:
            efficiency = 0.0

        quality = 1.0
        oee = availability * efficiency * quality

        theoretical_meta = await self.goal_repo.get_hour_meta(result.resource_id, end_time.hour)
        active_labor_count = await self.labor_repo.get_active_count_at(resource_result_id, end_time)
        planned_labor = 1
        labor_factor = active_labor_count / planned_labor
        adjusted_meta = int(theoretical_meta * labor_factor)

        andon_status = "OPERATING"
        active_dt = await self.downtime_repo.get_active_downtime(resource_result_id)
        if active_dt:
            andon_status = "DOWNTIME_PENDING" if active_dt.status == "OPEN" else "REPAIRING"

        return {
            "oee": round(oee * 100, 2),
            "availability": round(availability * 100, 2),
            "performance": round(efficiency * 100, 2), 
            "quality": 100.0,
            "adjusted_meta": adjusted_meta,
            "andon_status": andon_status,
            "metrics": {
                "produced": float(total_produced),
                "downtime_minutes": round(downtime_minutes, 2),
                "labor_minutes": round(total_labor_minutes, 2),
                "shift_duration_minutes": round(shift_duration_minutes, 2)
            }
        }

    async def _get_total_downtime(self, resource_result_id: uuid.UUID) -> float:
        downtimes = await self.downtime_repo.get_by_run_id(resource_result_id)
        total_minutes = 0.0
        for dt in downtimes:
            end = dt.closed_at or datetime.now()
            total_minutes += (end - dt.start_at).total_seconds() / 60
        return total_minutes

    async def _get_total_labor_minutes(self, resource_result_id: uuid.UUID) -> float:
        labors = await self.labor_repo.get_by_run_id(resource_result_id)
        total_minutes = 0.0
        for lb in labors:
            end = lb.clock_out or datetime.now()
            total_minutes += (end - lb.clock_in).total_seconds() / 60
        return total_minutes

    async def get_resource_graphic(self, resource_result_id: uuid.UUID) -> Dict[str, Any]:
        result = await self.run_repo.get_by_id(resource_result_id)
        if not result:
            raise NotFoundException("ProductionRun not found")

        start_hour = result.created_at.replace(minute=0, second=0, microsecond=0)
        end_time = datetime.now()
        end_hour = end_time.replace(minute=59, second=59, microsecond=0)

        graphic_data = {
            "categories": [], "meta": [], "real": [], "efficiency": [],
            "accumulated_real": [], "accumulated_meta": []
        }

        current_hour = start_hour
        acc_meta = 0
        acc_real = 0

        while current_hour <= end_hour:
            hour_label = current_hour.strftime("%H:00")
            theoretical_meta = await self.goal_repo.get_hour_meta(result.resource_id, current_hour.hour)
            active_labor_count = await self.labor_repo.get_active_count_at(resource_result_id, current_hour)
            planned_labor = 1
            adjusted_meta = int(theoretical_meta * (active_labor_count / planned_labor))
            
            acc_meta += adjusted_meta
            hour_real = await self.ledger_repo.get_produced_in_slot(resource_result_id, current_hour, current_hour + timedelta(hours=1))
            acc_real += float(hour_real)

            graphic_data["categories"].append(hour_label)
            graphic_data["meta"].append(adjusted_meta)
            graphic_data["accumulated_meta"].append(acc_meta)
            graphic_data["real"].append(float(hour_real))
            graphic_data["accumulated_real"].append(acc_real)
            
            eff = (float(hour_real) / adjusted_meta * 100) if adjusted_meta > 0 else 0.0
            graphic_data["efficiency"].append(min(100.0, round(eff, 2)))
            current_hour += timedelta(hours=1)

        return graphic_data
