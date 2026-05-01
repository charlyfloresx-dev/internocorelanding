from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from mes_app.dependencies import get_shift_repo, get_current_company
from mes_app.domain.repositories.interfaces import IShiftRepository
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid
from datetime import time
from typing import List, Optional

router = APIRouter()

class ShiftRead(BaseModel):
    id: uuid.UUID = Field(description="Unique shift ID")
    name: str = Field(description="Display name of the shift")
    start_time: time = Field(description="Official state time")
    end_time: time = Field(description="Official end time")
    is_overnight: bool = Field(description="True if shift crosses midnight")
    is_active: bool = Field(description="Status of the shift configuration")
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )

@router.get("/", response_model=List[ShiftRead])
async def get_shifts(
    company_id: uuid.UUID = Depends(get_current_company),
    shift_repo: IShiftRepository = Depends(get_shift_repo)
):
    """
    Lista todos los turnos configurados para la compañía.
    """
    return await shift_repo.get_active_shifts_by_criteria(company_id=company_id)
