import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from common.exceptions import ConflictException

from app.schemas.product_category import CategoryRead, CategoryCreate, CategoryUpdate
from app.services.product_category_service import ProductCategoryService
from common.responses import ApiResponse
from app.dependencies import get_current_user, get_category_service
from common.domain.entities.user_context import UserContext

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[CategoryRead]], summary="List Categories")
async def list_categories(
    current_user: UserContext = Depends(get_current_user),
    service: ProductCategoryService = Depends(get_category_service)
):
    company_id = current_user.company_id
    categories = await service.get_categories(company_id=company_id)
    return ApiResponse(status="success", data=categories, message="Categories retrieved successfully")

@router.post("/", response_model=ApiResponse[CategoryRead], summary="Create Category")
async def create_category(
    category_in: CategoryCreate,
    current_user: UserContext = Depends(get_current_user),
    service: ProductCategoryService = Depends(get_category_service)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can create Categories"
        )
    company_id = current_user.company_id
    try:
        category = await service.create_category(category_in=category_in, company_id=company_id)
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    
    return ApiResponse(status="success", data=category, message="Category created successfully")

@router.get("/{category_id}", response_model=ApiResponse[CategoryRead], summary="Get Category")
async def get_category(
    category_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    service: ProductCategoryService = Depends(get_category_service)
):
    company_id = current_user.company_id
    category = await service.get_category_by_id(category_id=category_id, company_id=company_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return ApiResponse(status="success", data=category, message="Category retrieved successfully")

@router.patch("/{category_id}", response_model=ApiResponse[CategoryRead], summary="Update Category")
async def update_category(
    category_id: uuid.UUID,
    category_in: CategoryUpdate,
    current_user: UserContext = Depends(get_current_user),
    service: ProductCategoryService = Depends(get_category_service)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can modify Categories"
        )
    company_id = current_user.company_id
    try:
        category = await service.update_category(category_id, company_id, category_in)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found or permission denied")
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
        
    return ApiResponse(status="success", data=category, message="Category updated successfully")

@router.delete("/{category_id}", response_model=ApiResponse[None], summary="Delete Category")
async def delete_category(
    category_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    service: ProductCategoryService = Depends(get_category_service)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can remove Categories"
        )
    company_id = current_user.company_id
    await service.delete_category(category_id, company_id)
    return ApiResponse(status="success", data=None, message="Category deleted successfully")
