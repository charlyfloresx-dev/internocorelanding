import pytest
import uuid
from app.models.warehouse import Warehouse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

@pytest.mark.asyncio
async def test_warehouse_multitenant_creation(db_session: AsyncSession):
    company_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    
    # Simulate DB Create
    new_warehouse = Warehouse(
        id=warehouse_id,
        company_id=company_id,
        name="Main Storage",
        code="WH01",
        location="NY"
    )
    db_session.add(new_warehouse)
    await db_session.commit()
    
    # Validation via Repo logic (simulate tenant filter)
    stmt = select(Warehouse).filter_by(company_id=company_id, id=warehouse_id)
    result = await db_session.execute(stmt)
    saved_wh = result.scalar_one_or_none()
    
    assert saved_wh is not None
    assert saved_wh.company_id == company_id
    assert saved_wh.name == "Main Storage"
    
    # Secure against cross-tenant retrieval
    other_company_id = uuid.uuid4()
    hacked_stmt = select(Warehouse).filter_by(company_id=other_company_id, id=warehouse_id)
    hacked_res = await db_session.execute(hacked_stmt)
    assert hacked_res.scalar_one_or_none() is None
