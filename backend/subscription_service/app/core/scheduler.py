import asyncio
import logging
from app.infrastructure.storage_audit import StorageAuditService
from app.services.grace_period_service import GracePeriodService
from app.infrastructure.database import AsyncSessionLocal

logger = logging.getLogger("subscription.scheduler")

async def storage_audit_job():
    """
    Tarea periódica para la auditoría de almacenamiento.
    """
    while True:
        try:
            logger.info("Ejecutando tarea programada: Auditoría de Almacenamiento (24h)")
            async with AsyncSessionLocal() as db:
                await StorageAuditService.sync_all_tenants(db)
        except Exception as e:
            logger.error(f"Error en scheduler (storage_audit_job): {e}")
        
        # Esperar 24 horas (86400 segundos)
        await asyncio.sleep(86400)

async def grace_period_job():
    """
    Tarea periódica para evaluar transiciones de Grace Period (24h).
    """
    while True:
        try:
            logger.info("Ejecutando tarea programada: Auditoría de Grace Period (24h)")
            async with AsyncSessionLocal() as db:
                await GracePeriodService.process_grace_periods(db)
        except Exception as e:
            logger.error(f"Error en scheduler (grace_period_job): {e}")
        
        await asyncio.sleep(86400)

def start_scheduler():
    """
    Inicia el loop de tareas en segundo plano.
    """
    loop = asyncio.get_event_loop()
    loop.create_task(storage_audit_job())
    loop.create_task(grace_period_job())
