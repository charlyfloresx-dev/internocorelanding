import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

async def list_concepts():
    db_url = os.environ.get("CORE_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5433/dbname")
    engine = create_async_engine(db_url, pool_pre_ping=True)
    
    async with engine.connect() as conn:
        print("--- CONCEPTS IN DB ---")
        try:
            result = await conn.execute(text("SELECT id, name, code, type FROM movement_concepts"))
            rows = result.fetchall()
            for row in rows:
                print(f"ID: {row.id} | Name: {row.name} | Code: {row.code} | Type: {row.type}")
        except Exception as e:
            print(f"Error querying concepts: {e}")
            
        print("\n--- ENUMERATIONS IN DB ---")
        try:
            result = await conn.execute(text("SELECT type, key, label FROM enumerations"))
            rows = result.fetchall()
            for row in rows:
                print(f"Type: {row.type} | Key: {row.key} | Label: {row.label}")
        except Exception as e:
            print(f"Error querying enumerations: {e}")

if __name__ == "__main__":
    asyncio.run(list_concepts())
