import uuid
from typing import List, Tuple, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import User, UserCompanyRole
from app.core.security import verify_password

class AuthService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def get_user_companies(db: AsyncSession, user_id: uuid.UUID) -> List[dict]:
        stmt = (
            select(UserCompanyRole)
            .where(UserCompanyRole.user_id == user_id)
            .options(selectinload(UserCompanyRole.company))
            .options(selectinload(UserCompanyRole.role))
        )
        result = await db.execute(stmt)
        ucr_list = result.scalars().all()
        
        companies = []
        for ucr in ucr_list:
            if ucr.company:
                companies.append({
                    "company_id": ucr.company.id,
                    "company_name": ucr.company.name,
                    "logo": ucr.company.logo,
                    "is_new": ucr.is_new,
                    "role_names": [ucr.role.name] if ucr.role else []
                })
        return companies

    @staticmethod
    async def get_user_context_for_company(
        db: AsyncSession, user_id: uuid.UUID, company_id: uuid.UUID
    ) -> Tuple[List[str], List[str]]:
        """
        Obtiene los roles y scopes de un usuario para una compañía específica.
        
        ESTA ES LA CORRECCIÓN CRÍTICA:
        Ahora la función devuelve tanto los roles como los scopes.
        """
        stmt = (
            select(UserCompanyRole)
            .where(UserCompanyRole.user_id == user_id, UserCompanyRole.company_id == company_id)
            .options(selectinload(UserCompanyRole.role))
        )
        result = await db.execute(stmt)
        relation = result.scalar_one_or_none()

        if not relation or not relation.role:
            return [], []

        roles = [relation.role.name]
        scopes = relation.scopes or []
        return (roles, scopes)