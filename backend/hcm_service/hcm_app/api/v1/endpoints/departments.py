from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

from hcm_app.core.database import get_db
from hcm_app.models.department import Department
from hcm_app.schemas.department import DepartmentRead
from common.responses import ApiResponse
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[DepartmentRead]])
async def list_departments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    List all departments for the current company.
    Supports pagination and filtering by status.
    """
    try:
        stmt = select(Department).where(Department.company_id == token.company_id)
        
        if is_active is not None:
            stmt = stmt.where(Department.is_active == is_active)
            
        stmt = stmt.offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        departments = result.scalars().all()
        
        return ApiResponse(
            status="success",
            data=[DepartmentRead.model_validate(d) for d in departments],
            message="Departments retrieved successfully."
        )
    except Exception as e:
        logger.exception("Error listing departments")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing departments: {str(e)}"
        )
