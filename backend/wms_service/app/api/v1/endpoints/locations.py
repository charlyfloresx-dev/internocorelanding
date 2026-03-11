from typing import List, Optional, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from common.security.auth_payload import TokenPayload
from common.responses import ApiResponse
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationResponse

router = APIRouter()

@router.post("/", response_model=None)
async def create_location(
    location_in: LocationCreate,
    db: AsyncSession = Depends(get_db),
    token_data: TokenPayload = Depends(get_current_user)
) -> Any:
    """
    Crea una nueva ubicación física en el almacén.
    """
    try:
        # Validar duplicados
        stmt = select(Location).where(
            Location.company_id == token_data.company_id,
            Location.warehouse_id == location_in.warehouse_id,
            Location.zone_code == location_in.zone_code,
            Location.bin_code == location_in.bin_code
        )
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="La ubicación ya existe en este almacén.")

        db_location = Location(
            **location_in.model_dump(),
            company_id=token_data.company_id
        )
        db.add(db_location)
        await db.commit()
        await db.refresh(db_location)

        return ApiResponse(
            data=LocationResponse.from_orm(db_location),
            message="Ubicación creada exitosamente"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=None)
async def list_locations(
    warehouse_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    token_data: TokenPayload = Depends(get_current_user)
) -> Any:
    """
    Lista las ubicaciones físicas, opcionalmente filtradas por almacén.
    """
    stmt = select(Location).where(Location.company_id == token_data.company_id)
    if warehouse_id:
        stmt = stmt.where(Location.warehouse_id == warehouse_id)
    
    result = await db.execute(stmt)
    locations = result.scalars().all()

    return ApiResponse(
        data=[LocationResponse.from_orm(loc) for loc in locations],
        message="Ubicaciones listadas exitosamente"
    )
