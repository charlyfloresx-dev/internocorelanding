import uuid
import hashlib
import logging
from decimal import Decimal
from typing import List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import httpx

from inventory_app.db.session import get_db
from inventory_app.models.inventory import InventoryLevel, InventoryTransaction, TransactionType
from inventory_app.domain.entities.inventory_item import TransactionType as DomainTransactionType
from inventory_app.models.movement import Movement
from inventory_app.models.customs_pedimento import CustomsPedimento
from inventory_app.schemas.inventory import InventoryTransactionCreate, InventoryTransactionRead, InventoryDocumentCreate, StockRelocationCreate
from inventory_app.services.inventory import InventoryTransactionService
from inventory_app.services.density_guard_audit import run_density_guard_audit
from inventory_app.domain.entities.inventory_item import DocumentDetailEntity, DocumentListRowEntity
from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
from inventory_app.dependencies.repositories import get_inventory_service, get_inventory_repository
from common.responses import ApiResponse
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload
from common.security.idempotency import idempotent
from common.security.limiter import limiter

router = APIRouter()
logger = logging.getLogger(__name__)

_OUTBOUND_TYPES = {DomainTransactionType.OUT, DomainTransactionType.BACKFLUSHING}


async def _notify_admin_new_document(
    company_id: str,
    folio: str,
    doc_type: str,
    origin: str,
    destination: str,
    items_count: int,
    total_amount: str,
    doc_id: str = None
):
    """
    Background task: dispatches an HTTP event to the notification-service.
    Fire-and-forget — never blocks the main inventory transaction.
    """
    from common.config import settings
    _NOTIF_URL = settings.NOTIFICATION_SERVICE_URL
    type_clean = str(doc_type).lower()
    type_desc = "Entrada" if "in" in type_clean else "Salida" if "out" in type_clean else "Movimiento"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{_NOTIF_URL}/api/v1/events/",
                json={
                    "event_id": doc_id or folio,
                    "event_type": "InventoryDocumentCreated",
                    "folio": folio,
                    "doc_type": type_desc,
                    "origin": origin,
                    "destination": destination,
                    "items_count": items_count,
                    "total_amount": total_amount,
                    "action_url": f"/inventory/documents/{doc_id}" if doc_id else "/inventory/documents",
                },
                headers={"X-Company-ID": str(company_id)},
            )
            logger.info(f"🔔 InventoryDocumentCreated event dispatched for {folio}")
    except Exception as e:
        logger.warning(f"NOTIFY_ADMIN_FAILED (non-critical): {e}")


