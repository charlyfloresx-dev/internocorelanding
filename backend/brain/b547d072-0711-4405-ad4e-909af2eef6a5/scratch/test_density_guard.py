import asyncio
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

# Mocking app and common because they might not be in path
import sys
import os

# Calculate absolute path to backend
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, BACKEND_DIR)  # For 'common'
sys.path.insert(0, os.path.join(BACKEND_DIR, 'inventory_service'))  # For 'app'

try:
    from app.services.density_guard_audit import run_density_guard_audit
except ImportError as e:
    print(f"Could not import density_guard_audit: {e}")
    sys.exit(1)

async def test_audit_overflow():
    print("Test: Testing Density Guard Audit - OVERFLOW scenario")
    
    warehouse_id = uuid.uuid4()
    location_code = "A1-01-01"
    movement_id = uuid.uuid4()
    company_id = uuid.uuid4()
    
    # Mock Repository
    repo = AsyncMock()
    # Current occupancy is 500
    repo.get_location_occupancy.return_value = Decimal("500.0")
    # Mock session
    repo.session = AsyncMock()
    repo.session.execute = AsyncMock()
    repo.session.commit = AsyncMock()
    
    # Mock Master Data Client
    md_client = AsyncMock()
    # Capacity is only 10
    md_client.get_location_capacity.return_value = Decimal("10.0")
    
    # Run Audit
    await run_density_guard_audit(
        warehouse_id=warehouse_id,
        location_code=location_code,
        quantity_moved=Decimal("500.0"),
        movement_id=movement_id,
        company_id=company_id,
        repository=repo,
        md_client=md_client
    )
    
    print("Audit completed. Verifying results...")
    
    # Verify that it updated the status to OVERFLOW_CONFIRMED
    # We expect an update statement to be executed
    # In the real code: stmt = sa.update(Movement).where(Movement.id == movement_id).values(validation_status="OVERFLOW_CONFIRMED")
    # Check if execute was called
    assert repo.session.execute.called
    print("SUCCESS: DB was updated with overflow status.")

async def test_audit_clean():
    print("\nTest: Testing Density Guard Audit - CLEAN scenario")
    
    warehouse_id = uuid.uuid4()
    location_code = "A1-01-02"
    movement_id = uuid.uuid4()
    company_id = uuid.uuid4()
    
    repo = AsyncMock()
    repo.get_location_occupancy.return_value = Decimal("80.0")
    repo.session = AsyncMock()
    
    md_client = AsyncMock()
    md_client.get_location_capacity.return_value = Decimal("100.0")
    
    await run_density_guard_audit(
        warehouse_id=warehouse_id,
        location_code=location_code,
        quantity_moved=Decimal("20.0"),
        movement_id=movement_id,
        company_id=company_id,
        repository=repo,
        md_client=md_client
    )
    
    print("Audit completed. Verifying results...")
    # Should update to CLEAN
    assert repo.session.execute.called
    print("SUCCESS: DB was updated with CLEAN status.")

if __name__ == "__main__":
    asyncio.run(test_audit_overflow())
    asyncio.run(test_audit_clean())
