import logging

logger = logging.getLogger(__name__)

async def apply_migrations(engine):
    logger.info("[DEPRECATED] migrate_schema.py is deprecated in favor of Alembic.")
    logger.info("[DEPRECATED] Everything is now handled by 000_inventory_baseline.py")
    return

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("This script is deprecated. Run 'alembic upgrade head' instead.")
