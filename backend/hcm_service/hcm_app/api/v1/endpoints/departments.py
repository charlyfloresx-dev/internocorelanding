import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

from hcm_app.core.database import get_db
from hcm_app.models.department import Department
from hcm_app.schemas.department import DepartmentRead, DepartmentCreate, DepartmentUpdate
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
    """List all departments for the current company."""
    try:
        stmt = select(Department).where(Department.company_id == token.company_id)
        if is_active is not None:
            stmt = stmt.where(Department.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit).order_by(Department.code)

        result = await db.execute(stmt)
        departments = result.scalars().all()

        return ApiResponse(
            status="success",
            data=[DepartmentRead.model_validate(d) for d in departments],
            message="Departments retrieved successfully."
        )
    except Exception as e:
        logger.exception("Error listing departments")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/", response_model=ApiResponse[DepartmentRead], status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """Create a new department for the current company. Code must be unique per company."""
    existing = (await db.execute(
        select(Department).where(
            Department.company_id == token.company_id,
            Department.code == payload.code.upper(),
        )
    )).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Department with code '{payload.code}' already exists."
        )

    department = Department(
        id=uuid.uuid4(),
        company_id=token.company_id,
        tenant_id=token.company_id,
        name=payload.name,
        code=payload.code.upper(),
        description=payload.description,
        is_active=payload.is_active,
        version_id=1,
        created_by=token.sub,
    )
    db.add(department)
    await db.commit()
    await db.refresh(department)

    logger.info("Department created: %s (%s) company=%s", department.code, department.name, token.company_id)
    return ApiResponse(
        status="success",
        data=DepartmentRead.model_validate(department),
        message=f"Department '{department.code}' created successfully."
    )


@router.patch("/{department_id}", response_model=ApiResponse[DepartmentRead])
async def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """Partial update of a department. Only provided fields are changed."""
    department = (await db.execute(
        select(Department).where(
            Department.id == department_id,
            Department.company_id == token.company_id,
        )
    )).scalar_one_or_none()

    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")

    updates = payload.model_dump(exclude_unset=True)

    if "code" in updates:
        new_code = updates["code"].upper()
        conflict = (await db.execute(
            select(Department).where(
                Department.company_id == token.company_id,
                Department.code == new_code,
                Department.id != department_id,
            )
        )).scalar_one_or_none()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Department with code '{new_code}' already exists."
            )
        updates["code"] = new_code

    for field, value in updates.items():
        setattr(department, field, value)

    department.updated_by = token.sub
    await db.commit()
    await db.refresh(department)

    return ApiResponse(
        status="success",
        data=DepartmentRead.model_validate(department),
        message=f"Department '{department.code}' updated successfully."
    )


@router.delete("/{department_id}", response_model=ApiResponse)
async def delete_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """Soft-delete a department (sets is_active=False). Preserves historical collaborator data."""
    department = (await db.execute(
        select(Department).where(
            Department.id == department_id,
            Department.company_id == token.company_id,
        )
    )).scalar_one_or_none()

    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")

    department.is_active = False
    department.updated_by = token.sub
    await db.commit()

    return ApiResponse(
        status="success",
        data=None,
        message=f"Department '{department.code}' deactivated."
    )
