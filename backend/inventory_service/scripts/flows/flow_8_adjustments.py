import asyncio
import os
import sys
import logging
import uuid
from decimal import Decimal

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from inventory_app.db.session import AsyncSessionLocal
from inventory_app.services.inventory import InventoryTransactionService
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.infrastructure.clients.master_data import MasterDataClient
from inventory_app.schemas.inventory import InventoryTransactionCreate
from flows._shared_ids import resolve_flow_ids

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("flow-adjustments")

async def run_flow_adjustments():
    print("=" * 60)
    print("FLUJO: AJUSTES DE INVENTARIO (Phase 83)")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyInventoryRepository(session)
        md_client = MasterDataClient()
        service = InventoryTransactionService(repo, md_client)
        
        ids = await resolve_flow_ids(session)
        co_id = ids["company_id"]
        
        # 1. POSITIVE ADJUSTMENT (Found Item)
        print("\n[1] Ejecutando Ajuste Positivo (+10 unidades)...")
        pos_adj = InventoryTransactionCreate(
            product_id=ids["product_id"],
            warehouse_id=ids["warehouse_id"],
            transaction_type="ADJUSTMENT",
            quantity_change=Decimal("10.0"),
            location="LOC-AUDIT-01",
            comments="Item found during cycle count",
            concept_id=ids["concepts"].get("AJUSTE_POS", ids["concepts"].get("INV_ADJ"))
        )
        
        tx_pos = await service.create_transaction(
            stmt=pos_adj,
            company_id=co_id,
            user_id=str(ids["user_id"]),
            trace_id=uuid.uuid4(),
            module_token="DUMMY_TOKEN"
        )
        await session.commit()
        print(f"    OK: Ajuste positivo registrado. TX: {tx_pos.id}")

        # 2. NEGATIVE ADJUSTMENT (Damage)
        print("\n[2] Ejecutando Ajuste Negativo (-5 unidades)...")
        neg_adj = InventoryTransactionCreate(
            product_id=ids["product_id"],
            warehouse_id=ids["warehouse_id"],
            transaction_type="ADJUSTMENT",
            quantity_change=Decimal("-5.0"),
            location="LOC-AUDIT-01",
            comments="Damage - Broken seal",
            concept_id=ids["concepts"].get("AJUSTE_NEG", ids["concepts"].get("INV_ADJ"))
        )
        
        tx_neg = await service.create_transaction(
            stmt=neg_adj,
            company_id=co_id,
            user_id=str(ids["user_id"]),
            trace_id=uuid.uuid4(),
            module_token="DUMMY_TOKEN"
        )
        await session.commit()
        print(f"    OK: Ajuste negativo registrado. TX: {tx_neg.id}")

        # 3. VERIFY LEVELS
        print("\n[3] Verificando Niveles Finales...")
        level = await repo.get_stock(ids["warehouse_id"], ids["product_id"], co_id)
        print(f"    Stock Final: {level.quantity if level else 0.0}")

    print("\n" + "=" * 60)
    print("FLUJO DE AJUSTES COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_flow_adjustments())
