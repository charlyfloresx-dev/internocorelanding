from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from inventory_app.db.session import get_db
from inventory_app.models.document import InventoryDocument
from inventory_app.models.inventory import InventoryTransaction
from inventory_app.schemas.document import DocumentRead, DocumentLineRead
from inventory_app.domain.interfaces.master_data_client import IMasterDataClient
from inventory_app.dependencies.clients import get_master_data_client
from common.responses import ApiResponse
from common.security.require_permission import RequirePermission
from common.security.auth_payload import TokenPayload

router = APIRouter()


@router.get("/documents/{folio}", response_model=ApiResponse[DocumentRead])
async def get_document_for_reprint(
    folio: str,
    token: TokenPayload = Depends(RequirePermission("inventory.stock.read")),
    session: AsyncSession = Depends(get_db),
    md_client: IMasterDataClient = Depends(get_master_data_client),
):
    """
    Returns an inventory document with point-in-time prices for historical reprinting.
    Prices are resolved at the moment the document was created (soft-close query).
    """
    # 1. Fetch document (tenant-scoped)
    doc_result = await session.execute(
        select(InventoryDocument).where(
            InventoryDocument.folio == folio,
            InventoryDocument.company_id == token.company_id,
        )
    )
    doc = doc_result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR_DOCUMENT_NOT_FOUND", "message": "Documento no encontrado."},
        )

    doc_date = doc.created_at

    # 2. Fetch all transaction lines for this document
    tx_result = await session.execute(
        select(InventoryTransaction).where(
            InventoryTransaction.reference_id == doc.id,
            InventoryTransaction.company_id == token.company_id,
        )
    )
    transactions = tx_result.scalars().all()

    if not transactions:
        return ApiResponse(
            data=DocumentRead(
                id=doc.id,
                folio=doc.folio,
                document_type=doc.document_type,
                status=doc.status.value if hasattr(doc.status, "value") else str(doc.status),
                origin_name=doc.origin_name,
                destination_name=doc.destination_name,
                total_items=doc.total_items,
                total_amount=doc.total_amount_val,
                total_currency=doc.total_currency,
                created_at=doc_date,
                items=[],
            )
        )

    # 3. Fetch product metadata and point-in-time prices via MasterDataClient (HTTP)
    unique_product_ids = list({tx.product_id for tx in transactions})
    product_meta: dict = {}
    price_meta: dict = {}

    for pid in unique_product_ids:
        meta = await md_client.get_product_internal_metadata(pid, token.company_id)
        product_meta[str(pid)] = meta

        price = await md_client.get_product_price_at_date(
            product_id=pid,
            company_id=token.company_id,
            as_of=doc_date,
        )
        if price:
            price_meta[str(pid)] = price

    # 4. Assemble line items
    items = []
    for tx in transactions:
        pid_str = str(tx.product_id)
        meta = product_meta.get(pid_str, {})
        price_info = price_meta.get(pid_str)

        unit_price: Optional[Decimal] = price_info["amount"] if price_info else None
        currency: str = price_info["currency"] if price_info else doc.total_currency
        qty = abs(tx.quantity_change)
        line_total: Optional[Decimal] = (unit_price * qty) if unit_price is not None else None

        items.append(
            DocumentLineRead(
                product_id=tx.product_id,
                product_name=meta.get("name", f"[{pid_str[:8]}]"),
                sku=meta.get("sku", ""),
                transaction_type=tx.transaction_type.value
                if hasattr(tx.transaction_type, "value")
                else str(tx.transaction_type),
                quantity=qty,
                unit_price=unit_price,
                currency=currency,
                line_total=line_total,
            )
        )

    return ApiResponse(
        data=DocumentRead(
            id=doc.id,
            folio=doc.folio,
            document_type=doc.document_type,
            status=doc.status.value if hasattr(doc.status, "value") else str(doc.status),
            origin_name=doc.origin_name,
            destination_name=doc.destination_name,
            total_items=doc.total_items,
            total_amount=doc.total_amount_val,
            total_currency=doc.total_currency,
            created_at=doc_date,
            items=items,
        )
    )
