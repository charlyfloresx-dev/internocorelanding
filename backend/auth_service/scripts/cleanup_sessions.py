import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add parent directory to sys.path to allow imports from auth_app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_app.core.database import AsyncSessionLocal
from auth_app.models.refresh_token import RefreshToken
from sqlalchemy import delete

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("cleanup_sessions.log")
    ]
)
logger = logging.getLogger("SessionCleanup")

async def cleanup_expired_sessions():
    """
    Garbage Collector: Prunes expired or revoked refresh tokens from the DB.
    """
    logger.info("Starting session cleanup (Garbage Collector)...")
    
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            
            stmt = delete(RefreshToken).where(RefreshToken.expires_at < now)
            result = await db.execute(stmt)
            await db.commit()
            
            # Note: with async engine/driver, rowcount might not be directly available 
            # after execute. In SQLAlchemy 2.0 result.rowcount should work.
            purged_count = result.rowcount
            
            if purged_count > 0:
                logger.info(f"✅ Successfully purged {purged_count} expired refresh tokens.")
            else:
                logger.info("✨ No expired sessions found. Database is clean.")

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")
            await db.rollback()
        finally:
            logger.info("Cleanup session closed.")

if __name__ == "__main__":
    asyncio.run(cleanup_expired_sessions())
