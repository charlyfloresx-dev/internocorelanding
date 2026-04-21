from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid

from master_app.dependencies import get_db, get_current_user
from master_app.models.warehouse import Warehouse
from master_app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from common.domain.entities.user_context import UserContext
from common.responses import ApiResponse

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[WarehouseResponse]])
async def get_warehouses(
    company_id: Optional[uuid.UUID] = Query(None, description="Optional: specific company filter"),
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    # Default to current tenant if not specified
    target_company = company_id or current_user.company_id
    
    print(f"[DEBUG] Fetching warehouses for company: {target_company}")

    stmt = select(Warehouse).where(
        Warehouse.company_id == target_company,
        Warehouse.is_active == True
    )
    
    result = await session.execute(stmt)
    warehouses = result.scalars().all()
    
    return ApiResponse(status="success", data=warehouses, message="Warehouses retrieved successfully")

@router.post("", response_model=ApiResponse[WarehouseResponse], status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    warehouse_in: WarehouseCreate,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    # Industrial Authorization Guard: Only Admins can create master data
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can create Warehouses"
        )

    new_warehouse = Warehouse(
        **warehouse_in.model_dump(),
        company_id=current_user.company_id,
        tenant_id=current_user.company_id,
        created_by=current_user.user_id,
        version_id=1
    )
    
    session.add(new_warehouse)
    await session.commit()
    await session.refresh(new_warehouse)
    
    return ApiResponse(status="success", data=new_warehouse, message="Warehouse created successfully")

@router.get("/{warehouse_id}")
async def get_warehouse(
    warehouse_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    stmt = select(Warehouse).filter(
        Warehouse.id == warehouse_id,
        Warehouse.company_id == current_user.company_id
    )
    result = await session.execute(stmt)
    w = result.scalar_one_or_none()
    
    if not w:
        raise HTTPException(status_code=404, detail="Warehouse not found")
        
    return ApiResponse(status="success", data=w, message="Warehouse retrieved successfully")

@router.patch("/{warehouse_id}", response_model=ApiResponse[WarehouseResponse])
async def update_warehouse(
    warehouse_id: uuid.UUID,
    warehouse_in: WarehouseUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can modify Warehouses"
        )

    stmt = select(Warehouse).where(
        Warehouse.id == warehouse_id,
        Warehouse.company_id == current_user.company_id
    )
    result = await session.execute(stmt)
    w = result.scalar_one_or_none()
    
    if not w:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    update_data = warehouse_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(w, key, value)
    
    await session.commit()
    await session.refresh(w)
    
    return ApiResponse(status="success", data=w, message="Warehouse updated successfully")

@router.delete("/{warehouse_id}", response_model=ApiResponse[bool])
async def delete_warehouse(
    warehouse_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can remove Warehouses"
        )

    stmt = select(Warehouse).where(
        Warehouse.id == warehouse_id,
        Warehouse.company_id == current_user.company_id
    )
    result = await session.execute(stmt)
    w = result.scalar_one_or_none()
    
    if not w:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    w.is_active = False
    await session.commit()
    
    return ApiResponse(status="success", data=True, message="Warehouse soft-deleted successfully")
