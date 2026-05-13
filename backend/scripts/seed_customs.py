import asyncio
import uuid
import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("customs-seed")

# IDs de Continuidad (Sincronizados con unified_industrial_seed.py)
ENTERPRISE_ID   = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
LOGISTICS_US_ID = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")

# Productos del Catálogo Industrial
PRODUCTS = [
    {"id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000001"), "sku": "ECM-600"},
    {"id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000002"), "sku": "TRB-700"},
    {"id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000003"), "sku": "BRK-800"},
    {"id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000004"), "sku": "FLI-900"},
    {"id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000005"), "sku": "SUS-100"},
]

async def seed_customs_balances():
    import os
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@postgres-db:5432/dbname")
    engine = create_async_engine(db_url, pool_pre_ping=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    now = datetime.now(timezone.utc)
    
    async with AsyncSessionLocal() as session:
        log.info("Iniciando inyección de cumplimiento aduanero (Anexo 24)...")
        
        # Obtener un UOM ID genérico (Piezas)
        res_uom = await session.execute(text("SELECT id FROM uoms WHERE code = 'PZ' LIMIT 1"))
        uom_id = res_uom.scalar()
        if not uom_id:
             uom_id = uuid.uuid4() # Fallback

        for cid, name in [
            (ENTERPRISE_ID, "Enterprise"),
            (LOGISTICS_MX_ID, "Logistics MX"),
            (LOGISTICS_US_ID, "Logistics US")
        ]:
            log.info(f"Procesando {name} ({cid})...")
            
            # 1. Obtener un almacén de la empresa
            res = await session.execute(text("SELECT id FROM inventory_warehouses WHERE company_id = :cid LIMIT 1"), {"cid": cid})
            wh_id = res.scalar()
            if not wh_id:
                log.warning(f"  SKIP: No se encontró almacén para {name}")
                continue

            # 2. Crear Pedimentos
            for i in range(1, 4):
                ped_id = uuid.uuid4()
                ped_number = f"24{i:02d}39547000{i}1"
                await session.execute(text("""
                    INSERT INTO customs_pedimentos (
                        id, pedimento_number, customs_key, operation_type, customs_date,
                        is_temporary, exchange_rate_dof,
                        company_id, tenant_id, version_id, is_active, created_at
                    ) VALUES (
                        :id, :num, 'V1', 'IMPORT', :cdate, 
                        TRUE, 17.50, 
                        :cid, :cid, 1, TRUE, NOW()
                    ) ON CONFLICT (pedimento_number) DO NOTHING;
                """), {
                    "id": ped_id, "num": ped_number, 
                    "cdate": now - timedelta(days=30), 
                    "cid": cid
                })
                
                # Obtener el ID si ya existe o el nuevo
                res_p = await session.execute(text("SELECT id FROM customs_pedimentos WHERE pedimento_number = :num"), {"num": ped_number})
                actual_ped_id = res_p.scalar()

                # 3. Crear movimientos de inventario con saldo para cada producto
                for prod in PRODUCTS:
                    await session.execute(text("""
                        INSERT INTO inventory_movements (
                            id, product_id, warehouse_id, quantity, available_quantity,
                            movement_type, customs_pedimento_id, expiry_date, 
                            uom_id, weight, unit_price, currency,
                            document_type, document_id,
                            company_id, tenant_id,
                            version_id, is_active, created_at
                        ) VALUES (
                            :id, :pid, :wid, :qty, :qty, 'IN', :ped, :exp,
                            :uom, :weight, 10.0, 'USD',
                            'INVENTORY_DOC', :did,
                            :cid, :cid, 1, TRUE, NOW()
                        ) ON CONFLICT DO NOTHING;
                    """), {
                        "id": uuid.uuid4(), "pid": prod['id'], "wid": wh_id,
                        "qty": Decimal("100.00"), "ped": actual_ped_id, 
                        "exp": now + timedelta(days=365),
                        "uom": uom_id, "weight": Decimal("1.0"),
                        "did": uuid.uuid4(),
                        "cid": cid
                    })
            
            log.info(f"  OK: Inyectados pedimentos y movimientos para {name}")
        
        await session.commit()
    
    await engine.dispose()
    log.info("Inyección finalizada con éxito.")

if __name__ == "__main__":
    asyncio.run(seed_customs_balances())
