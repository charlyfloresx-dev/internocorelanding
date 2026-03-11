import pytest
from datetime import datetime, timedelta
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.product_price import ProductPrice, PriceType, PriceOriginType
from app.infrastructure.repositories import ProductPriceRepository

@pytest.mark.asyncio
async def test_pricing_audit_append_only(db_session: AsyncSession):
    # Setup
    repo = ProductPriceRepository(db_session)
    product_id = uuid.uuid4()
    company_id = uuid.uuid4()

    # Create Initial Price (Version 1)
    initial_price = ProductPrice(
        product_id=product_id,
        company_id=company_id,
        price_type=PriceType.SALE,
        amount=Decimal("10.00"),
        currency_code="USD",
        change_reason="Precio Base Inicial"
    )

    saved_initial = await repo.upsert_with_audit(initial_price)
    assert saved_initial.version == 1
    assert saved_initial.end_date is None
    
    # Store its start date to verify proper truncation later
    start_v1 = saved_initial.start_date

    # Wait a tiny bit (mocking time logically, but we rely on utcnow in upsert)
    # the upsert uses utcnow internally, so we just run the second one.

    # Create Updated Price (Version 2)
    updated_price = ProductPrice(
        product_id=product_id,
        company_id=company_id,
        price_type=PriceType.SALE, # same context
        amount=Decimal("12.50"),   # new amount
        currency_code="USD",
        change_reason="Ajuste por Inflación 2026"
    )

    saved_updated = await repo.upsert_with_audit(updated_price)

    assert saved_updated.version == 2
    assert saved_updated.end_date is None
    assert saved_updated.amount == Decimal("12.50")
    assert saved_updated.change_reason == "Ajuste por Inflación 2026"

    # Verify that Version 1 was correctly closed
    # Re-fetch V1 from DB to ensure flush was applied
    stmt = select(ProductPrice).where(ProductPrice.id == saved_initial.id)
    result = await db_session.execute(stmt)
    v1_refetched = result.scalar_one()

    # The end_date of V1 must be precisely before the start_date of V2
    assert v1_refetched.end_date is not None
    # End date should be just before V2 starts (since start_date = now and end_date = now - 1 microsecond)
    # The diff should be exactly 1 microsecond in the logic
    diff = saved_updated.start_date - v1_refetched.end_date
    assert diff == timedelta(microseconds=1)

    # Verify get_effective_price uses the latest version
    effective = await repo.get_effective_price(product_id, company_id)
    assert effective is not None
    assert effective.amount == Decimal("12.50")
    assert effective.version == 2
