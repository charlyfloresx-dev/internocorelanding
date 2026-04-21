import pytest
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

from inventory_app.services.inventory import InventoryTransactionService
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.schemas.inventory import InventoryTransactionCreate
from inventory_app.models.inventory import TransactionType


def _mock_md_client() -> AsyncMock:
    """
    Provides a lightweight mock of IMasterDataClient.
    The service calls:
      - get_uom_factor()        → returns Decimal factor (1.0 is neutral)
      - validate_product()      → returns True (product is valid)
      - get_product_internal_metadata() → not needed for IN transactions
    """
    client = AsyncMock()
    client.get_uom_factor.return_value = Decimal("1.0")
    client.validate_product.return_value = True
    client.get_product_internal_metadata.return_value = {}
    return client


@pytest.mark.asyncio
async def test_receive_stock_updates_kardex_and_balance(db_session):
    """
    UC-INV-01: Receiving inventory (IN) must:
    - Persist a MovementEntity (Kardex entry)
    - Update the InventoryLevel balance to reflect the received quantity
    - Respect multi-tenancy (company_id scoping)
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    service = InventoryTransactionService(repo, md_client=_mock_md_client())

    company_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    product_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Command — uses correct schema field names
    command = InventoryTransactionCreate(
        transaction_type=TransactionType.IN,
        warehouse_id=warehouse_id,
        product_id=product_id,
        uom_id=uuid.uuid4(),
        concept_id=uuid.uuid4(),
        quantity_change=Decimal("100.0"),
        weight=Decimal("0.0"),
        unit_cost=Decimal("10.50"),   # ✅ correct field name (was unit_price)
        currency="USD",
        comments="Receipt Validation"
    )

    # Execute
    result = await service.create_transaction(
        stmt=command,
        company_id=company_id,
        user_id=user_id,
        trace_id=uuid.uuid4(),
        module_token="TEST"
    )

    # MovementEntity assertions
    assert result is not None
    assert result.quantity == Decimal("100.0")   # ✅ MovementEntity uses .quantity

    # Validate stock balance via repository
    stock = await repo.get_stock(
        warehouse_id=warehouse_id,
        product_id=product_id,
        company_id=company_id
    )
    assert stock is not None
    assert stock.quantity == Decimal("100.0")
    assert stock.company_id == company_id
