from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid

from master_app.dependencies import get_db, get_current_user
from master_app.models.movement_concept import MovementConcept
from master_app.schemas.concept import ConceptCreate, ConceptUpdate, ConceptResponse
from common.enums import MovementType
from common.domain.entities.user_context import UserContext
from common.responses import ApiResponse

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[ConceptResponse]])
async def get_concepts(
    type: Optional[MovementType] = Query(None, description="Filtrar por tipo de movimiento (ENTRADA, SALIDA, TRASPASO)"),
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    company_id = current_user.company_id
    stmt = select(MovementConcept).filter(MovementConcept.company_id == company_id)
    if type:
        stmt = stmt.filter(MovementConcept.type == type)
    
    result = await session.execute(stmt)
    concepts = result.scalars().all()
    
    return ApiResponse(status="success", data=concepts, message="Concepts retrieved successfully")

@router.post("", response_model=ApiResponse[ConceptResponse], status_code=status.HTTP_201_CREATED)
async def create_concept(
    concept_in: ConceptCreate,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can create Concepts"
        )

    new_concept = MovementConcept(
        **concept_in.model_dump(),
        company_id=current_user.company_id,
        tenant_id=current_user.company_id,
        created_by=current_user.user_id,
        version_id=1
    )
    
    session.add(new_concept)
    await session.commit()
    await session.refresh(new_concept)
    
    return ApiResponse(status="success", data=new_concept, message="Concept created successfully")

@router.patch("/{concept_id}", response_model=ApiResponse[ConceptResponse])
async def update_concept(
    concept_id: uuid.UUID,
    concept_in: ConceptUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can modify Concepts"
        )

    stmt = select(MovementConcept).where(
        MovementConcept.id == concept_id,
        MovementConcept.company_id == current_user.company_id
    )
    result = await session.execute(stmt)
    c = result.scalar_one_or_none()
    
    if not c:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    update_data = concept_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(c, key, value)
    
    await session.commit()
    await session.refresh(c)
    
    return ApiResponse(status="success", data=c, message="Concept updated successfully")

@router.delete("/{concept_id}", response_model=ApiResponse[bool])
async def delete_concept(
    concept_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    if not any(role in ["admin", "owner", "superadmin"] for role in current_user.role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ACC_ERR: Only administrators can remove Concepts"
        )

    stmt = select(MovementConcept).where(
        MovementConcept.id == concept_id,
        MovementConcept.company_id == current_user.company_id
    )
    result = await session.execute(stmt)
    c = result.scalar_one_or_none()
    
    if not c:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    c.is_active = False
    await session.commit()
    
    return ApiResponse(status="success", data=True, message="Concept soft-deleted successfully")
