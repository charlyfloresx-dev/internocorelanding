import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from master_app.services.sync_service import SyncService
from master_app.schemas.sync import MasterDataSyncResponse
from master_app.api.dependencies import get_db, get_current_user
from common.responses import ApiResponse

router = APIRouter()

@router.get("/all", response_model=ApiResponse[MasterDataSyncResponse])
async def sync_all_master_data(
    db: AsyncSession = Depends(get_db),
    service: SyncService = Depends(),
    current_user: dict = Security(require_scope, scopes=["master_data:read"])
):
    """
    Devuelve todos los productos y UOMs activos para hidratación inicial de otros servicios (WMS).
    """
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="Contexto de compañía no encontrado.")

    data = await service.get_all_master_data(db, uuid.UUID(str(company_id)))
    
    return ApiResponse(data=data, message="Master data sync payload generated successfully")
