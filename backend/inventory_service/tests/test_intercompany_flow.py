import asyncio
import uuid
import logging
import os
import sys
from decimal import Decimal
from datetime import datetime, timezone

# Path Normalization
service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from inventory_app.db.session import AsyncSessionLocal
from inventory_app.domain.entities.transfer_entities import InitiateTransferCommand, CompleteTransferCommand
from inventory_app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository as InventoryRepository

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("test_ict")

# Usuarios y Empresas Demo
USER_A = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.user.admin-a") # Admin Logistics
USER_B = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.user.admin-b") # Admin Enterprise
COMPANY_A = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242") # Logistics
COMPANY_B = uuid.UUID("d6b0bfcd-1eab-4d83-94c6-2eb969b92289") # Enterprise

# Almacenes
WH_MAIN_A = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.WH-MAIN")
WH_MAIN_B = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.ENTERPRISE-MAIN")

# Producto y UOM
PRODUCT_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.item.MAT-001")
UOM_PZ = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")


async def run_test():
    logger.info("==================================================")
    logger.info("🚀 INICIANDO TEST: INTER-COMPANY TRANSFER FLOW")
    logger.info("==================================================")

    async with AsyncSessionLocal() as session:
        # Asegurar que el almacén de destino exista para Empresa B
        from inventory_app.models.warehouse import Warehouse
        from sqlalchemy import select
        stmt = select(Warehouse).filter_by(id=WH_MAIN_B)
        res = await session.execute(stmt)
        wh = res.scalar_one_or_none()
        if not wh:
            logger.info("🔧 Creando almacén físico de destino para Empresa B...")
            wh = Warehouse(
                id=WH_MAIN_B,
                company_id=COMPANY_B,
                code="ENT-MAIN",
                name="Enterprise Main Warehouse",
                location="Texas, USA"
            )
            session.add(wh)
            await session.commit()
            
        repo = InventoryRepository(session)
        handler = TransferCommandHandler(session=session, repo=repo)

        # 1. EMPRESA A (Logistics) -> INICIA TRANFERENCIA A EMPRESA B (Enterprise)
        logger.info("\n--- PASO 1: EMPRESA A DESPACHA ---")
        init_cmd = InitiateTransferCommand(
            origin_company_id=COMPANY_A,
            initiated_by=USER_A,
            destination_company_id=COMPANY_B,
            destination_warehouse_id=WH_MAIN_B,
            origin_warehouse_id=WH_MAIN_A,
            product_id=PRODUCT_ID,
            uom_id=UOM_PZ,
            quantity=Decimal("50.0"),
            weight=Decimal("10.0"),
            origin_sku="MAT-001",
            destination_sku="ENT-MAT-001",
            destination_product_id=PRODUCT_ID,
            transfer_price=Decimal("150.00"),  # PRECIO PACTADO
            currency="MXN",
            notes="Transferencia urgente para ensamble",
            external_reference="PO-B-998877"
        )

        try:
            transfer_doc = await handler.initiate_transfer(init_cmd)
            await session.commit()
            logger.info(f"✅ Transferencia Iniciada: {transfer_doc.folio}")
            logger.info(f"   Status: {transfer_doc.status.value}")
            logger.info(f"   Precio Sellado (Venta A -> Compra B): ${transfer_doc.unit_price_at_dispatch}")
            logger.info(f"   Costo Real (WAC A): ${transfer_doc.wac_at_dispatch}")
            logger.info(f"   Ingreso A: ${transfer_doc.transfer_revenue_a} | Margen A: ${transfer_doc.transfer_margin_a}")
            logger.info(f"   Advertencia de Precio: {getattr(transfer_doc, 'transfer_price_warning', 'Ninguna')}")
        except Exception as e:
            logger.error(f"❌ Error al iniciar: {e}")
            await session.rollback()
            return

        transfer_id = transfer_doc.id

    # Nuevo Scope de Transacción para la Recepción
    async with AsyncSessionLocal() as session:
        repo = InventoryRepository(session)
        handler = TransferCommandHandler(session=session, repo=repo)

        # 2. EMPRESA B (Enterprise) -> RECIBE LA TRANSFERENCIA
        logger.info("\n--- PASO 2: EMPRESA B RECIBE ---")
        receive_cmd = CompleteTransferCommand(
            transfer_id=transfer_id,
            receiver_company_id=COMPANY_B,
            received_by=USER_B,
            received_quantity=Decimal("50.0"), # Recepción completa
            notes="Material recibido en perfectas condiciones"
        )

        try:
            completed_doc = await handler.complete_transfer(receive_cmd)
            await session.commit()
            logger.info(f"✅ Transferencia Completada: {completed_doc.folio}")
            logger.info(f"   Status Final: {completed_doc.status.value}")
            logger.info(f"   Cantidad Recibida: {completed_doc.received_quantity}")
            logger.info(f"   Costo de Adquisición para B (Recalculará su WAC): ${completed_doc.acquisition_cost_b}")
            
            # Verificar consistencia matemática del contrato
            expected_cost = Decimal("50.0") * Decimal("150.00")
            if completed_doc.acquisition_cost_b == expected_cost:
                logger.info("   [AUDIT] Integridad Matemática: APROBADA 🟢")
            else:
                logger.error(f"   [AUDIT] Falla de Integridad: {completed_doc.acquisition_cost_b} != {expected_cost} 🔴")

        except Exception as e:
            logger.error(f"❌ Error al recibir: {e}")
            await session.rollback()
            return

    logger.info("\n==================================================")
    logger.info("🏆 TEST FINALIZADO CON ÉXITO")
    logger.info("==================================================")

if __name__ == "__main__":
    asyncio.run(run_test())
