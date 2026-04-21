import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from master_app.main import master_app
from master_app.dependencies import get_current_user
from master_app.models.product import Product
from master_app.models.product_price import ProductPrice, UnitType
from master_app.models.price_agreement import PriceAgreement

@pytest.fixture
async def authenticated_client(async_client, mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield async_client
    app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.asyncio
async def test_get_product_prices_success(db, authenticated_client, mock_user):
    # 1. Setup product and price
    product = Product(
        id=uuid.uuid4(),
        sku="TEST-P",
        name="Test",
        company_id=mock_user.company_id,
        is_active=True
    )
    db.add(product)
    
    price = ProductPrice(
        id=uuid.uuid4(),
        product_id=product.id,
        company_id=mock_user.company_id,
        price_list_index=1,
        amount=Decimal("150.00"),
        currency="MXN",
        unit_type=UnitType.SALE,
        is_active=True
    )
    db.add(price)
    await db.commit()

    # 2. Call API
    response = await authenticated_client.get(f"/api/v1/prices/products/{product.id}/prices")
    
    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 1
    assert data["data"][0]["amount"] == "150.0000"
    assert data["data"][0]["currency"] == "MXN"

@pytest.mark.asyncio
async def test_upsert_price_agreement_flow(db, authenticated_client, mock_user):
    # 1. Setup
    product = Product(id=uuid.uuid4(), sku="B2B-P", name="B2B", company_id=mock_user.company_id)
    db.add(product)
    partner_id = uuid.uuid4()
    await db.commit()

    # 2. First Agreement
    payload = {
        "product_id": str(product.id),
        "partner_id": str(partner_id),
        "amount": 80.50,
        "currency": "USD"
    }
    resp1 = await authenticated_client.post("/api/v1/prices/agreements", json=payload)
    assert resp1.status_code == 201
    agreement_v1_id = resp1.json()["data"]["id"]

    # 3. Update Agreement (Soft-Close & Insert)
    payload["amount"] = 75.00
    resp2 = await authenticated_client.post("/api/v1/prices/agreements", json=payload)
    assert resp2.status_code == 201
    agreement_v2_id = resp2.json()["data"]["id"]
    assert agreement_v2_id != agreement_v1_id

    # 4. Verify in DB
    from sqlalchemy import select
    stmt = select(PriceAgreement).where(PriceAgreement.product_id == product.id)
    result = await db.execute(stmt)
    agreements = result.scalars().all()
    assert len(agreements) == 2
    
    active = [a for a in agreements if a.valid_until is None]
    closed = [a for a in agreements if a.valid_until is not None]
    assert len(active) == 1
    assert len(closed) == 1
    assert active[0].amount == Decimal("75.00")
    assert closed[0].amount == Decimal("80.50")
