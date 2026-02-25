import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.schemas.product_brand import BrandRead, BrandCreate, BrandUpdate
from app.services.product_brand_service import ProductBrandService
from common.responses import ApiResponse
from app.dependencies import get_current_user
from common.models.user_context import UserContext
from app.db.session import get_db

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[BrandRead]], summary="Listar Marcas")
async def list_brands(
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    company_id = current_user.company_id
    brands = await ProductBrandService.get_brands(db, company_id=company_id)
    return ApiResponse(status="success", data=brands, message="Marcas recuperadas")

@router.post("/", response_model=ApiResponse[BrandRead], summary="Crear Marca")
async def create_brand(
    brand_in: BrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    company_id = current_user.company_id
    try:
        brand = await ProductBrandService.create_brand(db, brand_in=brand_in, company_id=company_id)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código de marca duplicado")
    
    return ApiResponse(status="success", data=brand, message="Marca creada")

@router.get("/{brand_id}", response_model=ApiResponse[BrandRead], summary="Obtener Marca")
async def get_brand(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    company_id = current_user.company_id
    brand = await ProductBrandService.get_brand_by_id(db, brand_id=brand_id, company_id=company_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return ApiResponse(status="success", data=brand, message="Marca recuperada")

@router.patch("/{brand_id}", response_model=ApiResponse[BrandRead], summary="Actualizar Marca")
async def update_brand(
    brand_id: uuid.UUID,
    brand_in: BrandUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    company_id = current_user.company_id
    brand = await ProductBrandService.get_brand_by_id(db, brand_id=brand_id, company_id=company_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    
    if brand.company_id is None:
        raise HTTPException(status_code=403, detail="No se pueden modificar registros globales")

    try:
        brand = await ProductBrandService.update_brand(db, db_obj=brand, brand_in=brand_in)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código duplicado")
        
    return ApiResponse(status="success", data=brand, message="Marca actualizada")

@router.delete("/{brand_id}", response_model=ApiResponse[None], summary="Eliminar Marca")
async def delete_brand(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    company_id = current_user.company_id
    brand = await ProductBrandService.get_brand_by_id(db, brand_id=brand_id, company_id=company_id)
    if not brand or brand.company_id is None:
        raise HTTPException(status_code=404, detail="Marca no encontrada o es global")
    
    await ProductBrandService.delete_brand(db, db_obj=brand)
    return ApiResponse(status="success", data=None, message="Marca eliminada")