# Simple Column Check
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"

async def check_table(table):
    engine = create_async_engine(DB_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        res = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"))
        cols = [r[0] for r in res.fetchall()]
        print(f"TABLE {table}: {cols}")
    await engine.dispose()

async def main():
    await check_table('users')
    await check_table('companies')
    await check_table('roles')
    await check_table('user_company_roles')

if __name__ == "__main__":
    asyncio.run(main())
