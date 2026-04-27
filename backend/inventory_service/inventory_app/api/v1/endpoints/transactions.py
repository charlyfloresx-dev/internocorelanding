import uuid
import httpx
import logging
from typing import List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from inventory_app.db.session import get_db
from inventory_app.models.inventory import InventoryLevel, InventoryTransaction, TransactionType
from inventory_app.schemas.inventory import InventoryTransactionCreate, InventoryTransactionRead, InventoryDocumentCreate, StockRelocationCreate
from inventory_app.services.inventory import InventoryTransactionService
from inventory_app.services.density_guard_audit import run_density_guard_audit # Phase 64
from inventory_app.domain.entities.inventory_item import DocumentDetailEntity
from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
from inventory_app.dependencies.repositories import get_inventory_service, get_inventory_repository
from common.responses import ApiResponse
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload
from common.security.idempotency import idempotent
from common.security.limiter import limiter

router = APIRouter()
logger = logging.getLogger(__name__)


async def _notify_admin_new_document(
    company_id: str,
    folio: str,
    doc_type: str,
    origin: str,
    destination: str,
    items_count: int,
    total_amount: float,
    doc_id: str = None
):
    """
    Background task to notify ADMIN users on new inventory document.
    """
    try:
        from notification_app.services.notification_service import NotificationService
        from notification_app.models.notification import NotificationCategory, NotificationPriority
        from common.infrastructure.database import AsyncSessionLocal
        import uuid

        async with AsyncSessionLocal() as db:
            svc = NotificationService(db)
            
            # Formatear tipo para humanos
            type_clean = str(doc_type).lower()
            type_desc = "Entrada" if "in" in type_clean else "Salida" if "out" in type_clean else "Movimiento"
            
            await svc.notify_role(
                company_id=uuid.UUID(company_id),
                role_name="admin",
                title=f"📦 {type_desc} — {folio}",
                message=(
                    f"{type_desc} en {origin} con {items_count} partida(s). "
                    f"Total: ${total_amount:,.2f}"
                ),
                category=NotificationCategory.INVENTORY,
                priority=NotificationPriority.MEDIUM,
                action_url=f"/inventory/documents/{doc_id}" if doc_id else "/inventory/documents"
            )
            await db.commit()
            logger.info(f"🔔 Admin notified for document {folio}")
    except Exception as e:
        logger.warning(f"⚠️ NOTIFY_ADMIN_FAILED (non-critical): {e}")

