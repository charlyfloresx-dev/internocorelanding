from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from uuid import UUID

from inventory_app.db.session import get_db
from inventory_app.models.bom import BOM
from inventory_app.schemas.bom import BOMCreate, BOMUpdate, BOMRead
from common.responses import ApiResponse
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload

router = APIRouter()

@router.post("/", response_model=ApiResponse[BOMRead], status_code=status.HTTP_201_CREATED)
async def create_bom(
    stmt: BOMCreate,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    bom = BOM(
        parent_item_code=stmt.parent_item_code,
        component_item_code=stmt.component_item_code,
        quantity=stmt.quantity,
        uom=stmt.uom,
        level=stmt.level,
        is_active=stmt.is_active,
        company_id=token.company_id
    )
    db.add(bom)
    await db.commit()
    await db.refresh(bom)
    return ApiResponse(status="success", data=bom, message="BOM created successfully.")

@router.get("/", response_model=ApiResponse[List[BOMRead]])
async def list_boms(
    parent_item_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    query = select(BOM).where(BOM.company_id == token.company_id)
    if parent_item_code:
        query = query.where(BOM.parent_item_code == parent_item_code)
    
    result = await db.execute(query)
    boms = result.scalars().all()
    return ApiResponse(status="success", data=boms)

@router.patch("/{bom_id}", response_model=ApiResponse[BOMRead])
async def update_bom(
    bom_id: UUID,
    stmt: BOMUpdate,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    query = update(BOM).where(
        BOM.id == bom_id, 
        BOM.company_id == token.company_id
    ).values(**stmt.model_dump(exclude_unset=True)).returning(BOM)
    
    result = await db.execute(query)
    bom = result.scalar_one_or_none()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found.")
    
    await db.commit()
    return ApiResponse(status="success", data=bom, message="BOM updated successfully.")

@router.delete("/{bom_id}", response_model=ApiResponse)
async def delete_bom(
    bom_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    query = delete(BOM).where(
        BOM.id == bom_id, 
        BOM.company_id == token.company_id
    )
    result = await db.execute(query)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="BOM not found.")
    
    await db.commit()
    return ApiResponse(status="success", message="BOM deleted successfully.")
