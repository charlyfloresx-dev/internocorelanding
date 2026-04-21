import uuid
from typing import List
from fastapi import APIRouter, Depends, Header, Request, Response
from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
from inventory_app.dependencies.repositories import get_inventory_repository
from inventory_app.schemas.variant_search import (
    VariantSearchResult, VariantSearchResponse, 
    InventorySearchRow, InventorySearchResponse
)
# from common.responses import ApiResponse

router = APIRouter()

@router.get("/variants", response_model=List[VariantSearchResult])
async def search_variants(
    q: str,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: uuid.UUID = Header(...)
):
    results = await repo.search_items_and_variants(q, x_company_id)
    return results

@router.get("/products/search", response_model=List[InventorySearchRow])
async def search_inventory_products(
    q: str,
    warehouse_id: uuid.UUID,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: uuid.UUID = Header(...),
    request: Request = None,
    response: Response = None
):
    trace_id = (request.headers.get("x-correlation-id") or str(uuid.uuid4())) if request else str(uuid.uuid4())
    if response:
        response.headers["X-Trace-ID"] = trace_id

    results = await repo.search_inventory_products(
        query=q,
        company_id=x_company_id,
        warehouse_id=warehouse_id
    )
    # Convert entities to dicts for proper serialization in JSONResponse
    return [r.model_dump() if hasattr(r, 'model_dump') else vars(r) for r in results]

@router.get("/products/quick-catalog")
async def get_quick_catalog(
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: uuid.UUID = Header(...)
):
    """
    Returns a lightweight list of all known products/variants for the company.
    Used for frontend hydration (Registry Cache).
    """
    return await repo.get_quick_catalog(x_company_id)
