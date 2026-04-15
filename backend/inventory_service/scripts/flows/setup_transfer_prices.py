import asyncio
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# ─── CONFIGURACIÓN ───
MASTER_DATA_URL = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"
CO_ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
CO_LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")

PRODUCT_DATA = [
    {"id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000001"), "name": "Engine Control Module (ECM)", "sku": "ECM-600"},
    {"id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000002"), "name": "Turbocharger Assembly", "sku": "TRB-700"},
    {"id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000003"), "name": "Brake Disc Rotor", "sku": "BRK-800"},
    {"id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000004"), "name": "Fuel Injector Set", "sku": "FLI-900"},
    {"id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000005"), "name": "Suspension Damper", "sku": "SUS-100"},
]

async def setup_prices():
    engine = create_async_engine(MASTER_DATA_URL)
    
    async with engine.begin() as conn:
        print("==================================================")
        print("🚀 CONFIGURANDO PRECIOS DE TRANSFERENCIA")
        print("==================================================")

        for prod in PRODUCT_DATA:
            print(f"\n📦 Producto: {prod['name']}")
            
            # 1. Asegurar que el producto existe en Master Data
            await conn.execute(text("""
                INSERT INTO products (
                    id, name, sku, code, status, product_type,
                    requires_batch, requires_expiration, is_taxable, allow_price_override,
                    created_at, company_id, tenant_id, is_active, version_id
                )
                VALUES (
                    :id, :name, :sku, :sku, 'ACTIVE', 'GOODS',
                    FALSE, FALSE, TRUE, TRUE,
                    NOW(), :co_id, :co_id, TRUE, 1
                )
                ON CONFLICT (id) DO NOTHING;
            """), {"id": prod['id'], "name": prod['name'], "sku": prod['sku'], "co_id": CO_ENTERPRISE_ID})

            # 2. Precio de Transferencia: Enterprise -> Logistics MX (Price List 4 - MXN)
            # +10% sobre base (Base assumption: ECM 450 -> 495)
            # Link a cada producto con markups
            base_prices = {
                "ECM-600": 495.0,
                "TRB-700": 1320.0,
                "BRK-800": 165.0,
                "FLI-900": 352.0,
                "SUS-100": 308.0
            }
            price_mxn = base_prices[prod['sku']]
            
            await conn.execute(text("""
                INSERT INTO product_prices (
                    id, product_id, price_list_index, amount, currency, 
                    unit_type, is_active, is_manual, version_id, company_id, tenant_id
                )
                VALUES (
                    :id, :prod_id, 4, :amount, 'MXN', 
                    'SALE', TRUE, FALSE, 1, :co_id, :co_id
                )
                ON CONFLICT (company_id, product_id, price_list_index, unit_type, warehouse_id, currency) 
                DO UPDATE SET amount = EXCLUDED.amount;
            """), {
                "id": uuid.uuid4(),
                "prod_id": prod['id'],
                "amount": Decimal(str(price_mxn)),
                "co_id": CO_ENTERPRISE_ID
            })
            print(f"   ↳ [MX] Enterprise -> Logistics MX: ${price_mxn} MXN")

            # 3. Precio de Transferencia: Logistics MX -> Logistics US (Price List 5 - USD)
            # +20% sobre precio MXN y conversión a USD (~20)
            # (495 * 1.2) / 20 = 29.70
            mx_to_us_prices = {
                "ECM-600": 29.70,
                "TRB-700": 79.20,
                "BRK-800": 9.90,
                "FLI-900": 21.12,
                "SUS-100": 18.48
            }
            price_usd = mx_to_us_prices[prod['sku']]

            await conn.execute(text("""
                INSERT INTO product_prices (
                    id, product_id, price_list_index, amount, currency, 
                    unit_type, is_active, is_manual, version_id, company_id, tenant_id
                )
                VALUES (
                    :id, :prod_id, 4, :amount, 'USD', 
                    'SALE', TRUE, FALSE, 1, :co_id, :co_id
                )
                ON CONFLICT (company_id, product_id, price_list_index, unit_type, warehouse_id, currency) 
                DO UPDATE SET amount = EXCLUDED.amount;
            """), {
                "id": uuid.uuid4(),
                "prod_id": prod['id'],
                "amount": Decimal(str(price_usd)),
                "co_id": CO_LOGISTICS_MX_ID  # Propiedad de Logistics MX para vender a US
            })
            print(f"   ↳ [US] Logistics MX -> Logistics US: ${price_usd} USD")

    await engine.dispose()
    print("\n✅ Precios de transferencia configurados.")

if __name__ == "__main__":
    asyncio.run(setup_prices())
