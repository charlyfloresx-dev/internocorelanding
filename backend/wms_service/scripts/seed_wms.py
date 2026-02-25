import asyncio
import argparse
import uuid
import logging
from sqlalchemy.future import select
from app.core.database import engine, AsyncSessionLocal as SessionLocal 
from app.models import MultiTenantBase
from app.models.warehouse import Warehouse, Zone
from app.models.concept import Concept, ConceptType
from app.models.document_series import DocumentSeries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_wms(company_id: uuid.UUID):
    async with engine.begin() as conn:
        logger.info("Sincronizando esquema de base de datos para WMS...")
        await conn.run_sync(MultiTenantBase.metadata.create_all)

    async with SessionLocal() as db:
        # --- 1. CONCEPTOS (Master Data) ---
        concepts_to_create = [
            {
                "code": "RECEPCION_COMPRA", "name": "Recepción por Compra",
                "concept_type": ConceptType.ENTRY, "affect_stock": True
            },
            {
                "code": "SALIDA_VENTA", "name": "Salida por Venta",
                "concept_type": ConceptType.OUTPUT, "affect_stock": True
            }
        ]

        for c_data in concepts_to_create:
            exists = await db.execute(select(Concept).filter(Concept.code == c_data["code"], Concept.company_id == company_id))
            if not exists.scalars().first():
                logger.info(f"🌱 Creando concepto '{c_data['code']}'...")
                # Asumimos company_id global para el seed o específico
                db.add(Concept(**c_data, company_id=company_id))
            else:
                logger.info(f"ℹ️ Concepto '{c_data['code']}' ya existe.")

        # --- 2. SERIES DE DOCUMENTOS ---
        series_prefix = "MOV-"
        series_exists = await db.execute(select(DocumentSeries).filter(
            DocumentSeries.company_id == company_id,
            DocumentSeries.prefix == series_prefix
        ))
        if not series_exists.scalars().first():
            logger.info(f"🌱 Creando serie '{series_prefix}'...")
            # Asociamos a un concepto genérico o específico según regla de negocio
            db.add(DocumentSeries(prefix=series_prefix, concept_code="RECEPCION_COMPRA", company_id=company_id))
        else:
            logger.info(f"ℹ️ Serie '{series_prefix}' ya existe.")

        # --- 3. ALMACENES ---
        warehouses_to_create = [
            {"name": "Almacén Tijuana", "code": "WH-TIJ"},
            {"name": "Almacén San Diego", "code": "WH-SAN"}
        ]

        for wh_data in warehouses_to_create:
            # Verificar si el almacén ya existe
            result = await db.execute(
                select(Warehouse).filter(
                    Warehouse.company_id == company_id,
                    Warehouse.code == wh_data["code"]
                )
            )
            
            if result.scalars().first():
                logger.info(f"ℹ️ El {wh_data['name']} ya existe. Saltando.")
                continue

            logger.info(f"🌱 Creando {wh_data['name']}...")
            
            # Crear Almacén
            warehouse = Warehouse(
                name=wh_data["name"],
                code=wh_data["code"],
                company_id=company_id
            )
            db.add(warehouse)
            await db.flush() # Para obtener el ID del almacén

            # 2. Crear Zonas para cada almacén
            zones = [
                Zone(name=f"Recepción {wh_data['code']}", code=f"Z-RECV-{wh_data['code']}", 
                     warehouse_id=warehouse.id, company_id=company_id),
                Zone(name=f"Almacenamiento {wh_data['code']}", code=f"Z-STR-{wh_data['code']}", 
                     warehouse_id=warehouse.id, company_id=company_id)
            ]
            db.add_all(zones)

        await db.commit()
        logger.info("✅ Seed de WMS (Conceptos, Series y Almacenes) finalizado exitosamente.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--company-id", required=True)
    args = parser.parse_args()
    asyncio.run(seed_wms(company_id=uuid.UUID(args.company_id)))