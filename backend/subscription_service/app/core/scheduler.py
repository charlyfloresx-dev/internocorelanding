import asyncio
import logging
from app.infrastructure.storage_audit import StorageAuditService
from app.infrastructure.database import AsyncSessionLocal

logger = logging.getLogger("subscription.scheduler")

async def storage_audit_job():
    """
    Tarea peri\u00f3dica para la auditor\u00eda de almacenamiento.
    """
    while True:
        try:
            logger.info("\ud83d\udcc5 Ejecutando tarea programada: Auditor\u00eda de Almacenamiento (24h)")
            async with AsyncSessionLocal() as db:
                await StorageAuditService.sync_all_tenants(db)
        except Exception as e:
            logger.error(f"\u274c Error en scheduler (storage_audit_job): {e}")
        
        # Esperar 24 horas (86400 segundos)
        await asyncio.sleep(86400)

def start_scheduler():
    """
    Inicia el loop de tareas en segundo plano.
    """
    loop = asyncio.get_event_loop()
    loop.create_task(storage_audit_job())
