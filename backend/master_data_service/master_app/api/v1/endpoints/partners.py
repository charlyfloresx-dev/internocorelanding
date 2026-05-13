from fastapi import Security, APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid

from master_app.dependencies import get_db, get_current_user
from master_app.models.partner import Partner
from common.models.external_contact import ExternalContact
from master_app.schemas.partner import PartnerCreate, PartnerUpdate, PartnerResponse
from master_app.schemas.external_contact import ExternalContactResponse
from common.security.dependencies import require_scope
from common.responses import ApiResponse
from common.domain.entities.user_context import UserContext

router = APIRouter()

@router.get("/search", response_model=ApiResponse[List[PartnerResponse]])
async def search_partners(
    q: str = Query(..., min_length=2),
    type: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Security(require_scope, scopes=["master_data:read"])
):
    """
    Busca socios comerciales por nombre o código.
    """
    stmt = select(Partner).where(
        Partner.company_id == current_user.company_id,
        Partner.is_active == True
    )
    
    if q:
        stmt = stmt.where(
            (Partner.name.ilike(f"%{q}%")) | 
            (Partner.code.ilike(f"%{q}%"))
        )
    
    if type:
        stmt = stmt.where(Partner.type == type)
    
    result = await session.execute(stmt)
    partners = result.scalars().all()
    
    return ApiResponse(
        status="success", 
        data=partners, 
        message=f"Found {len(partners)} partners"
    )

@router.get("/contacts/search", response_model=ApiResponse[List[ExternalContactResponse]])
async def search_external_contacts(
    q: str = Query(..., min_length=2),
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Security(require_scope, scopes=["master_data:read"])
):
    """
    Busca contactos externos de proveedores por nombre o correo.
    """
    stmt = select(ExternalContact).where(
        ExternalContact.company_id == current_user.company_id
    )
    if q:
        stmt = stmt.where(
            (ExternalContact.full_name.ilike(f"%{q}%")) | 
            (ExternalContact.email.ilike(f"%{q}%"))
        )
    
    result = await session.execute(stmt)
    contacts = result.scalars().all()
    
    return ApiResponse(
        status="success", 
        data=[ExternalContactResponse.model_validate(c) for c in contacts], 
        message="External contacts found"
    )

@router.get("", response_model=ApiResponse[List[PartnerResponse]])
async def get_partners(
    type: Optional[str] = Query(None, description="Filter by partner type (CUSTOMER, SUPPLIER, BOTH)"),
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Security(require_scope, scopes=["master_data:read"])
):
    stmt = select(Partner).where(
        Partner.company_id == current_user.company_id,
        Partner.is_active == True
    )
    
    if type:
        stmt = stmt.where(Partner.type == type)
    
    result = await session.execute(stmt)
    partners = result.scalars().all()
    
    return ApiResponse(status="success", data=partners, message="Partners retrieved successfully")

@router.post("", response_model=ApiResponse[PartnerResponse], status_code=status.HTTP_201_CREATED)
async def create_partner(
    partner_in: PartnerCreate,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Security(require_scope, scopes=["master_data:write"])
):
    # Check if code already exists for this company
    stmt = select(Partner).where(
        Partner.company_id == current_user.company_id,
        Partner.code == partner_in.code
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Partner with code {partner_in.code} already exists")

    new_partner = Partner(
        **partner_in.model_dump(),
        company_id=current_user.company_id,
        tenant_id=current_user.company_id, # Simplified for now
        created_by=current_user.user_id,
        version_id=1
    )
    
    session.add(new_partner)
    await session.commit()
    await session.refresh(new_partner)
    
    return ApiResponse(status="success", data=new_partner, message="Partner created successfully")

@router.get("/{partner_id}", response_model=ApiResponse[PartnerResponse])
async def get_partner(
    partner_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Security(require_scope, scopes=["master_data:read"])
):
    stmt = select(Partner).where(
        Partner.id == partner_id,
        Partner.company_id == current_user.company_id
    )
    result = await session.execute(stmt)
    p = result.scalar_one_or_none()
    
    if not p:
        raise HTTPException(status_code=404, detail="Partner not found")
        
    return ApiResponse(status="success", data=p, message="Partner retrieved successfully")

@router.patch("/{partner_id}", response_model=ApiResponse[PartnerResponse])
async def update_partner(
    partner_id: uuid.UUID,
    partner_in: PartnerUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Security(require_scope, scopes=["master_data:write"])
):
    # Industrial Authorization Guard: Only Admins can edit master data
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can modify Business Partners"
        )

    stmt = select(Partner).where(
        Partner.id == partner_id,
        Partner.company_id == current_user.company_id
    )
    result = await session.execute(stmt)
    p = result.scalar_one_or_none()
    
    if not p:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    update_data = partner_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(p, key, value)
    
    await session.commit()
    await session.refresh(p)
    
    return ApiResponse(status="success", data=p, message="Partner updated successfully")

@router.delete("/{partner_id}", response_model=ApiResponse[bool])
async def delete_partner(
    partner_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Security(require_scope, scopes=["master_data:write"])
):
    # Industrial Authorization Guard: Only Admins can delete master data
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can remove Business Partners"
        )

    stmt = select(Partner).where(
        Partner.id == partner_id,
        Partner.company_id == current_user.company_id
    )
    result = await session.execute(stmt)
    p = result.scalar_one_or_none()
    
    if not p:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    # Soft delete
    p.is_active = False
    await session.commit()
    
    return ApiResponse(status="success", data=True, message="Partner soft-deleted successfully")