@router.post("/documents", response_model=ApiResponse)
@idempotent()
@limiter.limit("20/minute")
async def create_document(
    request: Request,
    doc: InventoryDocumentCreate,
    background_tasks: BackgroundTasks,
    service: InventoryTransactionService = Depends(get_inventory_service),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
    client_request_id: Optional[str] = None
):
    """
    Batch endpoint to create multiple inventory transactions under a single folio/document.
    """
    # 1. Process items/transactions
    results = []
    total_weight = 0
    total_amount = 0
    
    for i, item in enumerate(doc.items):
        item_request_id = f"{client_request_id}:{i}" if client_request_id else None
        
        stmt = InventoryTransactionCreate(
            product_id=item.product_id,
            uom_id=item.uom_id,
            warehouse_id=doc.warehouse_id,
            transaction_type=doc.type,
            concept_id=doc.concept_id,
            quantity_change=item.quantity,
            weight=item.weight,
            unit_cost=item.unit_price,
            target_warehouse_id=doc.target_warehouse_id,
            reference_id=doc.correlation_id,
            comments=doc.notes,
            location=item.location
        )
        
        try:
            tx = await service.create_transaction(
                stmt=stmt,
                company_id=token.company_id,
                user_id=token.sub,
                trace_id=doc.correlation_id,
                module_token=token.token,
                client_request_id=item_request_id,
                role=token.role,
                home_warehouse_id=token.wid,
                is_supervisor=token.is_supervisor
            )
        except ValueError as e:
            if "ERR_WAREHOUSE_LOCK" in str(e):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        # [PHASE 64] Silently Audit in Background
        if tx.location:
             background_tasks.add_task(
                 run_density_guard_audit,
                 warehouse_id=doc.warehouse_id,
                 location_code=tx.location,
                 quantity_moved=tx.quantity,
                 movement_id=tx.id,
                 company_id=token.company_id
             )

        results.append(tx)
        total_weight += tx.weight
        if tx.price:
            total_amount += (tx.price.amount * tx.quantity)
        else:
            logger.warning(f"TX_PRICE_MISSING: Transaction {tx.id} has no price.")

    # 2. Persist Document Metadata for Dashboard/Listing
    folio_id = str(doc.correlation_id)[:5].upper()
    
    # Enrichment: Get warehouse name from Master Data
    origin_name = "Almacén Central"
    try:
        warehouse_data = await service.md_client.get_warehouse(doc.warehouse_id, token.company_id)
        if warehouse_data:
            origin_name = warehouse_data.get("name") or warehouse_data.get("code") or origin_name
    except Exception as e:
        logger.error(f"MD_WAREHOUSE_ENRICHMENT_FAILED: {str(e)}")

    destination_name = doc.external_entity or "N/A"
    
    # Enrichment: If external_entity is a UUID, try to get the Partner Name
    if doc.external_entity:
        try:
            # Check if it's a valid UUID
            potential_uuid = uuid.UUID(doc.external_entity)
            partner_data = await service.md_client.get_partner(potential_uuid, token.company_id)
            if partner_data:
                destination_name = partner_data.get("name") or partner_data.get("code") or destination_name
        except (ValueError, Exception) as e:
            # Not a UUID or failed search, keep original
            pass

    doc_entity = {
        "id": doc.correlation_id,
        "folio": f"DOC-{folio_id}",
        "document_type": doc.type,
        "status": "PROCESSED",
        "origin_name": origin_name,
        "destination_name": destination_name,
        "total_items": len(results),
        "total_weight": float(total_weight),
        "total_amount": float(total_amount),
        "total_currency": results[0].price.currency if results else "MXN",
        "concept_id": doc.concept_id,
        "external_reference": str(doc.correlation_id)
    }
    
    try:
        await service.repository.create_inventory_document(doc_entity, token.company_id)
        # 3. CRITICAL: Commit all changes (Movements + Document)
        await service.repository.session.commit()
    except Exception as e:
        logging.error(f"DOC_METADATA_FAILED: {str(e)}", exc_info=True)
        # Rollback and raise to reveal the issue
        await service.repository.session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during document creation: {str(e)}")

    # 4. [NOTIFICATIONS] Notificar al administrador en background (fire-and-forget)
    background_tasks.add_task(
        _notify_admin_new_document,
        company_id=token.company_id,
        folio=f"DOC-{folio_id}",
        doc_type=str(doc.type),
        origin=origin_name,
        destination=destination_name,
        items_count=len(results),
        total_amount=float(total_amount),
        doc_id=str(doc.correlation_id)
    )

    return ApiResponse(
        status="success",
        data={"id": f"DOC-{folio_id}", "items_count": len(results)},
        message="Document processed and transactions recorded."
    )


@router.post("/transactions", response_model=ApiResponse[InventoryTransactionRead], status_code=status.HTTP_201_CREATED)
@idempotent()
@limiter.limit("40/minute")
async def create_transaction(
    request: Request,
    stmt: InventoryTransactionCreate,
    background_tasks: BackgroundTasks,
    service: InventoryTransactionService = Depends(get_inventory_service),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
    client_request_id: Optional[str] = None
):
    print(f"[*] INVENTORY_SERVICE received stmt: {stmt.model_dump()}")
    
    # El token ya fue validado por SubscriptionGuard
    company_id = token.company_id
    user_id = token.sub
    trace_id = token.correlation_id or uuid.uuid4()
    module_token = token.token # we might need to store the raw token in TokenPayload if not there

    # Delegación de la lógica estructurada al Unit Of Work
    print(f"DEBUG: RECIBIDO COMENTARIO EN API: {stmt.comments}")
    import sys; sys.stdout.flush()
    try:
        transaction = await service.create_transaction(
            stmt=stmt,
            company_id=company_id,
            user_id=user_id,
            trace_id=trace_id,
            module_token=module_token,
            client_request_id=client_request_id,
            role=token.role,
            home_warehouse_id=token.wid,
            is_supervisor=token.is_supervisor
        )
    except ValueError as e:
        if "ERR_WAREHOUSE_LOCK" in str(e):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # [PHASE 64] Silently Audit in Background
    if transaction.location:
         background_tasks.add_task(
             run_density_guard_audit,
             warehouse_id=stmt.warehouse_id,
             location_code=transaction.location,
             quantity_moved=transaction.quantity,
             movement_id=transaction.id,
             company_id=token.company_id
         )


    # CRITICAL: Commit transaction
    await service.repository.session.commit()

    return ApiResponse(
        status="success",
        data=transaction,
        message="Transaction recorded successfully."
    )


