import pytest
import uuid
from decimal import Decimal
from master_app.infrastructure.repositories.sqlalchemy_master_data_repository import SQLAlchemyMasterDataRepository
from master_app.models.product import Product
from master_app.models.product_price import UnitType

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

@pytest.mark.asyncio
async def test_price_upsert_logic(db, product_factory):
    """
    Verifica que al llamar a upsert_product_price:
    1. El registro anterior se cierre con 'valid_until'.
    2. El nuevo registro se cree con ID distinto y valid_until=None.
    """
    repo = SQLAlchemyMasterDataRepository(db)
    company_id = uuid.uuid4()
    product = await product_factory(company_id)
    
    price_data_v1 = {
        "product_id": product.id,
        "price_list_index": 1,
        "unit_type": UnitType.SALE,
        "currency": "MXN",
        "value": Decimal("100.00"),
        "is_manual": False
    }
    
    # 1. Crear primer precio
    price_v1 = await repo.upsert_product_price(price_data_v1, company_id)
    assert price_v1._amount == Decimal("100.00")
    assert price_v1.valid_until is None
    assert price_v1.is_active is True
    
    # 2. Upsert con nuevo valor ($120.00)
    price_data_v2 = price_data_v1.copy()
    price_data_v2["value"] = Decimal("120.00")
    
    price_v2 = await repo.upsert_product_price(price_data_v2, company_id)
    
    # Validaciones
    assert price_v2.id != price_v1.id
    assert price_v2._amount == Decimal("120.00")
    assert price_v2.valid_until is None
    assert price_v2.is_active is True
    
    # El registro anterior (v1) debe estar cerrado
    await db.refresh(price_v1)
    assert price_v1.valid_until is not None
    assert price_v1.is_active is False
    assert price_v1._amount == Decimal("100.00")

@pytest.mark.asyncio
async def test_manual_override_flag(db, product_factory):
    """
    Verifica que el flag is_manual se guarde correctamente para auditor\u00eda.
    """
    repo = SQLAlchemyMasterDataRepository(db)
    company_id = uuid.uuid4()
    product = await product_factory(company_id)
    
    manual_price_data = {
        "product_id": product.id,
        "price_list_index": 0, # Excepci\u00f3n o manual
        "unit_type": UnitType.SALE,
        "currency": "USD",
        "value": Decimal("50.00"),
        "is_manual": True
    }
    
    price = await repo.upsert_product_price(manual_price_data, company_id)
    assert price.is_manual is True
    assert price._amount == Decimal("50.00")
