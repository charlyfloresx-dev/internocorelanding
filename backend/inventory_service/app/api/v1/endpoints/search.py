import uuid
from typing import List
from fastapi import APIRouter, Depends, Header
from app.domain.repositories.inventory_repository import IInventoryRepository
from app.dependencies.repositories import get_inventory_repository
from app.schemas.search import VariantSearchResponse
from common.responses import ApiResponse

router = APIRouter()

@router.get("/variants", response_model=VariantSearchResponse)
async def search_variants(
    q: str,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: uuid.UUID = Header(...)
):
    """
    Buscador de variantes para Typeahead.
    Busca por SKU, Marca o MPN.
    Resultados incluyen metadatos industriales (peso/volumen).
    """
    results = await repo.search_items_and_variants(q, x_company_id)
    return VariantSearchResponse(data=results)
