import uuid
import logging
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from inventory_app.db.session import get_db
from inventory_app.dependencies.repositories import get_inventory_repository
from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
from inventory_app.schemas.customs import CustomsBalanceReportResponse
from common.responses import ApiResponse, ApiMeta
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/balances",
    # response_model=CustomsBalanceReportResponse, # Disabled to allow internal dict with meta
    summary="[Anexo 24] Reporte de Saldos por Pedimento",
    description=(
        "Obtiene el estado actual del inventario con respaldo aduanal. "
        "Agrupa por SKU y Pedimento, calculando el saldo residual (available_quantity) "
        "y detectando riesgos de vencimiento legal (IMMEX)."
    )
)
async def get_customs_balances(
    request: Request,
    query: Optional[str] = Query(None, alias="q", description="Buscar por SKU, Producto o Pedimento"),
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Filtrar por un almacén específico"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: IInventoryRepository = Depends(get_inventory_repository),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    """
    Exposición del reporte de cumplimiento Anexo 24 con soporte para paginación y búsqueda.
    """
    try:
        report_data, total_count = await repo.get_customs_balances(
            company_id=token.company_id,
            warehouse_id=warehouse_id,
            limit=limit,
            offset=offset,
            query=query
        )
        
        # We return a dict that matches ApiResponse structure to bypass middleware re-wrapping
        # but including the critical total_count at the sibling level for the Frontend Interceptor.
        return {
            "status": "success",
            "data": report_data,
            "total_count": total_count,
            "message": "Operation completed",
            "meta": {
                "trace_id": getattr(request.state, "transaction_id", str(uuid.uuid4())),
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "count": len(report_data),
                    "total": total_count
                }
            }
        }
    except Exception as e:
        logger.error(f"Error generating customs balance report: {str(e)}")
        raise e
