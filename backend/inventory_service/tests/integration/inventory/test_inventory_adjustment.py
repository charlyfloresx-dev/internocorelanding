import pytest
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

from inventory_app.services.inventory import InventoryTransactionService
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.schemas.inventory import InventoryTransactionCreate
from inventory_app.models.inventory import TransactionType


def _mock_md_client() -> AsyncMock:
    client = AsyncMock()
    client.get_uom_factor.return_value = Decimal("1.0")
    client.validate_product.return_value = True
    client.get_product_internal_metadata.return_value = {}
    return client


@pytest.mark.asyncio
async def test_inventory_adjustment_creates_audit_trail(db_session):
    """
    UC-INV-02: A manual adjustment (ADJ_IN) must:
    - Record a Kardex entry with movement_type == 'ADJ_IN'
    - Update stock balance correctly
    - Serve as the audit trail for the operation
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    service = InventoryTransactionService(repo, md_client=_mock_md_client())

    company_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    product_id = uuid.uuid4()
    user_id = uuid.uuid4()

    cmd = InventoryTransactionCreate(
        transaction_type=TransactionType.ADJ_IN,
        warehouse_id=warehouse_id,
        product_id=product_id,
        uom_id=uuid.uuid4(),
        concept_id=uuid.uuid4(),
        quantity_change=Decimal("5.0"),
        weight=Decimal("0.0"),
        unit_cost=Decimal("0.0"),    # ✅ correct field (unit_price → unit_cost)
        currency="MXN",
        comments="Auditoría: Ajuste Manual por Sobrante"
    )

    result = await service.create_transaction(
        stmt=cmd,
        company_id=company_id,
        user_id=user_id,
        trace_id=uuid.uuid4(),
        module_token="TEST"
    )

    # ✅ MovementEntity uses .movement_type (string), not .transaction_type
    assert result.movement_type == TransactionType.ADJ_IN.value

    # Audit trail: stock balance must reflect the adjustment
    stock = await repo.get_stock(
        warehouse_id=warehouse_id,
        product_id=product_id,
        company_id=company_id
    )
    assert stock.quantity == Decimal("5.0")
