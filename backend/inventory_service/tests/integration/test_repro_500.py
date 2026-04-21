import pytest
import uuid
from decimal import Decimal
from inventory_app.services.transfer_service import TransferService
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.domain.entities.inventory_item import MovementEntity
from inventory_app.models.warehouse import Warehouse
from inventory_app.models.stock import InventoryLevel
from sqlalchemy import select
from common.domain.value_objects import Money

@pytest.mark.asyncio
async def test_reproduce_warehouse_access_denied(db_session):
    """
    Reproduces the ERR_WAREHOUSE_ACCESS_DENIED during dispatch.
    Scenario:
    - Company: ad6cc8a6-34f9-42df-8f29-28254e0ad242
    - From WH: ce699eae-5db7-5d0a-a808-fd57a400523a
    - To WH: 386261e6-6a8c-5755-8e70-12287f2dd9f3
    - Transit ID derived from To WH: 537af6a5-cd97-50f0-9509-0d1f6226845e
    """
    # 1. Setup Data with exact IDs from user report
    COMPANY_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
    FROM_WH_ID = uuid.UUID("ce699eae-5db7-5d0a-a808-fd57a400523a")
    TO_WH_ID = uuid.UUID("386261e6-6a8c-5755-8e70-12287f2dd9f3")
    PRODUCT_ID = uuid.UUID("43988998-681e-5e8b-887b-f7641f1cf411")
    UOM_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
    
    # 2. Seed Source and Destination Warehouses
    src_wh = Warehouse(
        id=FROM_WH_ID,
        company_id=COMPANY_ID,
        tenant_id=COMPANY_ID,
        code="WH-SRC",
        name="Source Warehouse"
    )
    dest_wh = Warehouse(
        id=TO_WH_ID,
        company_id=COMPANY_ID,
        tenant_id=COMPANY_ID,
        code="WH-DEST",
        name="Destination Warehouse"
    )
    
    # 3. Seed Stock at Source
    stock = InventoryLevel(
        warehouse_id=FROM_WH_ID,
        product_id=PRODUCT_ID,
        company_id=COMPANY_ID,
        tenant_id=COMPANY_ID,
        uom_id=UOM_ID,
        quantity=Decimal("500")
    )
    
    db_session.add_all([src_wh, dest_wh, stock])
    await db_session.flush()
    await db_session.commit()
    
    # 4. Initialize Service
    repo = SQLAlchemyInventoryRepository(db_session)
    service = TransferService(repo)
    
    # 5. Execute Dispatch
    transfer_id = uuid.uuid4()
    
    # This call should pass after my previous fixes
    result = await service.dispatch_transfer(
        from_warehouse_id=FROM_WH_ID,
        to_warehouse_id=TO_WH_ID,
        product_id=PRODUCT_ID,
        quantity=Decimal("20"),
        uom_id=UOM_ID,
        weight=Decimal("10.5"),
        company_id=COMPANY_ID,
        transfer_id=transfer_id
    )
    
    assert result is not None
    
    # 6. Verify transit warehouse creation
    transit_id = uuid.uuid5(uuid.NAMESPACE_OID, f"{TO_WH_ID}_transit")
    stmt = select(Warehouse).where(Warehouse.id == transit_id)
    exec_res = await db_session.execute(stmt)
    transit_wh = exec_res.scalar_one_or_none()
    
    assert transit_wh is not None, "Transit warehouse should have been created"
    assert transit_wh.company_id == COMPANY_ID
    assert transit_wh.is_transit is True
