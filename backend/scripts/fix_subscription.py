
import asyncio
from common.infrastructure.database import AsyncSessionLocal
from sqlalchemy import text

async def fix():
    session = AsyncSessionLocal()
    try:
        # Get all subscriptions for Charly's company
        company_id = '9cd9986b-89da-48b7-8733-26a2a1225b01'
        await session.execute(
            text("UPDATE subscriptions SET status = 'ACTIVE' WHERE company_id = :co_id"),
            {"co_id": company_id}
        )
        await session.commit()
        print(f"Subscription for {company_id} set to ACTIVE")
    except Exception as e:
        print(f"Error: {e}")
        await session.rollback()
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(fix())
