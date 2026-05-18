import uuid
from decimal import Decimal
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from inventory_app.schemas.pos import SaleCreate, SaleResponse
from inventory_app.schemas.inventory import InventoryTransactionCreate, TransactionType as InventoryTransactionType
from inventory_app.services.inventory import InventoryTransactionService
from inventory_app.dependencies.repositories import get_inventory_service
from common.responses import ApiResponse
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload

router = APIRouter()

@router.post("/checkout", response_model=ApiResponse[SaleResponse])
async def pos_checkout(
    sale: SaleCreate,
    service: InventoryTransactionService = Depends(get_inventory_service),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    Processes a POS Sale as a set of inventory OUT movements.
    """
    correlation_id = uuid.uuid4()
    total_weight = 0.0
    concept_id = "SAL-VEN"
    movement_ids = []

    # ── Industrial Price Validation ──────────────────────────────────────────
    # We validate that the prices sent by the POS match the Master Data rules.
    # from master_app.models.product import Product (Removed cross-service import)
    # from master_app.models.product_price import ProductPrice (Removed cross-service import)
    # from master_app.models.price_agreement import PriceAgreement (Removed cross-service import)
    # from master_app.models.partner import Partner (Removed cross-service import)
    from sqlalchemy import text

    # ── Document Creation (Header) ───────────────────────────────────────────
    # We will create the document after processing items to aggregate totals.
    doc_id = uuid.uuid4()

    for item in sale.items:
        # 1. Get Product metadata
        # 1. Get Product metadata via raw SQL
        prod_res = await service.repository.session.execute(
            text("SELECT allow_price_override FROM products WHERE id = :id"),
            {"id": item.product_id}
        )
        product_override = prod_res.scalar()
        if product_override is None:
            raise HTTPException(status_code=404, detail=f"Product {item.sku} not found")

        # 2. Resolve target price following "Onion Layers" hierarchy
        resolved_price = None
        
        # Layer 1: B2B Agreement
        if sale.customer_id:
            ag_res = await service.repository.session.execute(
                text("""
                    SELECT amount FROM price_agreements 
                    WHERE product_id = :pid AND partner_id = :ptid 
                    AND company_id = :cid AND valid_until IS NULL
                """),
                {"pid": item.product_id, "ptid": sale.customer_id, "cid": token.company_id}
            )
            resolved_price = ag_res.scalar()

        # Layer 2 & 3 resolve price list index
        target_list_index = 1
        if not resolved_price and sale.customer_id:
            p_res = await service.repository.session.execute(
                text("SELECT price_list_index FROM partners WHERE id = :pid"),
                {"pid": sale.customer_id}
            )
            assigned_list = p_res.scalar()
            if assigned_list is not None:
                target_list_index = assigned_list

        if resolved_price is None:
            # Layer 2: Warehouse Specific
            wh_pr_res = await service.repository.session.execute(
                text("""
                    SELECT price_amount FROM product_prices 
                    WHERE product_id = :pid AND company_id = :cid 
                    AND price_list_index = :pli AND warehouse_id = :wid AND is_active = true
                """),
                {"pid": item.product_id, "cid": token.company_id, "pli": target_list_index, "wid": sale.warehouse_id}
            )
            resolved_price = wh_pr_res.scalar()

        if resolved_price is None:
            # Layer 3: Global Company
            gl_pr_res = await service.repository.session.execute(
                text("""
                    SELECT price_amount FROM product_prices 
                    WHERE product_id = :pid AND company_id = :cid 
                    AND price_list_index = :pli AND warehouse_id IS NULL AND is_active = true
                """),
                {"pid": item.product_id, "cid": token.company_id, "pli": target_list_index}
            )
            resolved_price = gl_pr_res.scalar()

        # Layer 4: Fallback
        if resolved_price is None and target_list_index != 1:
            fb_pr_res = await service.repository.session.execute(
                text("""
                    SELECT price_amount FROM product_prices 
                    WHERE product_id = :pid AND company_id = :cid 
                    AND price_list_index = 1 AND warehouse_id IS NULL AND is_active = true
                """),
                {"pid": item.product_id, "cid": token.company_id}
            )
            resolved_price = fb_pr_res.scalar()

        # 3. Price Enforcement
        if resolved_price is not None:
            if abs(Decimal(str(resolved_price)) - item.unit_price) > Decimal("0.01"):
                if not product_override:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"PRICE_ERR: Invalid price for {item.sku}. Expected {resolved_price}, got {item.unit_price}."
                    )

        # 4. Inventory Movement Creation
        movement = InventoryTransactionCreate(
            product_id=item.product_id,
            warehouse_id=sale.warehouse_id,
            quantity_change=-item.quantity,
            transaction_type=InventoryTransactionType.OUT,
            concept_id="SAL-VEN",
            reference_id=doc_id,
            comments=f"POS Sale: {sale.comments or ''}"
        )
        tx = await service.create_transaction(
            stmt=movement,
            company_id=token.company_id,
            user_id=token.sub,
            trace_id=doc_id,
            module_token=token.token,
            role=token.role
        )
        movement_ids.append(tx.id)
        total_weight += float(getattr(tx, 'weight', 0) or 0)
            
    # 3. Create Document grouping record
    folio_id = str(doc_id)[:5].upper()
    doc_entity = {
        "id": doc_id,
        "folio": f"POS-{folio_id}",
        "document_type": "OUT",
        "status": "PROCESSED",
        "origin_name": "POS Terminal",
        "destination_name": "Final Customer",
        "total_items": len(sale.items),
        "total_weight": total_weight,
        "total_amount": float(sale.total_amount),
        "total_currency": sale.currency,
        "concept_id": concept_id,
        "external_reference": str(doc_id)
    }
    await service.repository.create_inventory_document(doc_entity, token.company_id)

    # Commit all movements and document
    await service.repository.session.commit()
    
    return ApiResponse(
        status="success",
        data=SaleResponse(
            sale_id=doc_id,
            movement_ids=movement_ids
        ),
        message="POS Sale processed and Inventory Document created successfully."
    )

