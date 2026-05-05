from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
import uuid

from wms_app.core.database import get_db
from wms_app.schemas.sales_order import SalesOrderCreate, SalesOrderRead
from wms_app.application.commands import CreateSalesOrderCommand
from wms_app.application.handlers import CreateSalesOrderHandler
from common.context import request_context

from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload

router = APIRouter()

@router.post("/", response_model=SalesOrderRead)
async def create_sales_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_in: SalesOrderCreate,
    token: TokenPayload = Depends(SubscriptionGuard(module_code="WMS_CORE"))
) -> Any:
    """
    Crea una nueva Orden de Venta.
    Inicia el proceso atómico de descuento de stock.
    """
    ctx = request_context.get()
    if not ctx or not ctx.company_id:
        raise HTTPException(status_code=400, detail="Company ID missing in context")
    
    command = CreateSalesOrderCommand(
        folio=order_in.folio,
        product_id=str(order_in.product_id),
        warehouse_id=str(order_in.warehouse_id),
        uom_id=str(order_in.uom_id),
        quantity=order_in.quantity,
        comments=order_in.observations
    )
    
    handler = CreateSalesOrderHandler(db)
    try:
        order = await handler.handle(command, ctx.company_id)
        return order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
