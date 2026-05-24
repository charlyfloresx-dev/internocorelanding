import asyncio
import uuid
import logging
import os
import sys

# Ajuste de path
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(BACKEND_ROOT)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from master_app.db.db import async_session
from common.models.enumeration import Enumeration
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seed_enums")

SYSTEM_USER_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")

async def seed_enums():
    async with async_session() as session:
        logger.info("🌱 Iniciando Seeding de Enumeraciones Globales")
        
        enums_to_seed = [
            # TICKET_STATUS
            {"type": "TICKET_STATUS", "key": "OPEN", "label": "Abierto", "t_key": "enums.ticket_status.open", "sort": 1},
            {"type": "TICKET_STATUS", "key": "IN_PROGRESS", "label": "En Progreso", "t_key": "enums.ticket_status.in_progress", "sort": 2},
            {"type": "TICKET_STATUS", "key": "RESOLVED", "label": "Resuelto", "t_key": "enums.ticket_status.resolved", "sort": 3},
            {"type": "TICKET_STATUS", "key": "CLOSED", "label": "Cerrado", "t_key": "enums.ticket_status.closed", "sort": 4},
            
            # TICKET_PRIORITY
            {"type": "TICKET_PRIORITY", "key": "LOW", "label": "Baja", "t_key": "enums.ticket_priority.low", "sort": 1},
            {"type": "TICKET_PRIORITY", "key": "MEDIUM", "label": "Media", "t_key": "enums.ticket_priority.medium", "sort": 2},
            {"type": "TICKET_PRIORITY", "key": "HIGH", "label": "Alta", "t_key": "enums.ticket_priority.high", "sort": 3},
            {"type": "TICKET_PRIORITY", "key": "CRITICAL", "label": "Crítica", "t_key": "enums.ticket_priority.critical", "sort": 4},

            # ASSET_STATUS (CMMS)
            {"type": "ASSET_STATUS", "key": "OPERATIONAL", "label": "Operativo", "t_key": "enums.asset_status.operational", "sort": 1},
            {"type": "ASSET_STATUS", "key": "UNDER_MAINTENANCE", "label": "En Mantenimiento", "t_key": "enums.asset_status.maintenance", "sort": 2},
            {"type": "ASSET_STATUS", "key": "OUT_OF_SERVICE", "label": "Fuera de Servicio", "t_key": "enums.asset_status.out_of_service", "sort": 3},

            # WORK_ORDER_STATUS (CMMS)
            {"type": "WORK_ORDER_STATUS", "key": "DRAFT", "label": "Borrador", "t_key": "enums.wo_status.draft", "sort": 1},
            {"type": "WORK_ORDER_STATUS", "key": "SCHEDULED", "label": "Programada", "t_key": "enums.wo_status.scheduled", "sort": 2},
            {"type": "WORK_ORDER_STATUS", "key": "IN_PROGRESS", "label": "En Ejecución", "t_key": "enums.wo_status.in_progress", "sort": 3},
            {"type": "WORK_ORDER_STATUS", "key": "COMPLETED", "label": "Completada", "t_key": "enums.wo_status.completed", "sort": 4},

            # PAYMENT_METHOD (global defaults — companies can extend with company_id)
            {"type": "PAYMENT_METHOD", "key": "CASH", "label": "Efectivo", "t_key": "enums.payment_method.cash", "sort": 1},
            {"type": "PAYMENT_METHOD", "key": "CARD", "label": "Tarjeta", "t_key": "enums.payment_method.card", "sort": 2},
            {"type": "PAYMENT_METHOD", "key": "TRANSFER", "label": "Transferencia Bancaria", "t_key": "enums.payment_method.transfer", "sort": 3},
            {"type": "PAYMENT_METHOD", "key": "STRIPE", "label": "Stripe / Pago Online", "t_key": "enums.payment_method.stripe", "sort": 4},
            {"type": "PAYMENT_METHOD", "key": "CREDIT", "label": "Crédito / Cuenta Corriente", "t_key": "enums.payment_method.credit", "sort": 5},
        ]

        for e in enums_to_seed:
            stmt = select(Enumeration).where(
                Enumeration.type == e["type"],
                Enumeration.key == e["key"],
                Enumeration.company_id == None
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            
            if not existing:
                session.add(Enumeration(
                    id=uuid.uuid4(),
                    type=e["type"],
                    key=e["key"],
                    label=e["label"],
                    translation_key=e["t_key"],
                    sort_order=e["sort"],
                    company_id=None,
                    tenant_id=None,
                    is_active=True,
                    version_id=1,
                    created_by=SYSTEM_USER_ID
                ))
                logger.info(f"  ➕ Enum: {e['type']}.{e['key']}")
        
        await session.commit()
        logger.info("✅ Seeding de Enumeraciones completado.")

if __name__ == "__main__":
    asyncio.run(seed_enums())