async def _next_doc_folio(session, company_id: str, doc_type: str, fallback_id: uuid.UUID) -> str:
    """
    Generates a sequential folio using a per-company advisory lock to prevent
    race conditions under concurrent requests.
    """
    # Advisory lock key: deterministic per company+type, fits in int4
    lock_raw = f"{company_id}:{doc_type}:folio"
    lock_key = int(hashlib.md5(lock_raw.encode()).hexdigest()[:8], 16) % (2 ** 31)
    try:
        await session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": lock_key})
        count_res = await session.execute(
            text("SELECT count(*) FROM inventory_documents WHERE company_id = :cid"),
            {"cid": company_id},
        )
        seq_num = (count_res.scalar() or 0) + 1
        return f"{seq_num:06d}"
    except Exception:
        return str(fallback_id)[:5].upper()


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
    results = []
    total_weight = Decimal("0")
    total_amount = Decimal("0")

    for i, item in enumerate(doc.items):
        item_request_id = f"{client_request_id}:{i}" if client_request_id else None

        stmt = InventoryTransactionCreate(
            product_id=item.product_id,
            uom_id=item.uom_id,
            warehouse_id=doc.warehouse_id,
            transaction_type=doc.type,
            concept_id=doc.concept_id,
            quantity_change=-item.quantity if doc.type in _OUTBOUND_TYPES else item.quantity,
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
            err_msg = str(e)
            if "ERR_WAREHOUSE_LOCK" in err_msg:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err_msg)
            if "ERR_INSUFFICIENT_STOCK" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{err_msg} | SKU: {item.sku}"
                )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

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
        total_weight += Decimal(str(tx.weight)) if tx.weight else Decimal("0")
        if tx.price:
            total_amount += Decimal(str(tx.price.amount)) * Decimal(str(tx.quantity))
        else:
            logger.warning(f"TX_PRICE_MISSING: Transaction {tx.id} has no price.")

    # Persist Document Metadata
    origin_name = "Almacén Central"
    try:
        warehouse_data = await service.md_client.get_warehouse(doc.warehouse_id, token.company_id)
        if warehouse_data:
            origin_name = warehouse_data.get("name") or warehouse_data.get("code") or origin_name
    except Exception as e:
        logger.error(f"MD_WAREHOUSE_ENRICHMENT_FAILED: {str(e)}")

    destination_name = doc.external_entity or "N/A"
    if doc.external_entity:
        try:
            potential_uuid = (
                doc.external_entity
                if isinstance(doc.external_entity, uuid.UUID)
                else uuid.UUID(str(doc.external_entity))
            )
            partner_data = await service.md_client.get_partner(potential_uuid, token.company_id)
            if partner_data:
                destination_name = partner_data.get("name") or partner_data.get("code") or destination_name
        except (ValueError, Exception):
            pass

    folio_id = await _next_doc_folio(
        service.repository.session, token.company_id, str(doc.type), doc.correlation_id
    )

    doc_entity = {
        "id": doc.correlation_id,
        "folio": f"DOC-{folio_id}",
        "document_type": doc.type,
        "status": "PROCESSED",
        "origin_name": f"App Móvil ({doc.app_reference})" if getattr(doc, "app_reference", None) else origin_name,
        "destination_name": destination_name,
        "total_items": len(results),
        "total_weight": str(total_weight),
        "total_amount": str(total_amount),
        "total_currency": (results[0].price.currency if (results and results[0].price) else "MXN"),
        "concept_id": doc.concept_id,
        "external_reference": str(doc.correlation_id),
        "payment_method": doc.payment_method,
    }

    try:
        await service.repository.create_inventory_document(doc_entity, token.company_id)
        await service.repository.session.commit()
    except Exception as e:
        logging.error(f"DOC_METADATA_FAILED: {str(e)}", exc_info=True)
        await service.repository.session.rollback()
        raise HTTPException(status_code=500, detail={"code": "ERR_DOCUMENT_PERSIST", "message": "Failed to persist document metadata."})

    background_tasks.add_task(
        _notify_admin_new_document,
        company_id=token.company_id,
        folio=f"DOC-{folio_id}",
        doc_type=str(doc.type),
        origin=origin_name,
        destination=destination_name,
        items_count=len(results),
        total_amount=str(total_amount),
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
    try:
        transaction = await service.create_transaction(
            stmt=stmt,
            company_id=token.company_id,
            user_id=token.sub,
            trace_id=token.correlation_id or uuid.uuid4(),
            module_token=token.token,
            client_request_id=client_request_id,
            role=token.role,
            home_warehouse_id=token.wid,
            is_supervisor=token.is_supervisor
        )
    except ValueError as e:
        if "ERR_WAREHOUSE_LOCK" in str(e):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if transaction.location:
        background_tasks.add_task(
            run_density_guard_audit,
            warehouse_id=stmt.warehouse_id,
            location_code=transaction.location,
            quantity_moved=transaction.quantity,
            movement_id=transaction.id,
            company_id=token.company_id
        )

    await service.repository.session.commit()

    return ApiResponse(
        status="success",
        data=transaction,
        message="Transaction recorded successfully."
    )


@router.get("/documents", response_model=ApiResponse[List[DocumentListRowEntity]])
async def list_documents(
    document_type: Optional[str] = None,
    warehouse_id: Optional[uuid.UUID] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """Listado paginado de documentos de inventario filtrable por tipo y fechas."""
    docs, total = await repo.list_movements(
        company_id=token.company_id,
        limit=limit,
        offset=offset,
        movement_type=document_type,
        warehouse_id=warehouse_id,
        date_from=date_from,
        date_to=date_to,
    )
    return ApiResponse(status="success", data=docs, message=f"{total} documents found.")


@router.get("/transactions", response_model=ApiResponse[List[InventoryTransactionRead]])
async def get_transactions(
    request: Request,
    product_id: Optional[Union[uuid.UUID, str]] = None,
    warehouse_id: Optional[Union[uuid.UUID, str]] = None,
    limit: int = 100,
    offset: int = 0,
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
    db: AsyncSession = Depends(get_db)
):
    transactions = await InventoryTransactionService.get_transactions(
        db=db,
        company_id=token.company_id,
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
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
    db: AsyncSession = Depends(get_db)
):
    """List current stock levels for the authenticated company."""
    query = select(InventoryLevel).where(InventoryLevel.company_id == token.company_id)
    result = await db.execute(query)
    levels = result.scalars().all()

    return ApiResponse(
        status="success",
        data=[{
            "id": str(l.id),
            "product_id": str(l.product_id),
            "warehouse_id": str(l.warehouse_id),
            "stockQuantity": str(l.quantity),
            "reservedQuantity": str(l.reserved_quantity),
            "uom_id": str(l.uom_id)
        } for l in levels],
        message="Stock levels retrieved."
    )


@router.get("/folio-preview/{concept_id}", response_model=ApiResponse)
async def get_folio_preview(
    concept_id: str,
    service: InventoryTransactionService = Depends(get_inventory_service),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """Returns the next folio that will be assigned for a given document type."""
    try:
        count_res = await service.repository.session.execute(
            text("SELECT count(*) FROM inventory_documents WHERE company_id = :cid AND document_type = :dtype"),
            {"cid": token.company_id, "dtype": concept_id},
        )
        next_seq = (count_res.scalar() or 0) + 1
        next_folio = f"DOC-{next_seq:06d}"
    except Exception:
        next_folio = f"DOC-{str(uuid.uuid4())[:5].upper()}"

    return ApiResponse(
        status="success",
        data={"nextFolio": next_folio}
    )


@router.get("/vdetail/{document_id}", response_model=ApiResponse[DocumentDetailEntity])
async def get_document(
    document_id: str,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """Recupera los detalles de un documento de inventario por su ID."""
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
    Returns the specific batches (Movements) that WILL be consumed by FIFO.
    Uses a single JOIN query to avoid N+1 per movement.
    """
    movements = await repo.get_available_movements_fifo(
        product_id=product_id,
        warehouse_id=warehouse_id,
        company_id=token.company_id
    )

    if not movements:
        return ApiResponse(status="success", data=[], message="No FIFO batches available.")

    movement_ids = [m.id for m in movements]
    pedimento_map: dict[uuid.UUID, str] = {}
    location_map: dict[uuid.UUID, str] = {}

    # Single query for all pedimentos
    ped_rows = await repo.session.execute(
        select(Movement.id, CustomsPedimento.pedimento_number)
        .outerjoin(CustomsPedimento, Movement.customs_pedimento_id == CustomsPedimento.id)
        .where(Movement.id.in_(movement_ids))
    )
    for row in ped_rows:
        pedimento_map[row[0]] = row[1] or "GENERAL/STOCK"

    # Single query for all locations
    loc_rows = await repo.session.execute(
        select(Movement.id, Movement.location).where(Movement.id.in_(movement_ids))
    )
    for row in loc_rows:
        location_map[row[0]] = row[1] or "SIN UBICACIÓN"

    picking_summary = [
        {
            "movement_id": str(m.id),
            "quantity": str(m.available_quantity),
            "pedimento_number": pedimento_map.get(m.id, "GENERAL/STOCK"),
            "location": location_map.get(m.id, "SIN UBICACIÓN"),
            "date": m.created_at.isoformat() if m.created_at else None,
        }
        for m in movements
    ]

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
    """Consulta niveles de stock (actual y reservado) para un producto en un almacén."""
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
            "quantity": "0",
            "reserved_quantity": "0",
            "available_quantity": "0"
        }

    available = Decimal(str(level.quantity)) - Decimal(str(level.reserved_quantity))
    return {
        "product_id": str(level.product_id),
        "warehouse_id": str(level.warehouse_id),
        "quantity": str(level.quantity),
        "reserved_quantity": str(level.reserved_quantity),
        "available_quantity": str(available)
    }


@router.post("/relocate", response_model=ApiResponse)
@limiter.limit("30/minute")
async def relocate_stock(
    request: Request,
    stmt: StockRelocationCreate,
    service: InventoryTransactionService = Depends(get_inventory_service),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """[Phase 42.8] Internal Relocation — moves stock between locations within the same warehouse."""
    try:
        results = await service.relocate_stock(
            stmt=stmt,
            company_id=token.company_id,
            user_id=token.sub,
            role=token.role
        )

        await service.repository.session.commit()

        return ApiResponse(
            status="success",
            message=f"Relocated {stmt.quantity} units to {stmt.to_location}.",
            data={"count": len(results), "trace_id": str(stmt.correlation_id)}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"ERR_RELOCATE: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
