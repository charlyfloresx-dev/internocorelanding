import uuid
from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload
from app.core.config import settings

from app.services.inventory_service import InventoryService
from app.schemas.inventory import MasterDataSyncPayload, SyncResult
from app.dependencies import get_db, get_current_user # ✅ Correcto (ajusta según tu estructura real)
from common.responses import ApiResponse

router = APIRouter()

# Dependencia del Guardia de Suscripción (Pilotaje)
inventory_guard = SubscriptionGuard("inventory_core")

@router.post("/sync-initial", 
             response_model=ApiResponse[SyncResult],
             dependencies=[Depends(inventory_guard)])
async def sync_initial_inventory(
    payload: MasterDataSyncPayload,
    db: AsyncSession = Depends(get_db),
    service: InventoryService = Depends(),
    # current_user ya no se necesita inyectar si solo lo usa el guardia, 
    # pero a menudo se requiere para el transaction_id o auditoría.
    token_data: TokenPayload = Depends(get_current_user) 
):
    """
    Recibe el payload del Master Data Service y puebla la base de datos local del WMS.
    """
    company_id = token_data.company_id

    result = await service.sync_initial_data(db, uuid.UUID(str(company_id)), payload)
    
    return ApiResponse(data=result, message="Inventory synced successfully")