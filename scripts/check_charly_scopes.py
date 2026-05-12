
import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Config from your environment
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5433/auth_db"
CHARLY_ID = uuid.UUID("98b50e2d-dc99-43ef-b387-052637738f61")
ENTERPRISE_ID = uuid.UUID("40446806-0107-6201-9311-000000000001")

async def check_db():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from auth_app.models.user_company_role import UserCompanyRole
        
        result = await session.execute(
            select(UserCompanyRole).where(
                UserCompanyRole.user_id == CHARLY_ID,
                UserCompanyRole.company_id == ENTERPRISE_ID
            )
        )
        ucr = result.scalar_one_or_none()
        if ucr:
            print(f"User: {ucr.user_id}")
            print(f"Company: {ucr.company_id}")
            print(f"Scopes: {ucr.scopes}")
        else:
            print("No association found for Charly in Enterprise")

if __name__ == "__main__":
    import sys
    import os
    # Add auth_app to path
    sys.path.append(os.path.join(os.getcwd(), "backend"))
    sys.path.append(os.path.join(os.getcwd(), "backend", "auth_service"))
    asyncio.run(check_db())
