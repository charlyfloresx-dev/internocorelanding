import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

async def check_data():
    db_url = os.environ.get("CORE_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5433/dbname")
    engine = create_async_engine(db_url, pool_pre_ping=True)
    
    async with engine.connect() as conn:
        print("--- CONCEPTS CHECK ---")
        result = await conn.execute(text("SELECT count(*) FROM movement_concepts"))
        print(f"Total concepts: {result.scalar()}")
        
        result = await conn.execute(text("SELECT company_id, count(*) FROM movement_concepts GROUP BY company_id"))
        for row in result:
            print(f"Company: {row[0]} | Count: {row[1]}")
            
        print("\n--- ENUMERATIONS CHECK ---")
        result = await conn.execute(text("SELECT count(*) FROM enumerations"))
        print(f"Total enums: {result.scalar()}")
        
        result = await conn.execute(text("SELECT type, count(*) FROM enumerations GROUP BY type"))
        for row in result:
            print(f"Enum Type: {row[0]} | Count: {row[1]}")

if __name__ == "__main__":
    asyncio.run(check_data())
