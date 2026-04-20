from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine(settings.ASYNC_DATABASE_URL)
    async with engine.begin() as conn:
        print("Executing cleanup...")
        # 1. Keep only one user_company_roles per user/company combination (delete duplicates)
        res = await conn.execute(text(
            """
            DELETE FROM user_company_roles
            WHERE id IN (
                SELECT id
                FROM (
                    SELECT id,
                    ROW_NUMBER() OVER (partition BY user_id, company_id ORDER BY created_at DESC) as rnum
                    FROM user_company_roles
                ) t
                WHERE t.rnum > 1
            );
            """
        ))
        print("Deleted duplicated UserCompanyRoles:", res.rowcount)
        
        # 2. Delete duplicate users (if any exist) sharing the same email
        res2 = await conn.execute(text(
            """
            DELETE FROM users
            WHERE id IN (
                SELECT id
                FROM (
                    SELECT id,
                    ROW_NUMBER() OVER (partition BY email ORDER BY created_at ASC) as rnum
                    FROM users
                ) t
                WHERE t.rnum > 1
            );
            """
        ))
        print("Deleted duplicated Users:", res2.rowcount)

if __name__ == "__main__":
    asyncio.run(main())
