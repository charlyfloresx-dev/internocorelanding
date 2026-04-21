import asyncio
import uuid
from sqlalchemy import text
from inventory_app.db.session import AsyncSessionLocal

async def inspect():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT company_id, destination_company_id, folio FROM inter_company_transfers WHERE folio = 'ICT-TEST-50'"))
        row = res.fetchone()
        if row:
            print(f"DEBUG: Folio FOUND: {row[2]}")
            print(f"DEBUG: origin_company_id (DB):      {row[0]} (Type: {type(row[0])})")
            print(f"DEBUG: destination_company_id (DB): {row[1]} (Type: {type(row[1])})")
        else:
            print("DEBUG: Folio NOT FOUND")

if __name__ == "__main__":
    asyncio.run(inspect())
