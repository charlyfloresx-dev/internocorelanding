# pyre-ignore-all-errors[21]
import asyncio
import uuid
import logging
import os
import sys
import traceback
from decimal import Decimal
from datetime import datetime, timezone
import sqlalchemy.exc

# Ajustar path para encontrar 'app'
sys.path.append(os.getcwd())

from app.db.session import AsyncSessionLocal
from app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from app.domain.entities.transfer_entities import InitiateTransferCommand, CompleteTransferCommand
from app.models.item_variant import ItemVariant
from app.models.movement import Movement
from app.models.inter_company_transfer import InterCompanyTransfer
from sqlalchemy import select
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.infrastructure.clients.master_data import MasterDataClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("price_freeze_test")

async def verify_sealed_price_test():
    logger.info("--- PHASE 36: THE PRICE FREEZE TEST ---")
    
    # ── Contexto de Prueba ──────────────────
    company_a = uuid.UUID("11111111-1111-1111-1111-111111111111")
    company_b = uuid.UUID("22222222-2222-2222-2222-222222222222")
    user_id_a = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38") # SYSTEM_A
    user_id_b = uuid.UUID("77777777-7777-7777-7777-777777777777") # OPERATOR_B
    
    sku = "MAT-001"
    wh_code = "WH-MAIN"
    wh_a = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{company_a}.{wh_code}")
    wh_b = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{company_b}.{wh_code}")
    product_a = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{company_a}.{sku}")
    uom_id = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")

    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyInventoryRepository(session)
        handler = TransferCommandHandler(session, repo)
        
        logger.info(f"[STEP 1] Validando IDs determinísticos...")
        
        try:
            # 2. DESPACHO (ICT-OUT): Precio pactado $12.00
            logger.info("[STEP 2] Despacho: Empresa A envía 50 unidades a $12.00 (Precio Sellado)")
            cmd_init = InitiateTransferCommand(
                origin_company_id=company_a,
                initiated_by=user_id_a,
                destination_company_id=company_b,
                destination_warehouse_id=wh_b,
                origin_warehouse_id=wh_a,
                product_id=product_a,
                uom_id=uom_id,
                quantity=Decimal("50.0"),
                transfer_price=Decimal("12.00"),
                currency="USD",
                external_reference=f"AUDIT-{str(uuid.uuid4()).replace('-', '')[:8].upper()}"
            )
            
            transfer_doc = await handler.initiate_transfer(cmd_init)
            await session.commit() 
            
            transfer_id = transfer_doc.id
            logger.info(f"Transferencia SHIPPED | Folio: {transfer_doc.folio}")
            
            # 3. RECEPCIÓN (ICT-IN): Empresa B confirma
            logger.info("[STEP 3] Recepción: Empresa B recibe las 50 unidades")
            cmd_complete = CompleteTransferCommand(
                receiver_company_id=company_b,
                received_by=user_id_b,
                transfer_id=transfer_id,
                received_quantity=Decimal("50.0")
            )
            
            await handler.complete_transfer(cmd_complete)
            await session.commit()
            logger.info("Transferencia DELIVERED")

            # 4. VALIDACIÓN FINAL
            logger.info("[STEP 4] Auditoría Forense de Precio...")
            
            async with AsyncSessionLocal() as verify_session:
                stmt = select(Movement).filter_by(
                    document_id=transfer_id,
                    company_id=company_b,
                    movement_type="TRANSFER_IN"
                )
                result = await verify_session.execute(stmt)
                mov_in = result.scalar_one_or_none()
                
                if not mov_in:
                    logger.error("❌ FAILURE: No se encontró el movimiento de entrada en Empresa B")
                    sys.exit(1)

                final_price = mov_in.price.amount
                logger.info(f"RESULTADO: Costo de Adquisición en B = ${final_price}")
                
                if final_price == Decimal("12.00"):
                    logger.info("✅ VERIFIED: El oráculo financiero respetó la inmutabilidad (Sealed Price).")
                else:
                    logger.error(f"❌ TAMPERED: El precio mutó! Esperado 12.00, obtenido {final_price}")
                    sys.exit(1)
        
        except sqlalchemy.exc.IntegrityError as e:
            logger.error(f"DATABASE_INTEGRITY_VIOLATION: {str(e.orig)}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"RUNTIME_ERROR: {str(e)}")
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify_sealed_price_test())
