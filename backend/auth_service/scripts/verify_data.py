import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"

async def main():
    engine = create_async_engine(DB_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        print("Checking Business Groups:")
        res = await conn.execute(text("SELECT name FROM business_groups"))
        print(res.fetchall())
        
        print("\nChecking Companies:")
        res = await conn.execute(text("SELECT name, status FROM companies"))
        print(res.fetchall())
        
        print("\nChecking Users:")
        res = await conn.execute(text("SELECT email, identity_token FROM users"))
        print(res.fetchall())
        
        print("\nChecking Roles for Charly:")
        res = await conn.execute(text("""
            SELECT c.name, r.name 
            FROM user_company_roles ucr
            JOIN users u ON u.id = ucr.user_id
            JOIN companies c ON c.id = ucr.company_id
            JOIN roles r ON r.id = ucr.role_id
            WHERE u.email = 'charly@interno.com'
        """))
        print(res.fetchall())

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
