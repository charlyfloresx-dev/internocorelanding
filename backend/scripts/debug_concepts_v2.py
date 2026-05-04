import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

async def list_concepts():
    db_url = os.environ.get("CORE_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5433/dbname")
    engine = create_async_engine(db_url)
    
    async with engine.connect() as conn:
        print("--- CONCEPTS FULL DATA ---")
        try:
            result = await conn.execute(text("SELECT * FROM movement_concepts"))
            cols = result.keys()
            rows = result.fetchall()
            for row in rows:
                data = dict(zip(cols, row))
                print(data)
        except Exception as e:
            print(f"Error querying concepts: {e}")

if __name__ == "__main__":
    asyncio.run(list_concepts())
