import uuid
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
    from master_app.models.product import Product
    from master_app.models.product_price import ProductPrice
    from master_app.models.price_agreement import PriceAgreement
    from master_app.models.partner import Partner
    from sqlalchemy import select, and_

    # ── Document Creation (Header) ───────────────────────────────────────────
    from inventory_app.models.inventory import InventoryDocument, DocumentType
    doc_id = uuid.uuid4()
    
    doc = InventoryDocument(
        id=doc_id,
        company_id=token.company_id,
        tenant_id=token.company_id,
        document_type=DocumentType.POS_SALE,
        document_number=f"POS-{uuid.uuid4().hex[:8].upper()}",
        reference=f"POS Terminal {sale.warehouse_id}",
        comments=sale.comments or "POS Checkout",
        created_by=token.sub,
        version_id=1
    )
    service.repository.session.add(doc)

    for item in sale.items:
        # 1. Get Product metadata
        stmt = select(Product).where(Product.id == item.product_id)
        prod_res = await service.repository.session.execute(stmt)
        product = prod_res.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.sku} not found")

        # 2. Resolve target price following "Onion Layers" hierarchy
        resolved_price = None
        
        # Layer 1: B2B Agreement
        if sale.customer_id:
            ag_stmt = select(PriceAgreement).where(
                and_(
                    PriceAgreement.product_id == item.product_id,
                    PriceAgreement.partner_id == sale.customer_id,
                    PriceAgreement.company_id == token.company_id,
                    PriceAgreement.valid_until.is_(None)
                )
            )
            ag_res = await service.repository.session.execute(ag_stmt)
            agreement = ag_res.scalar_one_or_none()
            if agreement:
                resolved_price = agreement.amount

        # Layer 2 & 3 resolve price list index
        target_list_index = 1
        if not resolved_price and sale.customer_id:
            p_stmt = select(Partner.price_list_index).where(Partner.id == sale.customer_id)
            p_res = await service.repository.session.execute(p_stmt)
            assigned_list = p_res.scalar()
            if assigned_list is not None:
                target_list_index = assigned_list

        if resolved_price is None:
            # Layer 2: Warehouse Specific
            wh_pr_stmt = select(ProductPrice).where(
                and_(
                    ProductPrice.product_id == item.product_id,
                    ProductPrice.company_id == token.company_id,
                    ProductPrice.price_list_index == target_list_index,
                    ProductPrice.warehouse_id == sale.warehouse_id,
                    ProductPrice.is_active == True
                )
            )
            wh_pr_res = await service.repository.session.execute(wh_pr_stmt)
            wh_price = wh_pr_res.scalar_one_or_none()
            if wh_price:
                resolved_price = wh_price.price.amount

        if resolved_price is None:
            # Layer 3: Global Company
            gl_pr_stmt = select(ProductPrice).where(
                and_(
                    ProductPrice.product_id == item.product_id,
                    ProductPrice.company_id == token.company_id,
                    ProductPrice.price_list_index == target_list_index,
                    ProductPrice.warehouse_id.is_(None),
                    ProductPrice.is_active == True
                )
            )
            gl_pr_res = await service.repository.session.execute(gl_pr_stmt)
            gl_price = gl_pr_res.scalar_one_or_none()
            if gl_price:
                resolved_price = gl_price.price.amount

        # Layer 4: Fallback
        if resolved_price is None and target_list_index != 1:
            fb_pr_stmt = select(ProductPrice).where(
                and_(
                    ProductPrice.product_id == item.product_id,
                    ProductPrice.company_id == token.company_id,
                    ProductPrice.price_list_index == 1,
                    ProductPrice.warehouse_id.is_(None),
                    ProductPrice.is_active == True
                )
            )
            fb_pr_res = await service.repository.session.execute(fb_pr_stmt)
            fb_price = fb_pr_res.scalar_one_or_none()
            if fb_price:
                resolved_price = fb_price.price.amount

        # 3. Price Enforcement
        if resolved_price is not None:
            if abs(float(resolved_price) - item.unit_price) > 0.01:
                if not product.allow_price_override:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"PRICE_ERR: Invalid price for {item.sku}. Expected {resolved_price}, got {item.unit_price}."
                    )

        # 4. Inventory Movement Creation
        movement = InventoryTransactionCreate(
            product_id=item.product_id,
            warehouse_id=sale.warehouse_id,
            quantity_change=item.quantity,
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

