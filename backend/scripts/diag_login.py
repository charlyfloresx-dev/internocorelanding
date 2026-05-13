import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Mock dependencies
from auth_app.models.user import User
from auth_app.models.user_credential import UserCredential
from auth_app.core.security import verify_password, hash_password
from auth_app.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from auth_app.services.auth_service import AuthService

AUTH_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"

async def diagnose_login():
    engine = create_async_engine(AUTH_DB_URL, pool_pre_ping=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("--- Diagnostic: Charly Login ---")
        # 1. Look for credential
        stmt = select(UserCredential).where(UserCredential.email == "charly@interno.com")
        res = await session.execute(stmt)
        cred = res.scalar_one_or_none()
        
        if not cred:
            print("FAILED: Credential for charly@interno.com not found.")
            return

        print(f"FOUND: Credential ID {cred.id} for User {cred.user_id}")
        print(f"Stored Hash: {cred.hashed_password[:20]}...")
        
        # 2. Verify password manually
        password_to_test = "charly123"
        is_match = verify_password(password_to_test, cred.hashed_password)
        print(f"Manual Verification ('{password_to_test}'): {'SUCCESS' if is_match else 'FAILED'}")
        
        if not is_match:
            # Let's see what hash charly123 produces now
            new_hash = hash_password(password_to_test)
            print(f"Current Hashing produces: {new_hash[:20]}...")
            
        # 3. Check User status
        user = await session.get(User, cred.user_id)
        if user:
            print(f"User Status: {'ACTIVE' if user.is_active else 'INACTIVE'}")
        else:
            print("FAILED: User object not found for this credential.")

    await engine.dispose()

if __name__ == "__main__":
    import os
    import sys
    # Add backend to path to find auth_app
    sys.path.append(os.path.join(os.getcwd(), "backend"))
    sys.path.append(os.path.join(os.getcwd(), "backend", "auth_service"))
    asyncio.run(diagnose_login())
