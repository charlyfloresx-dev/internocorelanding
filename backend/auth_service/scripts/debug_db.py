# Debug DB Script - JSON Output
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"

async def debug_db():
    engine = create_async_engine(DB_URL)
    results = {}
    try:
        async with engine.begin() as conn:
            res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            results["tables"] = [r[0] for r in res.fetchall()]
            for table in results["tables"]:
                res = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"))
                results[f"{table}_cols"] = [r[0] for r in res.fetchall()]
        print("---JSON_START---")
        print(json.dumps(results))
        print("---JSON_END---")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_db())
