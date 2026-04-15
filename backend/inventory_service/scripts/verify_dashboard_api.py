import sys
import os
import uuid
import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
backend_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)
sys.path.append(backend_root)

# Imports
from common.models import Base
from app.db.session import AsyncSessionLocal, engine
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.models.movement import Movement
from app.models.document import InventoryDocument, DocumentStatus

async def verify_dashboard():
    print("--- Starting Dashboard API Verification ---")
    
    # 0. Setup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    company_id = uuid.uuid4()
    other_company_id = uuid.uuid4()
    
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=12)
    older_than_24h = now - timedelta(hours=48)
    
    async with AsyncSessionLocal() as db:
        repo = SQLAlchemyInventoryRepository(db)
        
        try:
            # 1. Inject Movements (Last 24h)
            print("   Injecting test movements...")
            m1 = Movement(
                id=uuid.uuid4(), warehouse_id=uuid.uuid4(), product_id=uuid.uuid4(),
                company_id=company_id, quantity=Decimal("10.0"), uom_id=uuid.uuid4(),
                weight=Decimal("10.0"), movement_type="IN", document_type="ENTRY", document_id=uuid.uuid4(),
                created_at=since_24h
            )
            m2 = Movement(
                id=uuid.uuid4(), warehouse_id=uuid.uuid4(), product_id=uuid.uuid4(),
                company_id=company_id, quantity=Decimal("5.0"), uom_id=uuid.uuid4(),
                weight=Decimal("5.0"), movement_type="OUT", document_type="EXIT", document_id=uuid.uuid4(),
                created_at=since_24h
            )
            m3 = Movement(
                id=uuid.uuid4(), warehouse_id=uuid.uuid4(), product_id=uuid.uuid4(),
                company_id=company_id, quantity=Decimal("1.0"), uom_id=uuid.uuid4(),
                weight=Decimal("1.0"), movement_type="TRANSFER", document_type="TRANS", document_id=uuid.uuid4(),
                created_at=since_24h
            )
            
            # Older movement (should not be counted in 24h summary)
            m_old = Movement(
                id=uuid.uuid4(), warehouse_id=uuid.uuid4(), product_id=uuid.uuid4(),
                company_id=company_id, quantity=Decimal("100.0"), uom_id=uuid.uuid4(),
                weight=Decimal("100.0"), movement_type="IN", document_type="ENTRY", document_id=uuid.uuid4(),
                created_at=older_than_24h
            )
            
            # Other company movement (should not be counted)
            m_other = Movement(
                id=uuid.uuid4(), warehouse_id=uuid.uuid4(), product_id=uuid.uuid4(),
                company_id=other_company_id, quantity=Decimal("1000.0"), uom_id=uuid.uuid4(),
                weight=Decimal("1000.0"), movement_type="IN", document_type="ENTRY", document_id=uuid.uuid4(),
                created_at=since_24h
            )
            
            db.add_all([m1, m2, m3, m_old, m_other])
            
            # 2. Inject Documents
            print("   Injecting test documents...")
            d1 = InventoryDocument(
                id=uuid.uuid4(), folio="INV-DRAFT-001", document_type="ENTRY",
                status=DocumentStatus.DRAFT, company_id=company_id, total_items=5
            )
            d2 = InventoryDocument(
                id=uuid.uuid4(), folio="INV-PROC-001", document_type="EXIT",
                status=DocumentStatus.PROCESSED, company_id=company_id, total_items=10
            )
            d_other = InventoryDocument(
                id=uuid.uuid4(), folio="INV-OTHER-001", document_type="ENTRY",
                status=DocumentStatus.DRAFT, company_id=other_company_id, total_items=99
            )
            
            db.add_all([d1, d2, d_other])
            await db.commit()
            
            # TEST 1: get_inventory_summary
            print("\n1. Testing get_inventory_summary...")
            summary = await repo.get_inventory_summary(company_id)
            print(f"   Results: IN={summary.entries_24h}, OUT={summary.outputs_24h}, TRANS={summary.transfers_24h}, PENDING={summary.pending_docs}")
            
            assert summary.entries_24h == 1, f"Expected 1 IN, got {summary.entries_24h}"
            assert summary.outputs_24h == 1, f"Expected 1 OUT, got {summary.outputs_24h}"
            assert summary.transfers_24h == 1, f"Expected 1 TRANS, got {summary.transfers_24h}"
            assert summary.pending_docs == 1, f"Expected 1 PENDING, got {summary.pending_docs}"
            print("   [PASS] Summary accurate and time/tenant isolated.")
            
            # TEST 2: list_movements
            print("\n2. Testing list_movements...")
            movements = await repo.list_movements(company_id, limit=10)
            print(f"   Documents found: {len(movements)}")
            
            assert len(movements) == 2, f"Expected 2 documents for company, got {len(movements)}"
            print(f"   First document folio: {movements[0].folio}")
            
            # Filter by type
            movements_in = await repo.list_movements(company_id, movement_type="ENTRY")
            assert len(movements_in) == 1, f"Expected 1 ENTRY document, got {len(movements_in)}"
            assert movements_in[0].folio == "INV-DRAFT-001"
            print("   [PASS] Listing paginated and filtered correctly.")
            
        except Exception:
            print("\n[CRITICAL ERROR] SCRIPT EXECUTION:")
            traceback.print_exc()
            
    await engine.dispose()
    print("\n--- Dashboard API Verification Completed ---")

if __name__ == "__main__":
    asyncio.run(verify_dashboard())
