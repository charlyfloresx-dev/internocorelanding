import asyncio
from sqlalchemy import text
from common.infrastructure.database import AsyncSessionLocal

async def check_auth_data():
    async with AsyncSessionLocal() as session:
        try:
            # Check users and credentials
            res = await session.execute(text("""
                SELECT uc.email, u.is_active 
                FROM users u 
                JOIN user_credentials uc ON u.id = uc.user_id
            """))
            users = res.all()
            print(f"DEBUG: Found {len(users)} users with credentials:")
            for u in users:
                print(f" - {u.email} (Active: {u.is_active})")
            
            # Check companies
            res = await session.execute(text("SELECT id, name, status FROM companies"))
            companies = res.all()
            print(f"DEBUG: Found {len(companies)} companies:")
            for c in companies:
                print(f" - {c.name} (ID: {c.id}, Status: {c.status})")
            
        except Exception as e:
            print(f"DEBUG: Error checking Auth data: {e}")

if __name__ == "__main__":
    asyncio.run(check_auth_data())
