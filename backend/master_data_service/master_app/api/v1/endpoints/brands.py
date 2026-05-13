import uuid
from typing import List

from fastapi import Security, APIRouter, Depends, HTTPException, status
from common.exceptions import ConflictException
from common.security.dependencies import require_scope
from common.responses import ApiResponse
from master_app.schemas.product_brand import BrandRead, BrandCreate, BrandUpdate
from master_app.services.product_brand_service import ProductBrandService
from master_app.dependencies import get_current_user, get_brand_service
from common.domain.entities.user_context import UserContext

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[BrandRead]], summary="List Brands")
async def list_brands(
    current_user: UserContext = Security(require_scope, scopes=["master_data:read"]),
    service: ProductBrandService = Depends(get_brand_service)
):
    brands = await service.get_brands(
        company_id=current_user.company_id,
        group_id=current_user.group_id
    )
    return ApiResponse(status="success", data=brands, message="Brands retrieved successfully")

@router.post("/", response_model=ApiResponse[BrandRead], summary="Create Brand")
async def create_brand(
    brand_in: BrandCreate,
    current_user: UserContext = Security(require_scope, scopes=["master_data:write"]),
    service: ProductBrandService = Depends(get_brand_service)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can create Brands"
        )
    company_id = current_user.company_id
    try:
        brand = await service.create_brand(brand_in=brand_in, company_id=company_id)
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    
    return ApiResponse(status="success", data=brand, message="Brand created successfully")

@router.get("/{brand_id}", response_model=ApiResponse[BrandRead], summary="Get Brand")
async def get_brand(
    brand_id: uuid.UUID,
    current_user: UserContext = Security(require_scope, scopes=["master_data:read"]),
    service: ProductBrandService = Depends(get_brand_service)
):
    brand = await service.get_brand_by_id(
        brand_id=brand_id, 
        company_id=current_user.company_id,
        group_id=current_user.group_id
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return ApiResponse(status="success", data=brand, message="Brand retrieved successfully")

@router.patch("/{brand_id}", response_model=ApiResponse[BrandRead], summary="Update Brand")
async def update_brand(
    brand_id: uuid.UUID,
    brand_in: BrandUpdate,
    current_user: UserContext = Security(require_scope, scopes=["master_data:write"]),
    service: ProductBrandService = Depends(get_brand_service)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can modify Brands"
        )
    company_id = current_user.company_id
    try:
        brand = await service.update_brand(brand_id, company_id, brand_in)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found or permission denied")
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
        
    return ApiResponse(status="success", data=brand, message="Brand updated successfully")

@router.delete("/{brand_id}", response_model=ApiResponse[None], summary="Delete Brand")
async def delete_brand(
    brand_id: uuid.UUID,
    current_user: UserContext = Security(require_scope, scopes=["master_data:write"]),
    service: ProductBrandService = Depends(get_brand_service)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can remove Brands"
        )
    company_id = current_user.company_id
    await service.delete_brand(brand_id, company_id)
    return ApiResponse(status="success", data=None, message="Brand deleted successfully")
