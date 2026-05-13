import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os

# Get DB URL from docker-compose defaults
AUTH_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"

async def get_users():
    print(f"Connecting to: {AUTH_DB_URL}")
    engine = create_async_engine(AUTH_DB_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            # Join with user_credentials to find email
            res = await conn.execute(text("""
                SELECT u.id, c.email 
                FROM users u 
                LEFT JOIN user_credentials c ON u.id = c.user_id
            """))
            rows = res.fetchall()
            if not rows:
                print("No users found in database.")
            for row in rows:
                print(f"ID: {row[0]}, Email: {row[1]}")
    except Exception as e:
        print(f"Error querying users: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(get_users())
