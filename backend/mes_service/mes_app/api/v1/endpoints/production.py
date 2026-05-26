from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

from common.infrastructure.database import get_db
from common.security.dependencies import require_scope
from common.exceptions import NotFoundException
from mes_app.dependencies import get_current_company
from mes_app.models.scrap_entry import ScrapEntry
from mes_app.models.production_run import ProductionRun

router = APIRouter()


class ScrapCreate(BaseModel):
    production_run_id: uuid.UUID = Field(description="ProductionRun where scrap occurred")
    qty: int = Field(gt=0, description="Number of scrapped units")
    reason_code: str = Field(max_length=50, description="Reason code (e.g. DIMENSIONAL, COSMETIC, WELD)")
    operator_id: str = Field(max_length=50, description="Internal ID of the reporting operator")

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ScrapRead(BaseModel):
    id: uuid.UUID
    production_run_id: uuid.UUID
    quantity: int
    reason_code: str
    operator_id: str | None

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


@router.post(
    "/scrap",
    response_model=ScrapRead,
    dependencies=[Depends(require_scope(["mes:write"]))],
    summary="Registrar scrap en una corrida de producción",
)
async def create_scrap(
    request: ScrapCreate,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """
    Persiste una entrada de scrap vinculada a un ProductionRun.
    Verifica que el run pertenece a la compañía del JWT (Muro de Hierro).
    """
    result = await db.execute(
        select(ProductionRun).where(
            ProductionRun.id == request.production_run_id,
            ProductionRun.company_id == company_id,
        )
    )
    if not result.scalar_one_or_none():
        raise NotFoundException("ProductionRun not found for this company")

    scrap = ScrapEntry(
        production_run_id=request.production_run_id,
        quantity=request.qty,
        reason_code=request.reason_code,
        operator_id=request.operator_id,
        company_id=company_id,
    )
    db.add(scrap)
    await db.commit()
    await db.refresh(scrap)
    return scrap
