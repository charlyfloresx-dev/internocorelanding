"""
Demo Reset Endpoint — "Fresh Demo Rule"
========================================
Purpose: Clear and re-populate demo data for the active tenant so that the
         Mission Control Dashboard always looks "alive" with timeseries
         from the last 24 hours.

Security:
  - Accessible only with OWNER or ADMIN role.
  - Operates strictly on the company_id from the JWT (guaranteed multitenancy).
  - In real production (ENV_MODE=prod), the endpoint can be disabled.
"""

import uuid
import asyncio
import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Union

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, text

from inventory_app.db.session import AsyncSessionLocal
from inventory_app.models.movement import Movement
from inventory_app.models.inventory import InventoryLevel, InventoryTransaction, TransactionType
from inventory_app.models.document import InventoryDocument, DocumentStatus
from inventory_app.models.concept import MovementConcept
from common.enums import MovementType
from inventory_app.models.item_variant import ItemVariant
from inventory_app.models.inter_company_transfer import InterCompanyTransfer, TransferStatus
from common.responses import ApiResponse
from common.security.auth_payload import TokenPayload

logger = logging.getLogger("demo_reset")
router = APIRouter()

# ─── Constants ────────────────────────────────────────────────────────────────

_DEMO_EMAIL = "charly@interno.com"
_SYSTEM_USER = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")
_UOM_PZ = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")
_SKUS = [f"MAT-{str(i).zfill(3)}" for i in range(1, 11)]

# ─── Movement Concepts Configuration (Sincronizado con Master Data) ───────────
_CONCEPT_CONFIG = {
    "ENT-PUR":     {"name": "Compra",           "type": MovementType.ENTRY},
    "ENT-ADJ":     {"name": "Ajuste Positivo",   "type": MovementType.ENTRY},
    "SAL-VEN":     {"name": "Venta",             "type": MovementType.OUTPUT},
    "SAL-ADJ":     {"name": "Ajuste Negativo",   "type": MovementType.OUTPUT},
    "TRF-INT":     {"name": "Traspaso Interno",  "type": MovementType.TRANSFER},
}


# ─── Helper: Auth guard ───────────────────────────────────────────────────────

def _require_admin(request: Request) -> TokenPayload:
    token: TokenPayload = getattr(request.state, "user_token", None)
    if not token:
        raise HTTPException(status_code=401, detail="Session token not found.")
    
    # Check both single role and role_names list, case-insensitive
    roles = [token.role.upper()] + [r.upper() for r in token.role_names]
    if "OWNER" not in roles and "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="Requires OWNER or ADMIN role.")
    return token


# ─── Core seed logic ──────────────────────────────────────────────────────────

