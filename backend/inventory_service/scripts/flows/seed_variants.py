import asyncio
import uuid
import sys
import os
from decimal import Decimal
from datetime import datetime, timezone

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from inventory_app.db.session import AsyncSessionLocal
from sqlalchemy import text

# ─── CONFIGURACIÓN ───
CO_ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")

# Datos de 5 Números de Parte (Productos) con 3 variantes cada uno
PRODUCT_CATALOG = [
    {
        "name": "Engine Control Module (ECM)",
        "sku": "ECM-600",
        "id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000001"),
        "variants": [
            {"brand": "Bosch", "mpn": "MPN-BOS-601", "price": 450.0, "weight": 1.2},
            {"brand": "Denso", "mpn": "MPN-DEN-602", "price": 485.0, "weight": 1.1},
            {"brand": "Magneti Marelli", "mpn": "MPN-MM-603", "price": 420.0, "weight": 1.3},
        ]
    },
    {
        "name": "Turbocharger Assembly",
        "sku": "TRB-700",
        "id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000002"),
        "variants": [
            {"brand": "Garrett", "mpn": "MPN-GAR-701", "price": 1200.0, "weight": 5.5},
            {"brand": "BorgWarner", "mpn": "MPN-BOR-702", "price": 1150.0, "weight": 5.8},
            {"brand": "Mitsubishi", "mpn": "MPN-MHI-703", "price": 1100.0, "weight": 5.6},
        ]
    },
    {
        "name": "Brake Disc Rotor",
        "sku": "BRK-800",
        "id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000003"),
        "variants": [
            {"brand": "Brembo", "mpn": "MPN-BRE-801", "price": 150.0, "weight": 8.5},
            {"brand": "Akebono", "mpn": "MPN-AKE-802", "price": 135.0, "weight": 8.0},
            {"brand": "Bosch", "mpn": "MPN-BOS-803", "price": 110.0, "weight": 8.2},
        ]
    },
    {
        "name": "Fuel Injector Set",
        "sku": "FLI-900",
        "id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000004"),
        "variants": [
            {"brand": "Siemens VDO", "mpn": "MPN-SIE-901", "price": 320.0, "weight": 0.4},
            {"brand": "Delphi Pro", "mpn": "MPN-DEL-902", "price": 310.0, "weight": 0.4},
            {"brand": "Hitachi Power", "mpn": "MPN-HIT-903", "price": 295.0, "weight": 0.5},
        ]
    },
    {
        "name": "Suspension Damper",
        "sku": "SUS-100",
        "id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000005"),
        "variants": [
            {"brand": "Bilstein", "mpn": "MPN-BIL-101", "price": 280.0, "weight": 3.2},
            {"brand": "Ohlins", "mpn": "MPN-OHL-102", "price": 550.0, "weight": 2.8},
            {"brand": "KYB", "mpn": "MPN-KYB-103", "price": 145.0, "weight": 3.5},
        ]
    }
]

async def seed_variants():
    print("==================================================")
    print("SEED: REGISTRANDO NUMEROS DE PARTE Y VARIANTES")
    print(f"Empresa ID: {CO_ENTERPRISE_ID}")
    print("==================================================")
    
    async with AsyncSessionLocal() as session:
        for prod in PRODUCT_CATALOG:
            print(f"\nProducto: {prod['name']} (SKU: {prod['sku']})")
            
            for var in prod['variants']:
                variant_id = uuid.uuid4()
                now = datetime.now(timezone.utc)
                
                # Insert / Upsert Variant
                # Note: We use raw SQL to ensure all mandatory MultiTenantBase fields are set correctly
                await session.execute(text("""
                    INSERT INTO inventory_item_variants (
                        id, product_id, internal_sku, brand, mfg_part_number, 
                        unit_price, weight, is_preferred, is_active, version_id,
                        company_id, tenant_id, created_at
                    )
                    VALUES (
                        :id, :prod_id, :sku, :brand, :mpn, 
                        :price, :weight, FALSE, TRUE, 1,
                        :co_id, :co_id, :now
                    )
                    ON CONFLICT (company_id, internal_sku, mfg_part_number) DO NOTHING;
                """), {
                    "id": variant_id,
                    "prod_id": prod['id'],
                    "sku": prod['sku'],
                    "brand": var['brand'],
                    "mpn": var['mpn'],
                    "price": Decimal(str(var['price'])),
                    "weight": Decimal(str(var['weight'])),
                    "co_id": CO_ENTERPRISE_ID,
                    "now": now
                })
                print(f"   - Variante: {var['brand']} | MPN: {var['mpn']} [OK]")
        
        await session.commit()
    print("\nSeed finalizado exitosamente.")

if __name__ == "__main__":
    asyncio.run(seed_variants())
