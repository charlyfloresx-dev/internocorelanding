import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from mes_app.dependencies import get_db, get_current_company, get_labor_allocation_repo
from mes_app.models.production_run import ProductionRun
from mes_app.models.labor_allocation import LaborAllocation
from mes_app.schemas.labor_assignment import (
    BulkAssignRequest,
    BulkAssignResponse,
    LaborAssignmentRead,
)
from common.security.dependencies import require_scope
from common.exceptions import NotFoundException

router = APIRouter()


@router.post(
    "/assign",
    response_model=BulkAssignResponse,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def assign_labor(
    request: BulkAssignRequest,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """
    Asigna colaboradores en masa a un ProductionRun.
    Limpia asignaciones anteriores y crea las nuevas en una sola transacción atómica
    para evitar condiciones de carrera (Race Conditions). Enforces multi-tenant isolation.
    """
    # 1. Validar existencia y pertenencia del ProductionRun
    query = select(ProductionRun).where(
        and_(
            ProductionRun.id == request.production_run_id,
            ProductionRun.company_id == company_id,
        )
    )
    result = await db.execute(query)
    run = result.scalars().first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production run not found or access denied"
        )

    assigned_count = 0
    removed_count = 0
    warnings = []

    # 2. Transacción atómica
    async with db.begin_nested():
        # Obtener y borrar asignaciones previas
        delete_query = delete(LaborAllocation).where(
            and_(
                LaborAllocation.production_run_id == request.production_run_id,
                LaborAllocation.company_id == company_id,
            )
        )
        del_res = await db.execute(delete_query)
        removed_count = del_res.rowcount

        # Insertar nuevas asignaciones
        for asm in request.assignments:
            allocation = LaborAllocation(
                production_run_id=request.production_run_id,
                collaborator_id=asm.collaborator_id,
                role=asm.role,
                shift_id=run.shift_id,
                company_id=company_id,
            )
            db.add(allocation)
            assigned_count += 1

    await db.commit()

    return BulkAssignResponse(
        assigned=assigned_count,
        removed=removed_count,
        warnings=warnings,
    )


@router.get(
    "/assignments/{production_run_id}",
    response_model=List[LaborAssignmentRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_assignments(
    production_run_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene el listado de colaboradores pre-asignados a un ProductionRun."""
    # Enforce tenant check on ProductionRun first
    run_query = select(ProductionRun).where(
        and_(
            ProductionRun.id == production_run_id,
            ProductionRun.company_id == company_id,
        )
    )
    run_res = await db.execute(run_query)
    if not run_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production run not found or access denied"
        )

    query = select(LaborAllocation).where(
        and_(
            LaborAllocation.production_run_id == production_run_id,
            LaborAllocation.company_id == company_id,
        )
    )
    res = await db.execute(query)
    return list(res.scalars().all())


@router.delete(
    "/assignments/{allocation_id}",
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def delete_assignment(
    allocation_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Remueve una asignación individual."""
    query = delete(LaborAllocation).where(
        and_(
            LaborAllocation.id == allocation_id,
            LaborAllocation.company_id == company_id,
        )
    )
    res = await db.execute(query)
    await db.commit()

    if res.rowcount == 0:
        raise NotFoundException("Assignment allocation not found")

    return {"message": "Assignment removed successfully"}
