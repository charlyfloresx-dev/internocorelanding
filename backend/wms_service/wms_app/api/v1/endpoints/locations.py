from typing import List, Optional, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from wms_app.dependencies import get_db, get_current_user
from common.security.auth_payload import TokenPayload
from common.responses import ApiResponse
from wms_app.models.location import Location
from wms_app.schemas.location import LocationCreate, LocationResponse
from common.security.dependencies import require_scope

router = APIRouter()

@router.post("/", response_model=None, summary="Create Location", dependencies=[Depends(require_scope(["wms:write"]))])
async def create_location(
    location_in: LocationCreate,
    db: AsyncSession = Depends(get_db),
    token_data: TokenPayload = Depends(get_current_user)
) -> Any:
    """
    Creates a new physical location in the warehouse.
    """
    try:
        # Validate duplicates
        stmt = select(Location).where(
            Location.company_id == token_data.company_id,
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
            data=LocationResponse.from_orm(db_location),
            message="Location created successfully."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=None, summary="List Locations", dependencies=[Depends(require_scope(["wms:read"]))])
async def list_locations(
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Optional warehouse ID filter"),
    db: AsyncSession = Depends(get_db),
    token_data: TokenPayload = Depends(get_current_user)
) -> Any:
    """
    Lists physical locations, optionally filtered by warehouse.
    """
    stmt = select(Location).where(Location.company_id == token_data.company_id)
    if warehouse_id:
        stmt = stmt.where(Location.warehouse_id == warehouse_id)
    
    result = await db.execute(stmt)
    locations = result.scalars().all()

    return ApiResponse(
        data=[LocationResponse.from_orm(loc) for loc in locations],
        message="Locations listed successfully."
    )
