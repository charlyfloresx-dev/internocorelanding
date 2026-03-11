from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.services.product_service import ProductService
from app.schemas.product import ProductCreate, ProductRead
from app.dependencies import get_current_user
# Asumimos que get_db está en dependencies o db.session. Usamos dependencies por convención.
from app.dependencies import get_db 

router = APIRouter()

def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    return ProductService(db)

@router.get("/", response_model=List[ProductRead])
async def get_products(
    current_user = Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    # FIX: current_user viene como dict desde el token JWT
    group_id = None
    if isinstance(current_user, dict):
        company_id = current_user.get("company_id")
        group_id = current_user.get("group_id")
    else:
        company_id = current_user.company_id
        # group_id might not be in the user model if it's legacy, so check context
        ctx = request_context.get()
        group_id = ctx.group_id if ctx else None
        
    return await service.get_products_by_company(UUID(str(company_id)), group_id)

@router.post("/", response_model=ProductRead)
async def create_product(
    product_in: ProductCreate,
    current_user = Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    if isinstance(current_user, dict):
        company_id = current_user.get("company_id")
        user_id = current_user.get("sub")
    else:
        company_id = current_user.company_id
        user_id = current_user.id

    return await service.create_product(product_in, UUID(str(company_id)), UUID(str(user_id)))

@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID,
    current_user = Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    if isinstance(current_user, dict):
        company_id = current_user.get("company_id")
    else:
        company_id = current_user.company_id
        
    return await service.get_product_by_id(product_id, UUID(str(company_id)))