from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional
import uuid

from app.core.database import get_db
from app.application.commands import DispatchSalesOrderCommand
from app.application.handlers import DispatchSalesOrderHandler
from app.application.queries import GetProductPriceAndStockQuery, GetProductPriceAndStockHandler
from app.schemas.sales_order import SalesOrderRead

from common.context import request_context
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload

router = APIRouter()

@router.get("/price-stock")
async def get_price_and_stock(
    product_id: str,
    warehouse_id: str,
    quantity: float = 1.0,
    channel_code: Optional[str] = None,
    customer_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="WMS_CORE"))
) -> Any:
    """
    Consulta el precio efectivo (Jerárquico) y el stock de un producto.
    """
    ctx = request_context.get()
    query = GetProductPriceAndStockQuery(
        product_id=product_id, 
        warehouse_id=warehouse_id,
        quantity=quantity,
        channel_code=channel_code,
        customer_id=customer_id
    )
    handler = GetProductPriceAndStockHandler(db)
    
    try:
        return await handler.handle(query, ctx.company_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/dispatch", response_model=SalesOrderRead)
async def dispatch_sales_order(
    command: DispatchSalesOrderCommand,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="WMS_CORE"))
) -> Any:
    """
    Ejecuta el despacho de una orden de venta.
    Asienta el movimiento en el inventario y marca la orden como enviada.
    """
    ctx = request_context.get()
    handler = DispatchSalesOrderHandler(db)
    
    try:
        order = await handler.handle(command, ctx.company_id)
        return order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
