
import asyncio
from common.infrastructure.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    session = AsyncSessionLocal()
    try:
        res = await session.execute(text('SELECT * FROM movement_concepts'))
        concepts = [dict(row._mapping) for row in res]
        print(f"Total concepts: {len(concepts)}")
        for c in concepts:
            print(f" - {c['name']} (Code: {c['code']}, Type: {c['type']}, OpType: {c.get('operation_type')})")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(check())
