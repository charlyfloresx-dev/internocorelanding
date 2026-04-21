import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from common.exceptions import ConflictException


from master_app.schemas.uom import UOMRead, UOMCreate, UOMUpdate
from master_app.services.uom_service import UOMService
from common.responses import ApiResponse
from master_app.dependencies import get_current_user, get_uom_service
from common.domain.entities.user_context import UserContext

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[UOMRead]], summary="List Units of Measure")
async def list_uoms(
    current_user: UserContext = Depends(get_current_user),
    service: UOMService = Depends(get_uom_service),
):
    """
    Returns a list of all Units of Measure (UOM) for the current company.
    """
    uoms = await service.get_uoms_by_company(
        company_id=current_user.company_id,
        group_id=current_user.group_id
    )
    return ApiResponse(
        status="success",
        data=uoms,
        message="Units of measure retrieved successfully"
    )

@router.post("/", response_model=ApiResponse[UOMRead], summary="Create Unit of Measure")
async def create_uom(
    uom_in: UOMCreate,
    current_user: UserContext = Depends(get_current_user),
    service: UOMService = Depends(get_uom_service),
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can create UOMs"
        )
    company_id = current_user.company_id
    try:
        uom = await service.create_uom(uom_in=uom_in, company_id=company_id)
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    
    return ApiResponse(
        status="success",
        data=uom,
        message="Unit of measure created successfully"
    )

@router.get("/{uom_id}", response_model=ApiResponse[UOMRead], summary="Get Unit of Measure")
async def get_uom(
    uom_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    service: UOMService = Depends(get_uom_service),
):
    uom = await service.get_uom_by_id(
        uom_id=uom_id, 
        company_id=current_user.company_id,
        group_id=current_user.group_id
    )
    if not uom:
        raise HTTPException(status_code=404, detail="Unit of measure not found")
    
    return ApiResponse(
        status="success",
        data=uom,
        message="Unit of measure retrieved successfully"
    )

@router.patch("/{uom_id}", response_model=ApiResponse[UOMRead], summary="Update Unit of Measure")
async def update_uom(
    uom_id: uuid.UUID,
    uom_in: UOMUpdate,
    current_user: UserContext = Depends(get_current_user),
    service: UOMService = Depends(get_uom_service),
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can modify UOMs"
        )
    company_id = current_user.company_id
    uom = await service.get_uom_by_id(uom_id=uom_id, company_id=company_id)
    if not uom:
        raise HTTPException(status_code=404, detail="Unit of measure not found")
    
    try:
        uom = await service.update_uom(db_obj=uom, uom_in=uom_in)
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )

    return ApiResponse(
        status="success",
        data=uom,
        message="Unit of measure updated successfully"
    )

@router.delete("/{uom_id}", response_model=ApiResponse[None], summary="Delete Unit of Measure")
async def delete_uom(
    uom_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    service: UOMService = Depends(get_uom_service),
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can remove UOMs"
        )
    company_id = current_user.company_id
    uom = await service.get_uom_by_id(uom_id=uom_id, company_id=company_id)
    if not uom:
        raise HTTPException(status_code=404, detail="Unit of measure not found")
    
    await service.delete_uom(db_obj=uom)
    
    return ApiResponse(
        status="success",
        data=None,
        message="Unit of measure deleted successfully"
    )
