import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.repositories.interfaces import (
    IProductionRunRepository, IManufacturingLedgerRepository, 
    IDowntimeRepository, ILaborRepository, IGoalRepository,
    IShiftRepository, IResourceRepository
)
from app.models.production_run import ProductionRun
from app.models.ledger import ManufacturingLedger
from app.models.downtime import Downtime
from app.models.labor import Labor
from app.models.kpi import Goal
from app.models.shift import Shift
from app.models.resource import Resource

class SQLAlchemyProductionRunRepository(IProductionRunRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_id(self, run_id: uuid.UUID) -> Any:
        return await self.db.get(ProductionRun, run_id)

class SQLAlchemyManufacturingLedgerRepository(IManufacturingLedgerRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, **kwargs) -> Any:
        entry = ManufacturingLedger(**kwargs)
        self.db.add(entry)
        return entry

    async def get_total_produced(self, run_id: uuid.UUID) -> float:
        query = select(func.sum(ManufacturingLedger.qty)).where(
            and_(ManufacturingLedger.production_run_id == run_id, 
                 ManufacturingLedger.transaction_type == "SCAN")
        )
        res = await self.db.execute(query)
        return float(res.scalar() or 0.0)
    
    async def get_produced_in_slot(self, run_id: uuid.UUID, start: datetime, end: datetime) -> float:
        query = select(func.sum(ManufacturingLedger.qty)).where(
            and_(ManufacturingLedger.production_run_id == run_id,
                 ManufacturingLedger.created_at >= start,
                 ManufacturingLedger.created_at < end)
        )
        res = await self.db.execute(query)
        return float(res.scalar() or 0.0)

class SQLAlchemyDowntimeRepository(IDowntimeRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_run_id(self, run_id: uuid.UUID) -> List[Any]:
        query = select(Downtime).where(Downtime.production_run_id == run_id)
        res = await self.db.execute(query)
        return list(res.scalars().all())
    
    async def get_active_downtime(self, run_id: uuid.UUID) -> Optional[Any]:
        query = select(Downtime).where(
            and_(Downtime.production_run_id == run_id, 
                 Downtime.status.in_(["OPEN", "RESPONDED"]))
        )
        res = await self.db.execute(query)
        return res.scalars().first()

class SQLAlchemyLaborRepository(ILaborRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_run_id(self, run_id: uuid.UUID) -> List[Any]:
        query = select(Labor).where(Labor.production_run_id == run_id)
        res = await self.db.execute(query)
        return list(res.scalars().all())
    
    async def get_active_count_at(self, run_id: uuid.UUID, timestamp: datetime) -> int:
        query = select(func.count(Labor.id)).where(
            and_(Labor.production_run_id == run_id,
                 Labor.clock_in <= timestamp,
                 (Labor.clock_out == None) | (Labor.clock_out > timestamp))
        )
        res = await self.db.execute(query)
        return res.scalar() or 0

class SQLAlchemyGoalRepository(IGoalRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_hour_meta(self, resource_id: uuid.UUID, hour: int) -> int:
        query = select(Goal.target_qty).where(
            and_(Goal.resource_id == resource_id, Goal.hour_of_day == hour)
        )
        res = await self.db.execute(query)
        return res.scalar() or 0

class SQLAlchemyShiftRepository(IShiftRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_id(self, shift_id: uuid.UUID) -> Optional[Any]:
        return await self.db.get(Shift, shift_id)
    
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
    async def get_by_id(self, resource_id: uuid.UUID) -> Optional[Any]:
        return await self.db.get(Resource, resource_id)
