import asyncio
import uuid
import logging
import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal

# 1. Path Normalization
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SERVICE_APP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
if SERVICE_APP not in sys.path:
    sys.path.insert(0, SERVICE_APP)

os.chdir(SERVICE_APP) 
from app.db.session import AsyncSessionLocal
from app.models.inventory import InventoryLevel, InventoryTransaction, TransactionType
from app.models.concept import MovementConcept, ConceptType
from app.models.item_variant import ItemVariant
from app.models.movement import Movement
from sqlalchemy.future import select
from sqlalchemy import delete

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seed_inventory")

# --- IDs ALINEADOS CON AUTH SEED (LOGISTIC DEMO) ---
CO_LOGISTICS_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
SYSTEM_USER_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38") # Admin "Charly"
UOM_PZ_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")

# IDs de Almacenes
WH_TIJ_ID = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.wh.WH-TIJ.{CO_LOGISTICS_ID}")
WH_SDY_ID = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.wh.WH-SDY.{CO_LOGISTICS_ID}")

async def seed_inventory():
    async with AsyncSessionLocal() as session:
        try:
            logger.info(f"🌱 [INVENTORY] Iniciando seed avanzado para company: {CO_LOGISTICS_ID}")

            # 0. Garantizar tablas (Fail-safe)
            async with session.bind.begin() as conn:
                from common.models import Base
                await conn.run_sync(Base.metadata.create_all)

            # 1. CONCEPTOS DE MOVIMIENTO
            concepts_data = [
                {"name": "Compra Externo", "code": "COMPRA", "type": ConceptType.ENTRY},
                {"name": "Consumo Producción", "code": "PRODUCCION", "type": ConceptType.OUTPUT},
                {"name": "Transferencia Tijuana-SD", "code": "TRANSFERENCIA", "type": ConceptType.OUTPUT},
                {"name": "Recepción Transferencia", "code": "RECEPCION_TRA", "type": ConceptType.ENTRY},
                {"name": "Material Scrap", "code": "SCRAP", "type": ConceptType.OUTPUT},
                {"name": "Ajuste de Inventario", "code": "AJUSTE", "type": ConceptType.ENTRY}, # Puede ser ambos, simplificado
                {"name": "Devolución Cliente", "code": "DEVOLUCION_CLIENTE", "type": ConceptType.ENTRY},
            ]
            
            concept_ids = {}
            for c in concepts_data:
                stmt = select(MovementConcept).filter_by(code=c["code"], company_id=CO_LOGISTICS_ID)
                res = await session.execute(stmt)
                obj = res.scalars().first()
                if not obj:
                    obj = MovementConcept(
                        id=uuid.uuid4(),
                        name=c["name"],
                        code=c["code"],
                        type=c["type"],
                        company_id=CO_LOGISTICS_ID,
                        created_by=SYSTEM_USER_ID
                    )
                    session.add(obj)
                concept_ids[c["code"]] = obj.id
            await session.flush()

            # 2. CATALOGO Y STOCK (10 MATERIALES)
            skus = [f"MAT-{str(i).zfill(3)}" for i in range(1, 11)]
            item_variant_data = {
                "MAT-001": [
                    {"brand": "Alcoa", "mpn": "AL-6061-T6", "price": 12.50, "weight": 2.7, "vol": 0.001, "pref": True},
                    {"brand": "Hydro", "mpn": "HY-EXT-6061", "price": 11.90, "weight": 2.7, "vol": 0.001, "pref": False}
                ],
                "MAT-005": [
                    {"brand": "3M", "mpn": "G10-PRO-3M", "price": 45.00, "weight": 1.2, "vol": 0.002, "pref": True},
                    {"brand": "Loctite", "mpn": "LOC-EPOXY-G10", "price": 42.50, "weight": 1.2, "vol": 0.002, "pref": False}
                ],
                "MAT-012": [
                    {"brand": "Southwire", "mpn": "SW-14AWG-BK", "price": 0.85, "weight": 0.05, "vol": 0.0001, "pref": True},
                    {"brand": "Encore", "mpn": "ENC-14AWG-CU", "price": 0.80, "weight": 0.05, "vol": 0.0001, "pref": False}
                ],
                "MAT-022": [
                    {"brand": "Fastenal", "mpn": "FAS-M8-SS-100", "price": 0.15, "weight": 0.01, "vol": 0.00001, "pref": True}
                ],
                "MAT-002": [
                    {"brand": "Uline", "mpn": "UL-STR-20IN", "price": 18.00, "weight": 5.0, "vol": 0.05, "pref": True}
                ]
            }

            for sku in skus:
                item_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{sku}")
                
                # STOCK INICIAL
                base_qty_tij = 5000.0
                base_qty_sdy = 2000.0
                
                # ALERTA MAT-001: Forzar stock bajo (Requisito 3)
                if sku == "MAT-001":
                    base_qty_tij = 12.0
                if sku == "MAT-005":
                    base_qty_sdy = 5.0

                for wh_id, qty in [(WH_TIJ_ID, base_qty_tij), (WH_SDY_ID, base_qty_sdy)]:
                    stmt = select(InventoryLevel).filter_by(
                        warehouse_id=wh_id, product_id=item_id, company_id=CO_LOGISTICS_ID
                    )
                    res = await session.execute(stmt)
                    level = res.scalars().first()
                    
                    if not level:
                        level = InventoryLevel(
                            id=uuid.uuid4(),
                            company_id=CO_LOGISTICS_ID,
                            warehouse_id=wh_id,
                            product_id=item_id,
                            uom_id=UOM_PZ_ID,
                            quantity=Decimal(str(qty)),
                            weighted_average_cost=Decimal("10.0"),
                            created_by=SYSTEM_USER_ID
                        )
                        session.add(level)
                    else:
                        level.quantity = Decimal(str(qty))

                # VARIANTES (Requisito 1)
                variants = item_variant_data.get(sku, [])
                for v in variants:
                    stmt = select(ItemVariant).filter_by(
                        internal_sku=sku, brand=v["brand"], company_id=CO_LOGISTICS_ID
                    )
                    res = await session.execute(stmt)
                    if not res.scalars().first():
                        session.add(ItemVariant(
                            id=uuid.uuid4(),
                            company_id=CO_LOGISTICS_ID,
                            product_id=item_id,
                            internal_sku=sku,
                            brand=v["brand"],
                            mfg_part_number=v["mpn"],
                            unit_price=Decimal(str(v["price"])),
                            weight=Decimal(str(v["weight"])),
                            volume=Decimal(str(v["vol"])),
                            is_preferred=v["pref"],
                            created_by=SYSTEM_USER_ID
                        ))

            # 3. MOVIMIENTOS HISTORICOS (20 últimos 24h)
            logger.info("🕒 Generando historial de movimientos (24h)...")
            now = datetime.utcnow()
            for _ in range(20):
                target_sku = random.choice(skus)
                target_item_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{target_sku}")
                wh = random.choice([WH_TIJ_ID, WH_SDY_ID])
                
                # Simular transacciones
                change = random.uniform(50, 200)
                is_entry = random.choice([True, False])
                
                # Seleccionar concepto y tipo
                if is_entry:
                    type_tx = TransactionType.IN
                    concept_code = "COMPRA"
                else:
                    type_tx = TransactionType.OUT
                    concept_code = "PRODUCCION"
                
                tx_date = now - timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
                
                # Registrar transaccion simplificada
                session.add(InventoryTransaction(
                    id=uuid.uuid4(),
                    company_id=CO_LOGISTICS_ID,
                    product_id=target_item_id,
                    warehouse_id=wh,
                    transaction_type=type_tx,
                    quantity_change=Decimal(str(change if is_entry else -change)),
                    previous_balance=Decimal("1000"), # Mock
                    new_balance=Decimal("1000") + Decimal(str(change if is_entry else -change)),
                    comments=f"Movimiento demo {concept_code}",
                    created_at=tx_date,
                    created_by=SYSTEM_USER_ID
                ))
                
                # Registrar Movimiento (Ledger)
                session.add(Movement(
                    id=uuid.uuid4(),
                    company_id=CO_LOGISTICS_ID,
                    warehouse_id=wh,
                    product_id=target_item_id,
                    quantity=Decimal(str(change)),
                    movement_type="IN" if is_entry else "OUT",
                    concept_id=concept_ids[concept_code],
                    document_type="ENT" if is_entry else "SAL",
                    document_id=uuid.uuid4(),
                    created_at=tx_date,
                    created_by=SYSTEM_USER_ID
                ))

            # Simular transferencia en TRANSIT (TRA-2026-0008)
            session.add(Movement(
                id=uuid.uuid4(),
                company_id=CO_LOGISTICS_ID,
                warehouse_id=WH_TIJ_ID,
                product_id=uuid.uuid5(uuid.NAMESPACE_DNS, "interno.item.MAT-002"),
                quantity=Decimal("500"),
                movement_type="OUT",
                concept_id=concept_ids["TRANSFERENCIA"],
                document_type="TRA",
                document_id=uuid.UUID("00000000-0000-0000-0000-202600000008"), # Mock folios
                comments="Transferencia activa a San Diego",
                created_by=SYSTEM_USER_ID
            ))

            await session.commit()
            logger.info("✅ [INVENTORY] Seed avanzado completado exitosamente.")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ [INVENTORY] Error en seed avanzado: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_inventory())
