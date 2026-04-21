import pytest
import uuid
from decimal import Decimal
from inventory_app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.domain.entities.transfer_entities import InitiateTransferCommand, TransferStatusEnum
from inventory_app.models.warehouse import Warehouse
from inventory_app.models.inventory import InventoryLevel


@pytest.mark.asyncio
async def test_internal_transfer_between_warehouses(db_session):
    """
    UC-INV-03: ICT flow — Company A dispatches to Company B.

    NOTE: InitiateTransferCommand enforces origin_company_id != destination_company_id
    (ERR_SAME_COMPANY_TRANSFER). This test uses two different companies to represent
    an *inter-company* transfer, which is the domain model's intended use case.
    For intra-company warehouse moves, use the internal TRANSFER transaction type instead.
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)

    company_a_id = uuid.uuid4()   # ✅ origin company
    company_b_id = uuid.uuid4()   # ✅ destination company (different from A)
    origin_warehouse_id = uuid.uuid4()
    dest_warehouse_id = uuid.uuid4()
    product_id = uuid.uuid4()
    uom_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # ── Pre-condition: seed origin warehouse and stock in Company A ─────────
    origin_wh = Warehouse(
        id=origin_warehouse_id,
        company_id=company_a_id,
        code="WH-A",
        name="Origin Warehouse"
    )
    db_session.add(origin_wh)

    dest_wh = Warehouse(
        id=dest_warehouse_id,
        company_id=company_b_id,
        code="WH-B",
        name="Destination Warehouse"
    )
    db_session.add(dest_wh)

    # Seed sufficient stock to avoid ERR_INSUFFICIENT_STOCK
    initial_stock = InventoryLevel(
        id=uuid.uuid4(),
        company_id=company_a_id,
        warehouse_id=origin_warehouse_id,
        product_id=product_id,
        uom_id=uom_id,
        quantity=Decimal("100.0"),
    )
    db_session.add(initial_stock)
    await db_session.flush()

    # ── ICT Command ─────────────────────────────────────────────────────────
    command = InitiateTransferCommand(
        origin_company_id=company_a_id,
        initiated_by=user_id,
        destination_company_id=company_b_id,   # ✅ different company — passes validation
        destination_warehouse_id=dest_warehouse_id,
        origin_warehouse_id=origin_warehouse_id,
        product_id=product_id,
        uom_id=uom_id,
        quantity=Decimal("50.0"),
        weight=Decimal("0.0"),
        transfer_price=Decimal("15.5"),
        currency="USD"
    )

    result = await handler.initiate_transfer(command)

    # ── Assertions ──────────────────────────────────────────────────────────
    assert result is not None
    assert result.status == TransferStatusEnum.SHIPPED
    assert result.origin.company_id == company_a_id
    assert result.destination.company_id == company_b_id
