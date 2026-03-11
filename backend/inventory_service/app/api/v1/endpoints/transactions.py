import uuid
import httpx
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.inventory import InventoryLevel, InventoryTransaction, TransactionType
from app.schemas.inventory import InventoryTransactionCreate, InventoryTransactionRead
from app.services.inventory import InventoryTransactionService
from common.responses import ApiResponse

from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload

router = APIRouter()

@router.post("/transactions", response_model=ApiResponse[InventoryTransactionRead], status_code=status.HTTP_201_CREATED)
async def create_transaction(
    request: Request,
    stmt: InventoryTransactionCreate,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    print(f"[*] INVENTORY_SERVICE received stmt: {stmt.model_dump()}")
    
    # El token ya fue validado por SubscriptionGuard
    company_id = token.company_id
    user_id = token.sub
    trace_id = token.correlation_id or uuid.uuid4()
    module_token = token.token # we might need to store the raw token in TokenPayload if not there

    # Delegaci\u00f3n de la l\u00f3gica estructurada al Unit Of Work
    print(f"DEBUG: RECIBIDO COMENTARIO EN API: {stmt.comments}")
    import sys; sys.stdout.flush()
    transaction = await InventoryTransactionService.create_transaction(
        db=db,
        stmt=stmt,
        company_id=company_id,
        user_id=user_id,
        trace_id=trace_id,
        module_token=module_token
    )

    return ApiResponse(
        status="success",
        data=transaction,
        message="Transaction recorded successfully."
    )

@router.get("/transactions", response_model=ApiResponse[List[InventoryTransactionRead]])
async def get_transactions(
    request: Request,
    product_id: Optional[uuid.UUID] = None,
    warehouse_id: Optional[uuid.UUID] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    company_id_str = request.headers.get("X-Company-ID")
    if not company_id_str:
        raise HTTPException(status_code=400, detail="X-Company-ID header missing")
    
    company_id = uuid.UUID(company_id_str)
    
    transactions = await InventoryTransactionService.get_transactions(
        db=db,
        company_id=company_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        limit=limit,
        offset=offset
    )
    
    return ApiResponse(
        status="success",
        data=transactions,
        message="Transactions retrieved successfully."
    )
@router.get("/levels/{product_id}/{warehouse_id}")
async def get_stock_levels(
    product_id: uuid.UUID,
    warehouse_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
) -> Any:
    """
    Consulta los niveles de stock (Actual y Reservado) para un producto en un almacén.
    """
    query = select(InventoryLevel).where(
        InventoryLevel.company_id == token.company_id,
        InventoryLevel.product_id == product_id,
        InventoryLevel.warehouse_id == warehouse_id
    )
    result = await db.execute(query)
    level = result.scalar_one_or_none()
    
    if not level:
        return {
            "product_id": str(product_id),
            "warehouse_id": str(warehouse_id),
            "quantity": 0.0,
            "reserved_quantity": 0.0,
            "available_quantity": 0.0
        }
        
    return {
        "product_id": str(level.product_id),
        "warehouse_id": str(level.warehouse_id),
        "quantity": float(level.quantity),
        "reserved_quantity": float(level.reserved_quantity),
        "available_quantity": float(level.quantity) - float(level.reserved_quantity)
    }
