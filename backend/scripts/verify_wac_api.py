import asyncio
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import httpx
import json

MASTER_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"
INV_SERVICE_URL = "http://localhost:8006/api/v1/dashboard/reports/valuation"
COMPANY_ID = "11111111-1111-4111-8111-123456789abc"
WAREHOUSE_ID = "aa11aaaa-aaaa-4aaa-8aaa-123456789abc"

async def verify_wac():
    # Pick a product that actually has movements to verify calculation
    engine_inv = create_async_engine("postgresql+asyncpg://user:password@localhost:5433/inventory_db", pool_pre_ping=True)
    async with engine_inv.connect() as conn:
        res = await conn.execute(text("SELECT product_id FROM inventory_movements WHERE company_id = :cid LIMIT 1"), {"cid": COMPANY_ID})
        row = res.fetchone()
        if not row:
            print("No movements found in inventory_movements")
            return
        pid = row[0]
        print(f"Testing Product from Movements: {pid}")

    await engine_inv.dispose()

    async with httpx.AsyncClient() as client:
        params = {
            "product_id": str(pid),
            "warehouse_id": WAREHOUSE_ID
        }
        headers = {
            "X-Company-Id": COMPANY_ID
        }
        response = await client.get(INV_SERVICE_URL, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("--- WAC Valuation Response ---")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_wac())
