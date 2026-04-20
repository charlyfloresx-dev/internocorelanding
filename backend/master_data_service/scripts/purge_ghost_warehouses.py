
import asyncio
import sys
sys.path.insert(0, '.')
from app.db.db import async_session
from app.models.warehouse import Warehouse
from sqlalchemy import delete
import uuid

# Solo estas dos son companies válidas del ecosistema
VALID_COMPANY_IDS = {
    uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242"),  # CO_LOGISTICS_MX
    uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277"),  # CO_LOGISTICS_US
}

async def purge_ghost_warehouses():
    async with async_session() as session:
        result = await session.execute(
            delete(Warehouse).where(
                Warehouse.company_id.notin_(list(VALID_COMPANY_IDS))
            )
        )
        await session.commit()
        print(f"✅ Purged {result.rowcount} ghost warehouse(s) from invalid companies.")

if __name__ == "__main__":
    asyncio.run(purge_ghost_warehouses())
