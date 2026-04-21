import sys
import os
import asyncio
from sqlalchemy import select

# Añadimos los paths necesarios
sys.path.append(os.path.join(os.getcwd(), "backend", "master_data_service"))
sys.path.append(os.path.join(os.getcwd(), "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Replace the inner function configuration
def get_session_factory():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

from master_app.models.product_price import ProductPrice
from master_app.models.price_agreement import PriceAgreement
from master_app.models.product import Product

async def check_prices():
    print("--- [AUDITORIA] DE PRECIOS Y ACUERDOS ---")
    async_session = get_session_factory()
    async with async_session() as session:
        # Check ProductPrices
        print("\n=> Product Prices:")
        stmt = select(ProductPrice, Product.sku).join(Product).order_by(Product.sku, ProductPrice.price_list_index, ProductPrice._amount)
        result = await session.execute(stmt)
        for price, sku in result.yield_per(100):
            status = "[ACTIVO]" if price.is_active else f"[CERRADO] ({price.valid_until})"
            print(f"[{sku}] Lista {price.price_list_index} | Monto: {price._amount} {price._currency} | Estado: {status}")
            
        # Check Price Agreements
        print("\n=> Price Agreements (B2B):")
        stmt_ag = select(PriceAgreement, Product.sku).join(Product).order_by(Product.sku, PriceAgreement.amount)
        result_ag = await session.execute(stmt_ag)
        for ag, sku in result_ag.yield_per(100):
            status = "[ACTIVO]" if ag.valid_until is None else f"[CERRADO] ({ag.valid_until})"
            print(f"[{sku}] Acuerdo | Monto: {ag.amount} {ag.currency} | Estado: {status}")

if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"
    asyncio.run(check_prices())
