import logging
import uuid
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from common.models.file_metadata import FileMetadata
from subscription_app.models.subscription import Subscription

logger = logging.getLogger("subscription.storage_audit")

class StorageAuditService:
    """
    Sincronizador de Auditor\u00eda de Almacenamiento.
    Calcula el uso real basado en metadatos y actualiza el estado de la suscripci\u00f3n.
    """

    @staticmethod
    async def sync_all_tenants(db: AsyncSession):
        """
        Itera por todas las compa\u00f1\u00edas que tienen suscripciones activas
        y recalcula su uso de almacenamiento.
        """
        logger.info("\ud83d\udd04 Iniciando auditor\u00eda global de almacenamiento...")
        
        # 1. Obtener todas las compa\u00f1\u00edas con suscripci\u00f3n
        stmt_tenants = select(Subscription.company_id).distinct()
        result_tenants = await db.execute(stmt_tenants)
        company_ids = result_tenants.scalars().all()

        for company_id in company_ids:
            try:
                await StorageAuditService.sync_tenant_usage(db, company_id)
            except Exception as e:
                logger.error(f"\u274c Error auditando almacenamiento para company {company_id}: {e}")
        
        await db.commit()
        logger.info("\u2705 Auditor\u00eda de almacenamiento completada.")

    @staticmethod
    async def sync_tenant_usage(db: AsyncSession, company_id: uuid.UUID):
        """
        Calcula el tama\u00f1o total de archivos para una compa\u00f1\u00eda
        utilizando una consulta agregada (SUM) sobre la tabla de metadatos.
        """
        # Consulta agregada optimizada
        stmt_sum = (
            select(func.sum(FileMetadata.size_bytes))
            .where(FileMetadata.company_id == company_id)
        )
        result_sum = await db.execute(stmt_sum)
        total_usage = result_sum.scalar() or 0

        # Actualizar la suscripci\u00f3n
        stmt_update = (
            update(Subscription)
            .where(Subscription.company_id == company_id)
            .values(current_storage_usage=total_usage)
        )
        await db.execute(stmt_update)
        
        logger.info(f"\ud83d\udcca Company {company_id}: Uso actualizado a {total_usage} bytes.")
        return total_usage
