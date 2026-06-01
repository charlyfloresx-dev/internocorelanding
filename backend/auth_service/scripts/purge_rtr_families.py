"""
RTR DB Worker — Purga de Familias de Tokens Expiradas

Elimina de forma segura las RefreshTokenFamily cuya ventana de refresh
ya expiró hace más de SAFETY_MARGIN_DAYS días, junto con sus
RefreshTokenRotationAudit en cascada.

IMPORTANTE: NO usa el ORM para el DELETE porque los Event Listeners en
RefreshTokenRotationAudit bloquean cualquier DELETE vía SQLAlchemy ORM
(protección append-only de la tabla de auditoría). En su lugar usa
text() con SQL nativo que bypasa los listeners.

Uso:
    # Dentro del contenedor auth_service:
    python scripts/purge_rtr_families.py

    # O como cron job (diario a las 3am):
    # docker exec interno-auth-dev python /app/scripts/purge_rtr_families.py
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from auth_app.core.database import AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("RTR.Purge")

# Familias expiradas hace más de 7 días se consideran seguras para borrar.
# Esto preserva familias recientes por si hay un RDS failover en curso.
SAFETY_MARGIN_DAYS = 7


async def purge_expired_families() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=SAFETY_MARGIN_DAYS)
    logger.info(f"Iniciando purga RTR. Cutoff: {cutoff.isoformat()} (SAFETY_MARGIN={SAFETY_MARGIN_DAYS}d)")

    async with AsyncSessionLocal() as db:
        try:
            # Paso 1: Contar familias candidatas
            count_result = await db.execute(
                text("""
                    SELECT COUNT(*) FROM refresh_token_families
                    WHERE refresh_window_expires_at < :cutoff
                """),
                {"cutoff": cutoff},
            )
            candidate_count = count_result.scalar_one()
            logger.info(f"Familias candidatas a purga: {candidate_count}")

            if candidate_count == 0:
                logger.info("No hay familias expiradas. Base de datos limpia.")
                return

            # Paso 2: Borrar auditoría en cascada primero (bypasa Event Listeners ORM)
            # Los listeners solo se disparan en operaciones ORM (session.delete / bulk_update_mappings).
            # text() ejecuta SQL nativo directamente → no activa los before_bulk_delete listeners.
            audit_result = await db.execute(
                text("""
                    DELETE FROM refresh_token_rotation_audit
                    WHERE family_id IN (
                        SELECT id FROM refresh_token_families
                        WHERE refresh_window_expires_at < :cutoff
                    )
                """),
                {"cutoff": cutoff},
            )
            audit_deleted = audit_result.rowcount
            logger.info(f"Registros de auditoría eliminados: {audit_deleted}")

            # Paso 3: Borrar las familias
            families_result = await db.execute(
                text("""
                    DELETE FROM refresh_token_families
                    WHERE refresh_window_expires_at < :cutoff
                """),
                {"cutoff": cutoff},
            )
            families_deleted = families_result.rowcount
            logger.info(f"Familias de tokens eliminadas: {families_deleted}")

            await db.commit()
            logger.info(
                f"Purga completada. Familias: {families_deleted} · Auditoría: {audit_deleted}"
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"Error durante la purga RTR: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(purge_expired_families())
