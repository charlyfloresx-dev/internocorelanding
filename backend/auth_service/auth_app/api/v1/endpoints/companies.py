from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from auth_app.dependencies import get_db
from auth_app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from common.responses import ApiResponse
from auth_app.models import Company
from common.repository import BaseRepository

router = APIRouter()

@router.post(
    "/", 
    response_model=ApiResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_company(
    request: Request,
    company_in: CompanyCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new company.
    """
    # No usamos company_id en el repo porque estamos creando la compañía raíz
    repo = BaseRepository(Company, db)
    
    existing = await repo.get_by_name(company_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company with this name already exists"
        )

    db_company = await repo.create(company_in)
    await db.commit()
    await db.refresh(db_company)
    
    return ApiResponse(
        status="success",
        data=CompanyResponse.model_validate(db_company),
        message="Company created successfully",
    )

@router.get(
    "/{company_id}", 
    response_model=ApiResponse
)
async def read_company(
    request: Request,
    company_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a single company by ID.
    """
    repo = BaseRepository(Company, db)
    company = await repo.get(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return ApiResponse(
        status="success",
        data=CompanyResponse.model_validate(company),
        message="Company retrieved successfully",
    )

@router.get(
    "/", 
    response_model=ApiResponse
)
async def read_companies(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of companies.
    """
    repo = BaseRepository(Company, db)
    companies = await repo.list(skip=skip, limit=limit)
    return ApiResponse(
        status="success",
        data=[CompanyResponse.model_validate(c) for c in companies],
        message="Companies retrieved successfully",
    )

@router.put(
    "/{company_id}", 
    response_model=ApiResponse
)
async def update_company(
    request: Request,
    company_id: int,
    company_in: CompanyUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing company.
    """
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    if company_in.name is not None:
        # Check if the new name already exists for another company
        existing_company_query = select(Company).where(Company.name == company_in.name, Company.id != company_id)
        existing_company_result = await db.execute(existing_company_query)
        if existing_company_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company with this name already exists"
            )
        company.name = company_in.name
    
    await db.commit()
    await db.refresh(company)
    return ApiResponse(
        status="success",
        data=CompanyResponse.model_validate(company),
        message="Company updated successfully",
    )

@router.delete(
    "/{company_id}", 
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse
)
async def delete_company(
    request: Request,
    company_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a company.
    """
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    await db.delete(company)
    await db.commit()
    return ApiResponse(
        status="success",
        data=None,
        message="Company deleted successfully",
    )
