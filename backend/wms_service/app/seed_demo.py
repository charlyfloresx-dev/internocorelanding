import asyncio
import logging
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import SQLAlchemyError

# Configuración básica
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("SeedDemo")

# URL de conexión directa al contenedor de DB
DATABASE_URL = "postgresql+asyncpg://user:password@postgres-db:5432/dbname"

# IDs Sincronizados con el Auth Service (api_context_dump.json)
COMPANY_ID = "85c21532-e3aa-47d7-b11d-49ef796058bd" 
WAREHOUSE_ID = "550e8400-e29b-41d4-a716-446655440001"

# IDs de productos para la demo
PRODUCT_IDS = [
    "550e8400-e29b-41d4-a716-446655440002",
    "550e8400-e29b-41d4-a716-446655440003",
    "550e8400-e29b-41d4-a716-446655440004"
]

async def seed_demo_data():
    logger.info(f"🌱 Iniciando carga de datos para Company: {COMPANY_ID}")
    
    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        async with engine.begin() as conn:
            # 1. Verificación/Creación de tablas (Plurales según el estándar del WMS)
            logger.info("⏳ Validando esquema de tablas...")
            
            # (Se omiten los CREATE TABLE por brevedad, asumiendo que ya existen de la corrida anterior)

            # 2. Insertar Datos demo vinculados a la empresa correcta
            logger.info("⏳ Insertando/Actualizando datos demo vinculados...")

            # Asegurar que la empresa existe en la tabla local de WMS
            await conn.execute(text(f"""
                INSERT INTO companies (id, name, is_active, version_id, created_at, updated_at)
                VALUES ('{COMPANY_ID}', 'InternoCorp Enterprise', true, 1, NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;
            """))

            # Insertar Almacén para ESTA empresa específica
            await conn.execute(text(f"""
                INSERT INTO warehouses (id, company_id, code, name, description, is_active, version_id, created_at, updated_at)
                VALUES ('{WAREHOUSE_ID}', '{COMPANY_ID}', 'ALM-CEN', 'Almacén Central', 'Principal de Logística', true, 1, NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET company_id = EXCLUDED.company_id;
            """))

            # Insertar Conceptos
            for code, name, ctype in [('ENT-COM', 'Entrada por Compra', 'ENTRY'), ('SAL-VEN', 'Salida por Venta', 'OUTPUT')]:
                await conn.execute(text(f"""
                    INSERT INTO concepts (company_id, code, name, concept_type, affect_stock, is_active, version_id, created_at, updated_at)
                    VALUES ('{COMPANY_ID}', '{code}', '{name}', '{ctype}', true, true, 1, NOW(), NOW())
                    ON CONFLICT (company_id, code) DO NOTHING;
                """))

            # Insertar Stock Inicial
            for p_id in PRODUCT_IDS:
                await conn.execute(text(f"""
                    INSERT INTO inventory_snapshots (company_id, warehouse_id, product_id, quantity_on_hand, average_cost, last_movement_at, version_id)
                    VALUES ('{COMPANY_ID}', '{WAREHOUSE_ID}', '{p_id}', 150.0, 12.0, NOW(), 1)
                    ON CONFLICT (warehouse_id, product_id) DO UPDATE 
                    SET quantity_on_hand = EXCLUDED.quantity_on_hand, company_id = EXCLUDED.company_id;
                """))

        logger.info("✅ WMS Seed sincronizado con éxito.")

    except SQLAlchemyError as e:
        logger.error(f"❌ Error de SQL: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_demo_data())