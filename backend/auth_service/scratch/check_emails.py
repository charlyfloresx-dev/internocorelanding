import asyncio
from sqlalchemy import text
from auth_app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT email FROM user_credentials"))
        emails = [row[0] for row in r.fetchall()]
        print(f"EMAILS: {emails}")

if __name__ == "__main__":
    asyncio.run(check())
