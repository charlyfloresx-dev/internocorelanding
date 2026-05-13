import uuid
from typing import Any, Dict
import typing
from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload
from wms_app.core.config import settings

from wms_app.services.wms_sync_service import WMSSyncService
from wms_app.schemas.inventory import MasterDataSyncPayload, SyncResult
from wms_app.domain.repositories.item_repository import IItemRepository
from wms_app.domain.interfaces.inventory_client import IInventoryClient
from wms_app.infrastructure.repositories.sqlalchemy_item_repository import SQLAlchemyItemRepository
from wms_app.infrastructure.clients.inventory_client import InventoryClient
from wms_app.dependencies import get_db, oauth2_scheme
from common.security.dependencies import require_scope
from common.responses import ApiResponse

router = APIRouter()

# Dependencia del Guardia de Suscripción (Pilotaje)
inventory_guard = SubscriptionGuard("inventory_core")

async def get_item_repository(db: AsyncSession = Depends(get_db)) -> IItemRepository:
    return SQLAlchemyItemRepository(db)

async def get_inventory_client() -> IInventoryClient:
    return InventoryClient()

@router.post("/sync-initial", 
             response_model=None,
             dependencies=[Depends(inventory_guard)])
async def sync_initial_inventory(
    payload: MasterDataSyncPayload,
    repo: IItemRepository = Depends(get_item_repository),
    inv_client: IInventoryClient = Depends(get_inventory_client),
    token_data: TokenPayload = Depends(require_scope(["wms:write"])),
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Recibe el payload del Master Data Service y puebla la base de datos local del WMS.
    """
    company_id = token_data.company_id
    service = WMSSyncService(repo, inv_client)

    result = await service.sync_initial_data(uuid.UUID(str(company_id)), payload, token)
    
    return ApiResponse(data=result, message="Inventory synced successfully")