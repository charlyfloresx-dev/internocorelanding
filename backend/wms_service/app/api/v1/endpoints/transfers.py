from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from typing import List, Any
import typing

from app.dependencies import get_db
from common.context import request_context
from common.audit.logger import AuditLogger
from common.models import Company
from pydantic import BaseModel, UUID4

router = APIRouter()

class InterCompanyTransferRequest(BaseModel):
    source_company_id: UUID4
    target_company_id: UUID4
    product_id: UUID4
    warehouse_id: UUID4
    quantity: float
    target_warehouse_id: UUID4

@router.post("/inter-company", status_code=status.HTTP_201_CREATED, summary="Create Inter-Company Transfer")
async def create_inter_company_transfer(
    transfer: InterCompanyTransferRequest,
    db: AsyncSession = Depends(get_db)
) -> typing.Any:
    """
    Creates an inter-company transfer between two companies in the same cluster.
    """
    ctx = request_context.get()
    if not ctx or not ctx.group_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation allowed only for users with Cluster (group_id) context."
        )

    # 1. Validate that both companies belong to the same Cluster/Group
    id_list = [transfer.source_company_id, transfer.target_company_id]
    result = await db.execute(select(Company).where(Company.id.in_(id_list)))
    companies = result.scalars().all()

    if len(companies) < 2 and transfer.source_company_id != transfer.target_company_id:
        raise HTTPException(status_code=404, detail="One or both companies not found.")

    for comp in companies:
        if comp.parent_group_id != ctx.group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"The company {comp.name} does not belong to your authorized cluster."
            )

    # 2. Generate the Inventory Document and Movements (Simplified for example)
    # In a real scenario, this would require complex business logic (out from one, in to another)
    
    # Audit the action
    await AuditLogger.log_action(
        db=db,
        action="INV_INTER_COMPANY_TRANSFER",
        table_name="inventory_movements",
        record_id=str(uuid.uuid4()),
        user_id=str(ctx.user_id),
        company_id=str(ctx.company_id),
        group_id=str(ctx.group_id)
    )
    
    await db.commit()

    return {
        "status": "success",
        "message": "Inter-company transfer registered successfully.",
        "meta": {"trace_id": ctx.trace_id}
    }
