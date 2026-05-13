from typing import List, Optional, Any
import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from wms_app.dependencies import get_db, get_current_user
from common.security.auth_payload import TokenPayload
from common.responses import ApiResponse
from wms_app.models.location import Location
from wms_app.schemas.location import LocationCreate, LocationResponse
from common.security.dependencies import require_scope
from sqlalchemy import func
from wms_app.models.inventory_movement import InventoryMovement
from wms_app.models.item import Item
from wms_app.application.transfer_stock_handler import TransferStockHandler, TransferStockCommand
from pydantic import BaseModel

class TransferRequest(BaseModel):
    product_id: str
    source_location_id: str
    target_location_id: str
    quantity: Decimal
    warehouse_id: str

router = APIRouter()

@router.post("/", response_model=None, summary="Create Location")
async def create_location(
    location_in: LocationCreate,
    db: AsyncSession = Depends(get_db),
    token_data: TokenPayload = Depends(require_scope(["wms:write"]))
) -> Any:
    """
    Creates a new physical location in the warehouse.
    """
    try:
        # Validate duplicates
        stmt = select(Location).where(

            Location.warehouse_id == location_in.warehouse_id,
            Location.zone_code == location_in.zone_code,
            Location.bin_code == location_in.bin_code
        )
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Location already exists in this warehouse.")

        db_location = Location(
            **location_in.model_dump(),
            company_id=token_data.company_id
        )
        db.add(db_location)
        await db.commit()
        await db.refresh(db_location)

        return ApiResponse(
            data=LocationResponse.model_validate(db_location),
            message="Location created successfully."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=None, summary="List Locations")
async def list_locations(
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Optional warehouse ID filter"),
    db: AsyncSession = Depends(get_db),
    token_data: TokenPayload = Depends(require_scope(["wms:read"]))
) -> Any:
    """
    Lists physical locations, optionally filtered by warehouse.
    """
    stmt = select(Location)
    if warehouse_id:
        stmt = stmt.where(Location.warehouse_id == warehouse_id)
    
    result = await db.execute(stmt)
    locations = result.scalars().all()

    return ApiResponse(
        data=[LocationResponse.model_validate(loc) for loc in locations],
        message="Locations listed successfully."
    )

@router.get("/{id}/inventory", response_model=None, summary="Get Location Inventory Projection")
async def get_location_inventory(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token_data: TokenPayload = Depends(require_scope(["wms:read"]))
) -> Any:
    """
    Standard Gold Projection: select(Stock.product_id, Product.sku, Stock.quantity).
    Only what the operator needs to see on their scanner.
    """
    stmt = select(
        InventoryMovement.product_id,
        Item.sku,
        func.sum(InventoryMovement.quantity).label("quantity")
    ).join(Item, Item.id == InventoryMovement.product_id).where(
        InventoryMovement.location_id == id
    ).group_by(InventoryMovement.product_id, Item.sku)
    
    result = await db.execute(stmt)
    items = result.all()
    
    return ApiResponse(
        data=[{"product_id": str(r.product_id), "sku": r.sku, "quantity": Decimal(str(r.quantity))} for r in items],
        message="Inventory projection fetched."
    )

@router.post("/transfer", response_model=None, summary="Atomic Stock Transfer")
async def transfer_stock(
    req: TransferRequest,
    db: AsyncSession = Depends(get_db),
    token_data: TokenPayload = Depends(require_scope(["wms:write"]))
) -> Any:
    handler = TransferStockHandler(db)
    command = TransferStockCommand(
        product_id=req.product_id,
        source_location_id=req.source_location_id,
        target_location_id=req.target_location_id,
        quantity=req.quantity,
        warehouse_id=req.warehouse_id
    )
    res = await handler.handle(command)
    await db.commit()
    return ApiResponse(data=res, message="Stock transferred atomically.")
