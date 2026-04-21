import pytest
import uuid
import datetime
from decimal import Decimal
from httpx import AsyncClient, ASGITransport
from jose import jwt
from common.config import settings

from master_app.main import master_app
from master_app.models.product_price import UnitType
from master_app.models.product import Product

@pytest.fixture
async def product_factory(db):
    async def _create(company_id: uuid.UUID):
        prod = Product(
            sku=f"SKU-{uuid.uuid4().hex[:6]}",
            name="Test Product",
            company_id=company_id,
            product_type="GOODS",
            is_active=True
        )
        db.add(prod)
        await db.flush()
        return prod
    return _create

from master_app.db.session import get_db

@pytest.mark.asyncio
async def test_cross_service_price_fetch(db, product_factory):
    # Override get_db to use test session
    async def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    # Setup Tenant IDs (Simulating Tijuana and Enterprise)
    tenant_tijuana = uuid.uuid4()
    tenant_enterprise = uuid.uuid4()
    
    # 1. Base Setup: Crear un producto comun que existe en Tijuana (o es compartido)
    product_tijuana = await product_factory(tenant_tijuana)
    
    # Insert prices for the product in Tijuana
    from master_app.infrastructure.repositories.sqlalchemy_master_data_repository import SQLAlchemyMasterDataRepository
    repo = SQLAlchemyMasterDataRepository(db)
    
    # Precio Tijuana: MXN
    await repo.upsert_product_price({
        "product_id": product_tijuana.id,
        "price_list_index": 1,
        "unit_type": UnitType.SALE,
        "currency": "MXN",
        "value": Decimal("150.00"),
        "is_manual": False
    }, tenant_tijuana)
    
    # Setup JWT Mock Function
    def _generate_jwt_for_tenant(company_id: uuid.UUID) -> str:
        payload = {
            "sub": str(uuid.uuid4()), # user_id
            "company_id": str(company_id),
            "role": "OPERATOR",
            "role_names": ["operator"],
            "scopes": [],
            "accessible_warehouses": [],
            "modules": ["auth_core", "master_data"],
            "status": "ACTIVE",
            "readonly": False,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # Diagnostic: check db
    from sqlalchemy import select
    from master_app.models.product import Product
    diag = await db.execute(select(Product).where(Product.company_id == tenant_tijuana))
    diag_prod = diag.scalar_one_or_none()
    assert diag_prod is not None, "Product missing in db before HTTP call"
    assert diag_prod.id == product_tijuana.id, "Product ID mismatch"
    
    # Transport and Client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # --- SCENARIO 1: Tenant Tijuana fetches its own price ---
        token_tijuana = _generate_jwt_for_tenant(tenant_tijuana)
        headers_tijuana = {
            "Authorization": f"Bearer {token_tijuana}",
            "X-Company-ID": str(tenant_tijuana)
        }
        
        response = await client.get(
            f"/api/v1/prices/products/{product_tijuana.id}/prices/resolve",
            params={"currency": "MXN"},
            headers=headers_tijuana
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert Decimal(str(data["resolved_amount"])) == Decimal("150.00")
        assert data["currency"] == "MXN"
        
        # --- SCENARIO 2: Create Enterprise Product and fetch USD ---
        product_enterprise = await product_factory(tenant_enterprise)
        await repo.upsert_product_price({
            "product_id": product_enterprise.id,
            "price_list_index": 1,
            "unit_type": UnitType.SALE,
            "currency": "USD",
            "value": Decimal("12.50"),
            "is_manual": False
        }, tenant_enterprise)
        
        token_enterprise = _generate_jwt_for_tenant(tenant_enterprise)
        headers_enterprise = {
            "Authorization": f"Bearer {token_enterprise}",
            "X-Company-ID": str(tenant_enterprise)
        }
        
        resp_ent = await client.get(
            f"/api/v1/prices/products/{product_enterprise.id}/prices/resolve",
            params={"currency": "USD"},
            headers=headers_enterprise
        )
        assert resp_ent.status_code == 200, resp_ent.text
        data_ent = resp_ent.json()["data"]
        assert Decimal(str(data_ent["resolved_amount"])) == Decimal("12.50")
        assert data_ent["currency"] == "USD"
        
        # --- SCENARIO 3: Security - Tijuana tries to fetch Enterprise price ---
        headers_tijuana_invalid = {
            "Authorization": f"Bearer {token_tijuana}",
            "X-Company-ID": str(tenant_enterprise)
        }
        resp_forbidden = await client.get(
            f"/api/v1/prices/products/{product_enterprise.id}/prices/resolve",
            params={"currency": "USD"},
            headers=headers_tijuana_invalid
        )
        
        # El middleware de seguridad o el endpoint debe devolver un 404 (No found porque busca por company_id) o un 403 Forbidden.
        # Debido al where(company_id == current_user.company_id), devolvera 404 Not Found porque el producto no existe en el contexto del tenant.
        # Confirmamos el aislamiento multi-tenant
        assert resp_forbidden.status_code == 403 
