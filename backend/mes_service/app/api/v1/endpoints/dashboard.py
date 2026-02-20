from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.services.kpi_service import KPIService
import uuid

from common.responses import ApiResponse

router = APIRouter()

@router.get("/oee/{resource_result_id}")
async def get_oee(resource_result_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Retorna OEE. NotFoundException manejada por handler común.
    """
    service = KPIService(db)
    return await service.calculate_oee(resource_result_id)

@router.get("/graphic/{resource_result_id}")
async def get_graphic(resource_result_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Retorna gráfico de tendencias.
    """
    service = KPIService(db)
    return await service.get_resource_graphic(resource_result_id)