@router.get("/transactions", response_model=ApiResponse[List[InventoryTransactionRead]])
async def get_transactions(
    request: Request,
    product_id: Optional[Union[uuid.UUID, str]] = None,
    warehouse_id: Optional[Union[uuid.UUID, str]] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    company_id_str = request.headers.get("X-Company-ID")
    if not company_id_str:
        raise HTTPException(status_code=400, detail="X-Company-ID header missing")
    
    # Allow strings for demo, otherwise try UUID
    try:
        if "-" in company_id_str:
            company_id = uuid.UUID(company_id_str)
        else:
            company_id = company_id_str
    except ValueError:
        company_id = company_id_str
    
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

@router.get("/levels", response_model=ApiResponse[List[Any]])
async def get_all_levels(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    List all current stock levels for the active company.
    """
    company_id_str = request.headers.get("X-Company-ID")
    if not company_id_str:
        raise HTTPException(status_code=400, detail="X-Company-ID header missing")
    
    # Simple query for now
    query = select(InventoryLevel).where(InventoryLevel.company_id == company_id_str)
    result = await db.execute(query)
    levels = result.scalars().all()
    
    return ApiResponse(
        status="success",
        data=[{
            "id": str(l.id),
            "product_id": str(l.product_id),
            "warehouse_id": str(l.warehouse_id),
            "stockQuantity": float(l.quantity),
            "reservedQuantity": float(l.reserved_quantity),
            "uom_id": str(l.uom_id)
        } for l in levels],
        message="Stock levels retrieved."
    )

@router.get("/folio-preview/{concept_id}", response_model=ApiResponse)
async def get_folio_preview(
    concept_id: str,
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    Generates a preview of the next folio for a given concept.
    """
    # Placeholder logic — in a real system, this would query the sequence generator
    import random
    fake_next = f"PREV-{concept_id[:3].upper()}-{random.randint(100, 999)}"
    return ApiResponse(
        status="success",
        data={"nextFolio": fake_next}
    )

@router.get("/vdetail/{document_id}", response_model=ApiResponse[DocumentDetailEntity])
async def get_document(
    document_id: str,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    Recupera los detalles de un documento de inventario por su ID.
    En el backend, el document_id es el id/trace_id de los movimientos.
    """
    try:
        doc_uuid = uuid.UUID(document_id)
        doc = await repo.get_document_by_id(doc_uuid, token.company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return ApiResponse(data=doc)

@router.get("/fifo-preview/{product_id}/{warehouse_id}")
async def get_fifo_preview(
    product_id: uuid.UUID,
    warehouse_id: uuid.UUID,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
) -> ApiResponse:
    """
    [PHASE 42.5] Picking Suggestion Logic.
    Returns the specific batches (Movements) that WILL be consumed by FIFO.
    """
    movements = await repo.get_available_movements_fifo(
        product_id=product_id,
        warehouse_id=warehouse_id,
        company_id=token.company_id
    )
    
    # Enrichment: We need pedimento numbers (labels)
    # The repository already does the outer join in get_available_movements_fifo potentially,
    # but MovementEntity might need clarification.
    picking_summary = []
    
    from inventory_app.models.movement import Movement
    from inventory_app.models.customs_pedimento import CustomsPedimento
    from sqlalchemy import select
    
    for m in movements:
        # Resolve pedimento number if exists
        p_num = "GENERAL/STOCK"
        if m.customs_pedimento_id:
            stmt = select(CustomsPedimento.pedimento_number).where(CustomsPedimento.id == m.customs_pedimento_id)
            res = await repo.session.execute(stmt)
            p_num = res.scalar() or "N/A"
            
        # Get location from DB model directly for precision
        stmt_loc = select(Movement.location).where(Movement.id == m.id)
        res_loc = await repo.session.execute(stmt_loc)
        location = res_loc.scalar() or "SIN UBICACIÓN"

        picking_summary.append({
            "movement_id": str(m.id),
            "quantity": float(m.available_quantity),
            "pedimento_number": p_num,
            "location": location,
            "date": m.created_at.isoformat() if m.created_at else None
        })
        
    return ApiResponse(
        status="success",
        data=picking_summary,
        message="FIFO picking preview generated."
    )

@router.get("/levels/{product_id}/{warehouse_id}")
async def get_stock_levels(
    product_id: Union[uuid.UUID, str],
    warehouse_id: Union[uuid.UUID, str],
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

@router.post("/relocate", response_model=ApiResponse)
@limiter.limit("30/minute")
async def relocate_stock(
    request: Request,
    stmt: StockRelocationCreate,
    service: InventoryTransactionService = Depends(get_inventory_service),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    [Phase 42.8] Internal Relocation.
    Executes a stock move between locations within the same warehouse.
    """
    try:
        results = await service.relocate_stock(
            stmt=stmt,
            company_id=token.company_id,
            user_id=token.sub,
            role=token.role
        )
        
        # Commit transaction
        await service.repository.session.commit()
        
        return ApiResponse(
            status="success",
            message=f"Relocated {stmt.quantity} units to {stmt.to_location}.",
            data={"count": len(results), "trace_id": str(stmt.correlation_id)}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"ERR_CREATE_DOC: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
