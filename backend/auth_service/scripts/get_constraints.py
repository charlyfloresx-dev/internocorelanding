import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"

async def main():
    engine = create_async_engine(DB_URL)
    async with engine.begin() as conn:
        res = await conn.execute(text("""
            SELECT 
                tc.constraint_name, 
                tc.table_name, 
                kcu.column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
            WHERE tc.table_name = 'user_company_roles';
        """))
        for row in res.fetchall():
            print(row)
    await engine.dispose()

asyncio.run(main())