async def _run_demo_seed(company_id: uuid.UUID) -> dict:
    """
    Clears and re-seeds demo data for the given company_id.
    All operations are ATOMIC within a single transaction.
    """
    now = datetime.utcnow()
    result = {
        "cleared_tables": [],
        "seeded": {
            "documents": 0,
            "movements": 0,
            "transactions": 0
        },
        "errors": []
    }

    async with AsyncSessionLocal() as session:
        async with session.begin():

            # ── 1. TRUNCATE (filtered by company_id = multitenancy safe) ──
            logger.info(f"[demo-reset] Clearing tables for company {company_id}...")

            await session.execute(
                delete(Movement).where(Movement.company_id == company_id)
            )
            result["cleared_tables"].append("inventory_movements")

            await session.execute(
                delete(InventoryTransaction).where(InventoryTransaction.company_id == company_id)
            )
            result["cleared_tables"].append("inventory_transactions")

            await session.execute(
                delete(InventoryDocument).where(InventoryDocument.company_id == company_id)
            )
            result["cleared_tables"].append("inventory_documents")

            await session.execute(
                delete(InventoryLevel).where(InventoryLevel.company_id == company_id)
            )
            result["cleared_tables"].append("inventory_levels")
            
            await session.execute(
                delete(InterCompanyTransfer).where(
                    (InterCompanyTransfer.company_id == company_id) | 
                    (InterCompanyTransfer.destination_company_id == company_id)
                )
            )
            result["cleared_tables"].append("inter_company_transfers")

            # ── 2. WAREHOUSES (Homologated IDs) ────────────────────────────
            wh_tij_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{company_id}.WH-TIJ")
            wh_sdy_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{company_id}.WH-SDY")
            
            # ── 3. CONCEPTS (upsert with Homologated IDs) ──────────────────
            concept_ids: dict[str, uuid.UUID] = {}
            for code, cfg in _CONCEPT_CONFIG.items():
                c_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.concept.{company_id}.{code}")
                stmt = select(MovementConcept).filter_by(id=c_id, company_id=company_id)
                res = await session.execute(stmt)
                obj = res.scalars().first()
                if not obj:
                    obj = MovementConcept(
                        id=c_id, 
                        name=cfg["name"],
                        code=code, 
                        type=cfg["type"],
                        company_id=company_id, 
                        tenant_id=company_id,
                        created_by=_SYSTEM_USER
                    )
                    session.add(obj)
                    await session.flush()
                concept_ids[code] = obj.id
            result["seeded"]["concepts"] = len(concept_ids)

            # ── 4. STOCK (base levels with alerts) ─────────────────────────
            wh_stock = {
                wh_tij_id: {"normal": 5000.0, "critical_skus": ["MAT-001", "MAT-003"]},
                wh_sdy_id: {"normal": 2000.0, "critical_skus": ["MAT-005"]},
            }
            for sku in _SKUS:
                item_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{company_id}.{sku}")
                for wh_id, cfg in wh_stock.items():
                    qty = 8.0 if sku in cfg["critical_skus"] else cfg["normal"]
                    session.add(InventoryLevel(
                        id=uuid.uuid4(), company_id=company_id, tenant_id=company_id,
                        warehouse_id=wh_id, product_id=item_id,
                        uom_id=_UOM_PZ, quantity=Decimal(str(qty)),
                        _wac_amount=Decimal(str(round(random.uniform(8, 45), 2))),
                        _wac_currency="MXN",
                        created_by=_SYSTEM_USER
                    ))
            result["seeded"]["inventory_levels"] = len(_SKUS) * 2

            # ── 5. DOCUMENTS with real folios ─────────────────────────────
            doc_templates = [("ENT", "ENTRY")] * 6 + [("SAL", "EXIT")] * 5 + [("TRA", "TRANSFER")] * 3
            documents: list[InventoryDocument] = []
            for i, (prefix, dtype) in enumerate(doc_templates, 1):
                # Simulated Industrial Names
                origin = "PRÉSTAMO EXTERNO" if dtype == "ENTRY" else "ALMACÉN TIJUANA"
                dest = "ALMACÉN TIJUANA" if dtype == "ENTRY" else ("CLIENTE FINAL" if dtype == "EXIT" else "TERMINAL SD")
                
                doc = InventoryDocument(
                    id=uuid.uuid4(), company_id=company_id, tenant_id=company_id,
                    folio=f"{prefix}-2026-{str(i).zfill(4)}",
                    document_type=dtype,
                    status=DocumentStatus.PROCESSED,
                    origin_name=origin,
                    destination_name=dest,
                    total_items=random.randint(2, 12),
                    total_weight=Decimal(str(round(random.uniform(50, 500), 2))),
                    created_by=_SYSTEM_USER,
                    external_reference=f"EXT-REF-{uuid.uuid4().hex[:8].upper()}"
                )
                session.add(doc)
                documents.append(doc)
            await session.flush()
            result["seeded"]["documents"] = len(documents)

            # ── 6. MOVEMENTS (150 records, peak-hours, 24h window) ──────
            move_count = 0
            for i in range(150):
                sku = random.choice(_SKUS)
                item_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{company_id}.{sku}")
                wh = random.choice([wh_tij_id, wh_sdy_id])
                doc = random.choice(documents)

                # Peak-hour bias
                hour_offset = random.randint(0, 23)
                if random.random() < 0.6:
                    hour_offset = random.choice([7, 8, 9, 15, 16, 17])
                tx_date = now - timedelta(hours=hour_offset, minutes=random.randint(0, 59))

                base_qty = Decimal(str(round(random.uniform(10, 60), 2)))
                if hour_offset in (8, 16):
                    base_qty *= Decimal(str(round(random.uniform(4, 12), 1)))

                is_in = random.random() > 0.4
                concept_code = "ENT-PUR" if is_in else "SAL-VEN"

                session.add(InventoryTransaction(
                    id=uuid.uuid4(), company_id=company_id, tenant_id=company_id,
                    product_id=item_id, warehouse_id=wh,
                    transaction_type=TransactionType.IN if is_in else TransactionType.OUT,
                    quantity_change=base_qty if is_in else -base_qty,
                    previous_balance=Decimal("1000"),
                    new_balance=Decimal("1000") + (base_qty if is_in else -base_qty),
                    comments=f"Demo {concept_code}",
                    created_at=tx_date, created_by=_SYSTEM_USER
                ))

                session.add(Movement(
                    id=uuid.uuid4(), company_id=company_id, tenant_id=company_id,
                    warehouse_id=wh, product_id=item_id,
                    quantity=base_qty, uom_id=_UOM_PZ,
                    weight=Decimal("0.0"),
                    _amount=Decimal(str(round(random.uniform(8, 50), 2))) if is_in else Decimal("0.0"),
                    _currency="MXN",
                    movement_type="IN" if is_in else "OUT",
                    concept_id=concept_ids[concept_code],
                    document_type=str(doc.document_type)[:3],
                    document_id=doc.id,
                    created_at=tx_date, created_by=_SYSTEM_USER
                ))
                move_count += 1

            result["seeded"]["movements"] = move_count
            result["seeded"]["transactions"] = move_count
            
            # ── 7. INTER-COMPANY TRANSFERS (Trusted Broker Seed) ───────
            logger.info(f"[demo-reset] Seeding Inter-Company Transfers...")
            transfer_count = 0
            company_b = uuid.UUID("d6b0bfcd-1eab-4d83-94c6-2eb969b92289")
            
            for i in range(10):
                sku = random.choice(_SKUS)
                item_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{company_id}.{sku}")
                
                days_ago = random.randint(0, 6)
                shipped_date = now - timedelta(days=days_ago, hours=random.randint(1, 10))
                is_delivered = random.random() < 0.6
                received_date = shipped_date + timedelta(hours=random.randint(4, 48)) if is_delivered else None
                
                status = TransferStatus.DELIVERED if is_delivered else TransferStatus.SHIPPED
                qty = Decimal(str(random.randint(10, 500)))
                transfer_price = Decimal(str(round(random.uniform(50, 150), 2)))
                wac = transfer_price * Decimal("0.8")
                
                transfer = InterCompanyTransfer(
                    id=uuid.uuid4(),
                    folio=f"ICT-202603{(16-days_ago)}-{str(uuid.uuid4())[:5].upper()}",
                    company_id=company_id,
                    tenant_id=company_id,
                    destination_company_id=company_b,
                    origin_warehouse_id=wh_tij_id,
                    destination_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{company_b}.WH-MAIN"),
                    transit_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{company_id}.WH-SDY"),
                    product_id=item_id,
                    uom_id=_UOM_PZ,
                    quantity=qty,
                    weight=Decimal("0.0"),
                    _unit_price_at_dispatch=transfer_price,
                    _wac_at_dispatch=wac,
                    _transfer_revenue_a=qty * transfer_price,
                    _acquisition_cost_b=(qty * transfer_price) if is_delivered else None,
                    status=status,
                    shipped_at=shipped_date,
                    shipped_by=_SYSTEM_USER,
                    received_at=received_date,
                    received_by=_SYSTEM_USER if is_delivered else None,
                    received_quantity=qty if is_delivered else Decimal("0.0"),
                    origin_sku=sku,
                    destination_sku=f"ENT-{sku}",
                    destination_product_id=item_id,
                    notes=f"Demo ICT - Automatically generated",
                    created_by=_SYSTEM_USER,
                    created_at=shipped_date
                )
                session.add(transfer)
                transfer_count += 1
            
            result["seeded"]["inter_company_transfers"] = transfer_count

            result["timestamp"] = now.isoformat()
            logger.info(f"[demo-reset] ✅ Seed completed: {result}")

    return result


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post(
    "/admin/demo-reset",
    summary="🔄 Demo Data Reset — Fresh Demo Rule",
    description=(
        "Clears and re-seeds active tenant data with timestamps from the "
        "last 24 hours. Only available for OWNER/ADMIN roles. "
        "Designed to keep the Dashboard always 'alive' in demos and development."
    ),
    tags=["Admin / Demo"],
)
async def demo_reset(
    request: Request,
    x_company_id: Union[uuid.UUID, str] = Header(...),
    token: TokenPayload = Depends(_require_admin),
):
    """
    POST /api/v1/admin/demo-reset

    Required Headers:
      - x-company-id: Tenant UUID
      - Authorization: Bearer <jwt> (OWNER or ADMIN role)
    """
    try:
        company_id = uuid.UUID(str(x_company_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid x-company-id.")

    logger.info(f"[demo-reset] Triggered by user={token.sub}, company={company_id}")

    result = await _run_demo_seed(company_id)

    return ApiResponse(
        data=result,
        message="✅ Demo reset completed. Dashboard refreshed with data from the last 24 hours.",
        meta={"company_id": str(company_id), "triggered_by": token.sub}
    )


@router.get(
    "/admin/demo-reset/status",
    summary="Demo Reset — Health Check",
    tags=["Admin / Demo"],
)
async def demo_reset_status(
    request: Request,
    token: TokenPayload = Depends(_require_admin),
):
    """Verifies that the demo-reset endpoint is active and the user has permissions."""
    return ApiResponse(
        data={"available": True, "trigger_email": _DEMO_EMAIL},
        message="Demo-reset endpoint active."
    )
