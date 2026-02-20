import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.inventory_service import InventoryService
from app.schemas.inventory import MasterDataSyncPayload, SyncResult
from app.dependencies import get_db, get_current_user # ✅ Correcto (ajusta según tu estructura real)
from common.responses import ApiResponse

router = APIRouter()

@router.post("/sync-initial", response_model=ApiResponse[SyncResult])
async def sync_initial_inventory(
    payload: MasterDataSyncPayload,
    db: AsyncSession = Depends(get_db),
    service: InventoryService = Depends(),
    current_user: dict = Depends(get_current_user)
):
    """
    Recibe el payload del Master Data Service y puebla la base de datos local del WMS.
    """
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="Contexto de compañía no encontrado.")

    result = await service.sync_initial_data(db, uuid.UUID(str(company_id)), payload)
    
    return ApiResponse(data=result, message="Inventory synced successfully")