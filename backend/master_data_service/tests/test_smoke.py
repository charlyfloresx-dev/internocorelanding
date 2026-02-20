import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Verifica que el endpoint de salud responda correctamente."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "master_data_service"

@pytest.mark.asyncio
async def test_um_creation(db, um_factory):
    """Verifica el mapeo del modelo UM con la nueva arquitectura domain."""
    um = await um_factory(code="KG", name="Kilogram")
    assert um.id is not None
    assert um.code == "KG"
    assert um.is_active is True  # Verificando herencia de BaseDomainEntity
    assert um.created_at is not None # Verificando herencia de AuditBase

@pytest.mark.asyncio
async def test_category_creation(db, category_factory):
    """Verifica el mapeo del modelo ProductCategory."""
    cat = await category_factory(name="Raw Materials")
    assert cat.id is not None
    assert cat.name == "Raw Materials"
    assert cat.company_id is not None # Verificando herencia de MultiTenantBase
