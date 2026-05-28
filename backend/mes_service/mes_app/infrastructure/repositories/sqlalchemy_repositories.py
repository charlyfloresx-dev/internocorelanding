import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from mes_app.domain.repositories.interfaces import (
    IProductionRunRepository, IManufacturingLedgerRepository,
    IDowntimeRepository, ILaborRepository, IGoalRepository,
    IShiftRepository, IResourceRepository, IWorkOrderRepository,
)
from mes_app.models.production_run import ProductionRun
from mes_app.models.ledger import ManufacturingLedger
from mes_app.models.downtime import Downtime
from mes_app.models.labor import Labor
from mes_app.models.kpi import Goal
from mes_app.models.shift import Shift
from mes_app.models.resource import Resource
from mes_app.models.work_order import WorkOrder
from mes_app.models.work_order_line import WorkOrderLine
from mes_app.core.enums import WorkOrderLineType, WorkOrderLineStatus

class SQLAlchemyProductionRunRepository(IProductionRunRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_id(self, run_id: uuid.UUID, company_id: Optional[str] = None) -> Any:
        query = select(ProductionRun).where(ProductionRun.id == run_id)
        if company_id:
            query = query.where(ProductionRun.company_id == company_id)
        res = await self.db.execute(query)
        return res.scalars().first()

class SQLAlchemyManufacturingLedgerRepository(IManufacturingLedgerRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, **kwargs) -> Any:
        entry = ManufacturingLedger(**kwargs)
        self.db.add(entry)
        return entry

    async def get_total_produced(self, run_id: uuid.UUID, company_id: Optional[str] = None) -> float:
        query = select(func.sum(ManufacturingLedger.qty)).where(
            and_(ManufacturingLedger.production_run_id == run_id, 
                 ManufacturingLedger.transaction_type == "SCAN")
        )
        if company_id:
            query = query.where(ManufacturingLedger.company_id == company_id)
        res = await self.db.execute(query)
        return float(res.scalar() or 0.0)
    
    async def get_produced_in_slot(self, run_id: uuid.UUID, start: datetime, end: datetime, company_id: Optional[str] = None) -> float:
        query = select(func.sum(ManufacturingLedger.qty)).where(
            and_(ManufacturingLedger.production_run_id == run_id,
                 ManufacturingLedger.created_at >= start,
                 ManufacturingLedger.created_at < end)
        )
        if company_id:
            query = query.where(ManufacturingLedger.company_id == company_id)
        res = await self.db.execute(query)
        return float(res.scalar() or 0.0)

class SQLAlchemyDowntimeRepository(IDowntimeRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_run_id(self, run_id: uuid.UUID, company_id: Optional[str] = None) -> List[Any]:
        query = select(Downtime).where(Downtime.production_run_id == run_id)
        if company_id:
            query = query.where(Downtime.company_id == company_id)
        res = await self.db.execute(query)
        return list(res.scalars().all())
    
    async def get_active_downtime(self, run_id: uuid.UUID, company_id: Optional[str] = None) -> Optional[Any]:
        query = select(Downtime).where(
            and_(Downtime.production_run_id == run_id, 
                 Downtime.status.in_(["OPEN", "RESPONDED"]))
        )
        if company_id:
            query = query.where(Downtime.company_id == company_id)
        res = await self.db.execute(query)
        return res.scalars().first()

class SQLAlchemyLaborRepository(ILaborRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_run_id(self, run_id: uuid.UUID, company_id: Optional[str] = None) -> List[Any]:
        query = select(Labor).where(Labor.production_run_id == run_id)
        if company_id:
            query = query.where(Labor.company_id == company_id)
        res = await self.db.execute(query)
        return list(res.scalars().all())
    
    async def get_active_count_at(self, run_id: uuid.UUID, timestamp: datetime, company_id: Optional[str] = None) -> int:
        query = select(func.count(Labor.id)).where(
            and_(Labor.production_run_id == run_id,
                 Labor.clock_in <= timestamp,
                 (Labor.clock_out == None) | (Labor.clock_out > timestamp))
        )
        if company_id:
            query = query.where(Labor.company_id == company_id)
        res = await self.db.execute(query)
        return res.scalar() or 0

class SQLAlchemyGoalRepository(IGoalRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_hour_meta(self, resource_id: uuid.UUID, hour: int, company_id: Optional[str] = None) -> int:
        query = select(Goal.target_qty).where(
            and_(Goal.resource_id == resource_id, Goal.hour_of_day == hour)
        )
        if company_id:
            query = query.where(Goal.company_id == company_id)
        res = await self.db.execute(query)
        return res.scalar() or 0

class SQLAlchemyShiftRepository(IShiftRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_id(self, shift_id: uuid.UUID, company_id: Optional[str] = None) -> Optional[Any]:
        query = select(Shift).where(Shift.id == shift_id)
        if company_id:
            query = query.where(Shift.company_id == company_id)
        res = await self.db.execute(query)
        return res.scalars().first()
    
    async def get_active_shifts_by_criteria(self, **kwargs) -> List[Any]:
        query = select(Shift).where(Shift.is_active == True)
        if "resource_id" in kwargs:
            query = query.where(Shift.resource_id == kwargs["resource_id"])
        if "facility_id" in kwargs:
            query = query.where(Shift.facility_id == kwargs["facility_id"])
        if "company_id" in kwargs:
            query = query.where(Shift.company_id == kwargs["company_id"])
        
        res = await self.db.execute(query)
        return list(res.scalars().all())

class SQLAlchemyResourceRepository(IResourceRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_id(self, resource_id: uuid.UUID, company_id: Optional[str] = None) -> Optional[Any]:
        query = select(Resource).where(Resource.id == resource_id)
        if company_id:
            query = query.where(Resource.company_id == company_id)
        res = await self.db.execute(query)
        return res.scalars().first()


class SQLAlchemyWorkOrderRepository(IWorkOrderRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def increment_manufactured_quantity(
        self,
        work_order_id: uuid.UUID,
        qty: Decimal,
        company_id: uuid.UUID,
    ) -> None:
        wo = await self.db.get(WorkOrder, work_order_id)
        if not wo:
            return

        int_qty = int(qty)
        wo.manufactured_quantity = (wo.manufactured_quantity or 0) + int_qty

        if wo.status == "DRAFT":
            wo.status = "IN_PROGRESS"
        if wo.manufactured_quantity >= wo.order_quantity:
            wo.status = "COMPLETED"

        result = await self.db.execute(
            select(WorkOrderLine).where(
                WorkOrderLine.work_order_id == work_order_id,
                WorkOrderLine.line_type == WorkOrderLineType.PLANNED_OUTPUT,
                WorkOrderLine.company_id == company_id,
            )
        )
        output_line = result.scalar_one_or_none()
        if output_line:
            output_line.actual_quantity = output_line.actual_quantity + qty
            if output_line.actual_quantity >= output_line.planned_quantity:
                output_line.status = WorkOrderLineStatus.COMPLETED
            elif output_line.actual_quantity > 0:
                output_line.status = WorkOrderLineStatus.IN_PROGRESS
