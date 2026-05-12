from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from common.infrastructure.database import get_db
from common.context import request_context
import uuid

# Domain Interfaces
from mes_app.domain.repositories.interfaces import (
    IProductionRunRepository, IManufacturingLedgerRepository,
    IDowntimeRepository, ILaborRepository, IGoalRepository,
    IShiftRepository, IResourceRepository, IWMSClient
)
from mes_app.domain.repositories.event_interfaces import (
    IProductionEventRepository, IProductionSessionRepository
)

# Infrastructure Implementations
from mes_app.infrastructure.repositories.sqlalchemy_repositories import (
    SQLAlchemyProductionRunRepository, SQLAlchemyManufacturingLedgerRepository,
    SQLAlchemyDowntimeRepository, SQLAlchemyLaborRepository, SQLAlchemyGoalRepository,
    SQLAlchemyShiftRepository, SQLAlchemyResourceRepository
)
from mes_app.infrastructure.repositories.event_repositories import (
    SQLAlchemyProductionEventRepository, SQLAlchemyProductionSessionRepository
)
from mes_app.infrastructure.clients.wms_adapter import SQLAlchemyWMSClient

async def get_current_company() -> uuid.UUID:
    ctx = request_context.get()
    if not ctx or not ctx.company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid company context required"
        )
    return ctx.company_id

# Repository Providers
def get_production_run_repo(db: AsyncSession = Depends(get_db)) -> IProductionRunRepository:
    return SQLAlchemyProductionRunRepository(db)

def get_ledger_repo(db: AsyncSession = Depends(get_db)) -> IManufacturingLedgerRepository:
    return SQLAlchemyManufacturingLedgerRepository(db)

def get_downtime_repo(db: AsyncSession = Depends(get_db)) -> IDowntimeRepository:
    return SQLAlchemyDowntimeRepository(db)

def get_labor_repo(db: AsyncSession = Depends(get_db)) -> ILaborRepository:
    return SQLAlchemyLaborRepository(db)

def get_goal_repo(db: AsyncSession = Depends(get_db)) -> IGoalRepository:
    return SQLAlchemyGoalRepository(db)

def get_event_repo(db: AsyncSession = Depends(get_db)) -> IProductionEventRepository:
    return SQLAlchemyProductionEventRepository(db)

def get_session_repo(db: AsyncSession = Depends(get_db)) -> IProductionSessionRepository:
    return SQLAlchemyProductionSessionRepository(db)

def get_shift_repo(db: AsyncSession = Depends(get_db)) -> IShiftRepository:
    return SQLAlchemyShiftRepository(db)

def get_resource_repo(db: AsyncSession = Depends(get_db)) -> IResourceRepository:
    return SQLAlchemyResourceRepository(db)

def get_wms_client() -> IWMSClient:
    return SQLAlchemyWMSClient()
