import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.schemas.product_category import CategoryRead, CategoryCreate, CategoryUpdate
from app.services.product_category_service import ProductCategoryService
from common.responses import ApiResponse
from app.dependencies import get_current_user
from common.domain.entities.user_context import UserContext
from app.db.session import get_db

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[CategoryRead]], summary="Listar Categorías")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    company_id = current_user.company_id
    categories = await ProductCategoryService.get_categories(db, company_id=company_id)
    return ApiResponse(status="success", data=categories, message="Categorías recuperadas")

@router.post("/", response_model=ApiResponse[CategoryRead], summary="Crear Categoría")
async def create_category(
    category_in: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    company_id = current_user.company_id
    try:
        category = await ProductCategoryService.create_category(db, category_in=category_in, company_id=company_id)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código de categoría duplicado")
    
    return ApiResponse(status="success", data=category, message="Categoría creada")

@router.get("/{category_id}", response_model=ApiResponse[CategoryRead], summary="Obtener Categoría")
async def get_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    company_id = current_user.company_id
    category = await ProductCategoryService.get_category_by_id(db, category_id=category_id, company_id=company_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return ApiResponse(status="success", data=category, message="Categoría recuperada")

@router.patch("/{category_id}", response_model=ApiResponse[CategoryRead], summary="Actualizar Categoría")
async def update_category(
    category_id: uuid.UUID,
    category_in: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    company_id = current_user.company_id
    category = await ProductCategoryService.get_category_by_id(db, category_id=category_id, company_id=company_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Prevent modification of Global records by tenants
    if category.company_id is None:
        raise HTTPException(status_code=403, detail="No se pueden modificar registros globales")

    try:
        category = await ProductCategoryService.update_category(db, db_obj=category, category_in=category_in)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código duplicado")
        
    return ApiResponse(status="success", data=category, message="Categoría actualizada")

@router.delete("/{category_id}", response_model=ApiResponse[None], summary="Eliminar Categoría")
async def delete_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    company_id = current_user.company_id
    category = await ProductCategoryService.get_category_by_id(db, category_id=category_id, company_id=company_id)
    if not category or category.company_id is None: # Protect globals
        raise HTTPException(status_code=404, detail="Categoría no encontrada o es global")
    
    await ProductCategoryService.delete_category(db, db_obj=category)
    return ApiResponse(status="success", data=None, message="Categoría eliminada")