
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5433/inventory_db"

async def check():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, code, name FROM inventory_warehouses"))
        for row in res:
            print(f"ID: {row[0]}, CODE: {row[1]}, NAME: {row[2]}")
            
if __name__ == "__main__":
    asyncio.run(check())
