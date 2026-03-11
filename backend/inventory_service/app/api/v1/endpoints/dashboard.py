import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from app.domain.repositories.inventory_repository import IInventoryRepository
from app.dependencies.repositories import get_inventory_repository
from app.schemas.dashboard import StockDashboardRow, ForceReleaseCmd
from common.responses import ApiResponse
from common.security.auth_payload import TokenPayload

router = APIRouter()

def require_owner_role(request: Request):
    """Dependency to enforce OWNER or ADMIN role for emergency actions."""
    token_data: TokenPayload = getattr(request.state, "user_token", None)
    if not token_data or token_data.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Access Denied: Requires OWNER or ADMIN role.")
    return token_data

@router.get("/stock", response_model=ApiResponse[List[StockDashboardRow]])
async def get_dashboard_stock(
    request: Request,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: uuid.UUID = Header(...)
):
    """
    Returns the consolidated view of physical and transit stock.
    Accessible by all valid tenant users.
    """
    rows = await repo.get_dashboard_stock(x_company_id)
    return ApiResponse(data=rows)

@router.post("/force-release", response_model=ApiResponse, dependencies=[Depends(require_owner_role)])
async def force_release_reservation(
    cmd: ForceReleaseCmd,
    request: Request,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: uuid.UUID = Header(...)
):
    """
    [EMERGENCY] Releases stuck reserved_quantity.
    Requires OWNER/ADMIN role.
    """
    try:
        stock = await repo.force_release_orphan(
            warehouse_id=cmd.warehouse_id,
            product_id=cmd.product_id,
            release_qty=cmd.release_qty,
            company_id=x_company_id
        )
        return ApiResponse(
            message="Reservation forcibly released", 
            data={"available_quantity": stock.available_quantity, "reserved_quantity": stock.reserved_quantity}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
