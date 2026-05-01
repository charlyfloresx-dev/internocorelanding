from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from mes_app.dependencies import get_db, get_current_company
from mes_app.models.resource import Resource
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid
from typing import List, Optional

router = APIRouter()

class ResourceRead(BaseModel):
    id: uuid.UUID = Field(description="Unique resource ID")
    code: str = Field(description="Unique code identifying the line/cell")
    name: str = Field(description="Human readable name")
    description: Optional[str] = Field(None, description="Detailed description of the resource")
    active: bool = Field(True, description="Whether the resource is active")
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )

@router.get("/", response_model=List[ResourceRead])
async def get_resources(
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los recursos (Líneas/Celdas) pertenecientes a la compañía.
    """
    query = select(Resource).where(Resource.company_id == company_id)
    result = await db.execute(query)
    return result.scalars().all()
