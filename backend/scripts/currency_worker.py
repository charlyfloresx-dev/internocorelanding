import asyncio
import uuid
import logging
import os
import sys
from datetime import datetime, timezone

# Adjust path to find 'common' and 'app'
# Assuming script is run from /backend
sys.path.append(os.getcwd())
# Also add the service path so we can import 'app' from currency_service
sys.path.append(os.path.join(os.getcwd(), "currency_service"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Import common settings and components
from common.config import settings
from common.models import Company
# Import from the specific service
from app.services.currency_service import CurrencyService
from app.infrastructure.clients.rate_provider import ExternalRateProvider

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("currency_worker")

# DB Connection for the currency service (own DB)
CURRENCY_DB_URL = str(settings.database_url)
engine = create_async_engine(CURRENCY_DB_URL, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Separate engine for reading companies (main DB)
MAIN_DB_URL = str(settings.database_url)
main_engine = create_async_engine(MAIN_DB_URL, pool_pre_ping=True)
main_session = async_sessionmaker(main_engine, expire_on_commit=False)

async def run_worker():
    """
    Main loop for the currency worker.
    Iterates through all active companies and updates their exchange rates.
    """
    logger.info("🚀 Starting Currency Exchange Worker...")
    
    # Initialize provider once
    provider = ExternalRateProvider(banxico_token=settings.int_banxico_token)
    
    async with main_session() as m_session:
        try:
            # 1. Get all active companies from the main DB
            stmt = select(Company.id, Company.base_currency).where(Company.status == "ACTIVE")
            result = await m_session.execute(stmt)
            companies = result.all()
            
            logger.info(f"Found {len(companies)} active companies to update.")
            
            # 2. Update rates for each company using the currency DB
            async with async_session() as c_session:
                service = CurrencyService(c_session, rate_provider=provider)
                
                for cid, base_curr in companies:
                    try:
                        base = base_curr or "USD"
                        # For now, we update common targets. 
                        # In the future, this list could come from company-specific preferences.
                        targets = ["MXN", "EUR"] 
                        
                        logger.info(f"  [Worker] Updating rates for Company: {cid} (Base: {base})")
                        await service.update_rates_automatically(cid, base, targets)
                        logger.info(f"  ✅ Rates updated for {cid}")
                    except Exception as e:
                        logger.error(f"  ❌ Error updating rates for company {cid}: {str(e)}")
            
            logger.info("Done. Currency update cycle completed.")
            
        except Exception as e:
            logger.error(f"CRITICAL: Worker failed: {str(e)}")
            raise
        finally:
            await engine.dispose()
            await main_engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_worker())
