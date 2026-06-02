import uuid
import pytest
import httpx
from datetime import date
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from httpx import AsyncClient, HTTPStatusError

from mes_app.main import app
from mes_app.models.production_run import ProductionRun
from mes_app.models.labor_allocation import LaborAllocation
from mes_app.models.resource import Resource
from mes_app.models.facility import Facility
from mes_app.models.production_area import ProductionArea
from mes_app.core.enums import LaborRole
from mes_app.infrastructure.clients.hcm_client import HCMClient

# ── Mocking scopes/JWT dependencies to bypass auth for testing endpoint directly ──
from common.security.dependencies import require_scope, get_current_active_user
from common.security.auth_payload import TokenPayload
app.dependency_overrides[require_scope(["mes:write"])] = lambda: True
app.dependency_overrides[require_scope(["mes:read"])] = lambda: True
app.dependency_overrides[get_current_active_user] = lambda: TokenPayload(
    sub="test-user",
    company_id=uuid.uuid4(),
    role="OPERATOR",
    role_names=["operator"],
    scopes=["mes:write", "mes:read"]
)


@pytest.mark.asyncio
async def test_hcm_client_resilience_and_timeout():
    """HCMClient must handle HTTPX exceptions gracefully and return None."""
    client = HCMClient()
    collaborator_id = uuid.uuid4()
    company_id = uuid.uuid4()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Simulate standard Timeout
        mock_get.side_effect = httpx.TimeoutException("Connection timed out")
        res = await client.get_collaborator(collaborator_id, company_id)
        assert res is None, "HCMClient must return None on Timeout without raising exceptions"

        # Simulate 500 Internal Server Error
        mock_get.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=httpx.Request("GET", "http://hcm-service/api/v1/collaborators/1"),
            response=httpx.Response(500)
        )
        res = await client.get_collaborator(collaborator_id, company_id)
        assert res is None, "HCMClient must return None on status 500 without raising exceptions"


@pytest.mark.asyncio
async def test_multi_tenant_bulk_assignment_isolation(db_session):
    """
    Multi-tenant Attack Simulation:
    Company A attempts to assign collaborators to Company B's Production Run.
    The endpoint must fail with 404 or 403 Forbidden.
    """
    company_a = uuid.uuid4()
    company_b = uuid.uuid4()

    # 1. Create hierarchy (Facility -> ProductionArea -> Resource) for Company B
    facility = Facility(
        id=uuid.uuid4(),
        company_id=company_b,
        tenant_id=company_b,
        code="FAC-B",
        name="Facility B"
    )
    db_session.add(facility)
    await db_session.flush()

    area = ProductionArea(
        id=uuid.uuid4(),
        company_id=company_b,
        tenant_id=company_b,
        name="Area B",
        facility_id=facility.id
    )
    db_session.add(area)
    await db_session.flush()

    res_b = Resource(
        id=uuid.uuid4(),
        company_id=company_b,
        tenant_id=company_b,
        code="RES-B",
        name="Resource B",
        production_area_id=area.id
    )
    db_session.add(res_b)
    await db_session.flush()

    # Create WorkOrder for Company B
    from mes_app.models.work_order import WorkOrder
    from mes_app.core.enums import WOType
    wo_num_b = f"WO-B-{uuid.uuid4().hex[:8]}"
    wo_b = WorkOrder(
        id=uuid.uuid4(),
        company_id=company_b,
        tenant_id=company_b,
        order_number=wo_num_b,
        item_code="ITEM-999",
        order_quantity=100,
        status="DRAFT",
        wo_type=WOType.STANDARD
    )
    db_session.add(wo_b)
    await db_session.flush()

    # 2. Create a ProductionRun belonging to Company B
    run_b = ProductionRun(
        id=uuid.uuid4(),
        company_id=company_b,
        tenant_id=company_b,
        work_order_id=wo_b.id,
        resource_id=res_b.id,
        shift_id=uuid.uuid4(),
        date=date.today(),
        leader_collaborator_id=None,
        supervisor_collaborator_id=None,
        planned_quantity=100,
        actual_quantity=0,
        status="SCHEDULED",
    )
    db_session.add(run_b)
    await db_session.flush()

    # 3. Setup the request body for bulk assignment
    payload = {
        "production_run_id": str(run_b.id),
        "assignments": [
            {"collaborator_id": str(uuid.uuid4()), "role": "OPERATOR"}
        ]
    }

    # 4. Simulate calling the FastAPI endpoint with Company A headers (Attack)
    headers = {
        "X-Company-ID": str(company_a),
        "Content-Type": "application/json"
    }

    # Override get_current_company to return Company A
    from mes_app.dependencies import get_current_company
    app.dependency_overrides[get_current_company] = lambda: company_a

    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/mes/labor/assign", json=payload, headers=headers)
        
        # Attack must be rejected with 404 or 403
        assert response.status_code in [403, 404]

    # Cleanup overrides
    app.dependency_overrides.pop(get_current_company, None)


@pytest.mark.asyncio
async def test_atomic_bulk_assignment_clears_previous(db_session):
    """Bulk assignment must atomically clean old records and replace them."""
    company_id = uuid.uuid4()

    # Create hierarchy (Facility -> ProductionArea -> Resource) for Company
    facility = Facility(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        code="FAC-A",
        name="Facility A"
    )
    db_session.add(facility)
    await db_session.flush()

    area = ProductionArea(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        name="Area A",
        facility_id=facility.id
    )
    db_session.add(area)
    await db_session.flush()

    res = Resource(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        code="RES-A",
        name="Resource A",
        production_area_id=area.id
    )
    db_session.add(res)
    await db_session.flush()

    # Create WorkOrder for Company
    from mes_app.models.work_order import WorkOrder
    from mes_app.core.enums import WOType
    wo_num = f"WO-A-{uuid.uuid4().hex[:8]}"
    wo = WorkOrder(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        order_number=wo_num,
        item_code="ITEM-888",
        order_quantity=50,
        status="DRAFT",
        wo_type=WOType.STANDARD
    )
    db_session.add(wo)
    await db_session.flush()

    # Create run
    run = ProductionRun(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        work_order_id=wo.id,
        resource_id=res.id,
        shift_id=uuid.uuid4(),
        date=date.today(),
        planned_quantity=10,
        status="SCHEDULED",
    )
    db_session.add(run)
    await db_session.flush()

    # Create previous allocations
    alloc1 = LaborAllocation(
        id=uuid.uuid4(),
        production_run_id=run.id,
        collaborator_id=uuid.uuid4(),
        role="LEADER",
        shift_id=run.shift_id,
        company_id=company_id,
        tenant_id=company_id,
    )
    db_session.add(alloc1)
    await db_session.flush()

    # Request new assignments (using snake_case keys as required by BulkAssignRequest schema)
    payload = {
        "production_run_id": str(run.id),
        "assignments": [
            {"collaborator_id": str(uuid.uuid4()), "role": "OPERATOR"},
            {"collaborator_id": str(uuid.uuid4()), "role": "INSPECTOR"}
        ]
    }

    headers = {
        "X-Company-ID": str(company_id),
        "X-Admin-Master-Key": "ROTATED_MASTER_KEY_GOD_MODE",
        "Content-Type": "application/json"
    }

    from mes_app.dependencies import get_current_company, get_db
    app.dependency_overrides[get_current_company] = lambda: company_id
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/mes/labor/assign", json=payload, headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["assigned"] == 2
        assert body["data"]["removed"] == 1

    # Cleanup overrides
    app.dependency_overrides.pop(get_current_company, None)
    app.dependency_overrides.pop(get_db, None)

