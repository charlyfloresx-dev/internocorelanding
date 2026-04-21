# backend/inventory_service/scripts/seed_ict_real.py
import asyncio
import uuid
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from sqlalchemy import text
from common.domain.value_objects import Money
from inventory_app.db.session import AsyncSessionLocal
from inventory_app.models.inventory import InventoryLevel
from inventory_app.models.warehouse import Warehouse
from inventory_app.models.document import InventoryDocument, DocumentStatus
from inventory_app.models.inter_company_transfer import InterCompanyTransfer, TransferStatus
from inventory_app.models.inter_company_transfer import InterCompanyTransfer, TransferStatus

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_ict")

# Fixed IDs for consistency
CO_LOGISTICS_ID  = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242") # Empresa A
CO_ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01") # Empresa B
CHARLY_ID        = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")

WH_TIJ_ID     = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.WH-TIJ")
WH_SDY_ID     = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.WH-SDY")
WH_TRANSIT_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.WH-ICT-TRANSIT")

PROD_ALU_ID   = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.item.MAT-001") # MAT-001
UOM_PZ_ID     = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")

async def seed():
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.now(timezone.utc)
            
            # 1. Cleanup old data
            await session.execute(text("DELETE FROM inter_company_transfers WHERE folio LIKE 'ICT-REAL-%'"))
            await session.execute(text("DELETE FROM inventory_documents WHERE folio LIKE 'STR-ICT-REAL-%' OR folio LIKE 'IN-REAL-ICT-REAL-%'"))
            # We don't delete inventory levels yet, we'll just upsert
            await session.commit()

            # 2. Ensure Warehouses
            wh_cfgs = [
                (WH_TIJ_ID, CO_LOGISTICS_ID, "WH-TIJ", "TIJ Central", "TJ", False),
                (WH_SDY_ID, CO_ENTERPRISE_ID, "WH-SDY", "SD Hub", "SD", False),
                (WH_TRANSIT_ID, CO_ENTERPRISE_ID, "TRANSIT", "Transit", "Net", True)
            ]
            for wh_id, co_id, code, name, loc, is_trans in wh_cfgs:
                wh = await session.get(Warehouse, wh_id)
                if not wh:
                    session.add(Warehouse(id=wh_id, company_id=co_id, tenant_id=co_id, code=code, name=name, location=loc, is_transit=is_trans))
                else:
                    wh.is_transit = is_trans
                    wh.tenant_id = co_id
            await session.flush()

            # 3. Initial Stock & WAC (Origin: TIJ)
            # Before transfer: 500u @ 15.00
            l_tij = await session.execute(text("SELECT id FROM inventory_levels WHERE warehouse_id=:w AND product_id=:p"), {"w": str(WH_TIJ_ID), "p": str(PROD_ALU_ID)})
            l_tij_id = l_tij.scalar()
            if not l_tij_id:
                l_a = InventoryLevel(id=uuid.uuid4(), company_id=CO_LOGISTICS_ID, tenant_id=CO_LOGISTICS_ID, warehouse_id=WH_TIJ_ID, product_id=PROD_ALU_ID, uom_id=UOM_PZ_ID, quantity=Decimal("400.0"), created_by=CHARLY_ID)
                l_a.wac = Money(Decimal("15.0"), "USD")
                session.add(l_a)
            else:
                await session.execute(text("UPDATE inventory_levels SET quantity=400.0, wac_amount=15.0 WHERE id=:id"), {"id": l_tij_id})

            # 4. Initial Stock & WAC (Destination: SDY)
            # Before receipt: 50u @ 10.00
            l_sdy = await session.execute(text("SELECT id FROM inventory_levels WHERE warehouse_id=:w AND product_id=:p"), {"w": str(WH_SDY_ID), "p": str(PROD_ALU_ID)})
            l_sdy_id = l_sdy.scalar()
            
            # Mathematical Audit Values:
            # (50 * 10.00) + (100 * 25.00) = 3000
            # 3000 / 150 = 20.00
            
            if not l_sdy_id:
                l_b = InventoryLevel(id=uuid.uuid4(), company_id=CO_ENTERPRISE_ID, tenant_id=CO_ENTERPRISE_ID, warehouse_id=WH_SDY_ID, product_id=PROD_ALU_ID, uom_id=UOM_PZ_ID, quantity=Decimal("150.0"), created_by=CHARLY_ID)
                l_b.wac = Money(Decimal("20.0"), "USD") # Final state after transaction
                session.add(l_b)
            else:
                await session.execute(text("UPDATE inventory_levels SET quantity=150.0, wac_amount=20.0 WHERE id=:id"), {"id": l_sdy_id})

            await session.flush()

            # 5. Create ICT Documents (DELIVERED Case)
            folio_a = "ICT-REAL-2026-0001"
            ict_a_id = uuid.uuid5(uuid.NAMESPACE_DNS, "ict.real.A")
            
            out_a = InventoryDocument(id=uuid.uuid4(), company_id=CO_LOGISTICS_ID, tenant_id=CO_LOGISTICS_ID, folio=f"STR-{folio_a}", document_type="ICT_OUT", status=DocumentStatus.PROCESSED, total_amount=Money(Decimal(2500), "USD"), external_reference=f"OUT-{ict_a_id}", created_by=CHARLY_ID)
            in_a = InventoryDocument(id=uuid.uuid4(), company_id=CO_ENTERPRISE_ID, tenant_id=CO_ENTERPRISE_ID, folio=f"IN-REAL-{folio_a}", document_type="ICT_IN", status=DocumentStatus.PROCESSED, total_amount=Money(Decimal(2500), "USD"), external_reference=f"IN-{ict_a_id}", created_by=CHARLY_ID)
            session.add_all([out_a, in_a])
            
            ict_a = InterCompanyTransfer(
                id=ict_a_id, 
                company_id=CO_LOGISTICS_ID, 
                folio=folio_a, 
                status=TransferStatus.DELIVERED, 
                destination_company_id=CO_ENTERPRISE_ID, 
                origin_warehouse_id=WH_TIJ_ID, 
                destination_warehouse_id=WH_SDY_ID, 
                transit_warehouse_id=WH_TRANSIT_ID, 
                product_id=PROD_ALU_ID, 
                uom_id=UOM_PZ_ID, 
                quantity=100, 
                weight=100, 
                currency="USD", 
                mirror_document_id=in_a.id, 
                inbound_folio=in_a.folio, 
                shipped_at=now-timedelta(days=2), 
                received_at=now-timedelta(days=1), 
                shipped_by=CHARLY_ID, 
                received_by=CHARLY_ID, 
                received_quantity=100, 
                created_by=CHARLY_ID,
                tenant_id=CO_LOGISTICS_ID
            )
            ict_a.unit_price = Money(Decimal(25), "USD")
            ict_a.wac_origin = Money(Decimal(15.0), "USD")
            ict_a.revenue_a = Money(Decimal(2500), "USD")
            ict_a.cost_b = Money(Decimal(2500), "USD")
            session.add(ict_a)

            await session.commit()
            logger.info("🎉 SEED ICT REAL COMPLETADO (Con impacto en Inventarios)")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error: {e}")
            import traceback; traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(seed())
