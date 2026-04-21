from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid

from master_app.dependencies import get_db, get_current_user
from master_app.models.location import InventoryLocation
from master_app.schemas.location import (
    LocationCreate, 
    LocationResponse, 
    LocationCapacityResponse
)
from common.domain.entities.user_context import UserContext
from common.responses import ApiResponse

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[LocationResponse]])
async def get_locations(
    warehouse_id: Optional[uuid.UUID] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    stmt = select(InventoryLocation).where(
        InventoryLocation.company_id == current_user.company_id
    )
    if warehouse_id:
        stmt = stmt.where(InventoryLocation.warehouse_id == warehouse_id)
        
    result = await session.execute(stmt)
    locations = result.scalars().all()
    return ApiResponse(data=locations, message="Locations retrieved successfully")

@router.get("/{warehouse_id}/{location_code}/capacity", response_model=ApiResponse[LocationCapacityResponse])
async def get_location_capacity(
    warehouse_id: uuid.UUID,
    location_code: str,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    """
    [Phase 63] Ultra-fast capacity endpoint for Density Guard.
    Used by Inventory Service via MasterDataClient.
    """
    stmt = select(InventoryLocation).where(
        InventoryLocation.warehouse_id == warehouse_id,
        InventoryLocation.code == location_code,
        InventoryLocation.company_id == current_user.company_id
    )
    result = await session.execute(stmt)
    loc = result.scalar_one_or_none()
    
    if not loc:
        # Business Decision: If location is not defined, we assume 0 capacity (infinite)
        # or strict 0 (blocked). We'll return 0 so the Density Guard knows it's unrestricted.
        # However, for industrial standards, we return a virtual record.
        return ApiResponse(
            data=LocationCapacityResponse(
                location_id=uuid.uuid4(),
                code=location_code,
                max_capacity=0,
                warehouse_id=warehouse_id
            ),
            message="Location not found, assuming unrestricted capacity (0)"
        )

    return ApiResponse(
        data=LocationCapacityResponse(
            location_id=loc.id,
            code=loc.code,
            max_capacity=loc.max_capacity,
            warehouse_id=loc.warehouse_id
        ),
        message="Location capacity retrieved"
    )

@router.post("", response_model=ApiResponse[LocationResponse], status_code=status.HTTP_201_CREATED)
async def create_location(
    location_in: LocationCreate,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    # Industrial Authorization Guard
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can define structural locations"
        )

    new_location = InventoryLocation(
        **location_in.model_dump(),
        company_id=current_user.company_id,
        tenant_id=current_user.company_id
    )
    
    session.add(new_location)
    await session.commit()
    await session.refresh(new_location)
    
    return ApiResponse(data=new_location, message="Location created successfully")
