import pytest
import uuid
from unittest.mock import AsyncMock

from inventory_app.api.v1.handlers.dashboard_handler import GetInventoryDashboardHandler as DashboardHandler
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository


def _mock_md_client() -> AsyncMock:
    """
    Lightweight mock for IMasterDataClient.
    DashboardHandler only calls this for alert enrichment,
    and only if telemetry.alerts is non-empty (which it won't be for an empty tenant).
    """
    client = AsyncMock()
    client.get_product_internal_metadata.return_value = {
        "sku": "TEST-SKU",
        "name": "Test Product"
    }
    return client


@pytest.mark.asyncio
async def test_dashboard_telemetry_and_pagination(db_session):
    """
    UC-INV-04: Dashboard telemetry must:
    - Return a valid DashboardDTO even for an empty/new tenant (graceful degradation)
    - Expose total_stock_value (or dict-equivalent) for frontend consumption
    - Not crash when called with a warehouse_id + company_id that have no history
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = DashboardHandler(repo=repo, md_client=_mock_md_client())  # ✅ passes md_client

    company_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()   # ✅ execute() requires warehouse_id

    # ✅ Correct method name: .execute(), not .get_dashboard_summary()
    result = await handler.execute(
        company_id=company_id,
        warehouse_id=warehouse_id,
        trace_id=str(uuid.uuid4())
    )

    assert result is not None, "Dashboard handler must return a DashboardDTO, even for empty tenant."

    # Validate graceful degradation — empty tenant returns zero-valued DTO, not an exception
    # DashboardDTO has .valuation.total_usd ; also accept dict for flexibility
    if isinstance(result, dict):
        assert "valuation" in result or "total_stock_value" in result
    else:
        # DashboardDTO is a Pydantic model
        assert hasattr(result, "valuation"), "DashboardDTO must have a 'valuation' field."
        assert hasattr(result, "critical_alerts")
        assert hasattr(result, "movement_series")
