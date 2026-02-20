from typing import Generator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_db() -> Generator:
    async with SessionLocal() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    # TODO: Validar token contra Auth Service o decodificar JWT localmente
    return {"company_id": "00000000-0000-0000-0000-000000000000", "user_id": "demo-user"}