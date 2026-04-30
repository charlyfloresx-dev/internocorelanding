from pydantic import BaseModel, EmailStr
from typing import List, Optional
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from common.cqrs import IQuery, IQueryHandler
from auth_app.models import User, UserCompanyRole
from auth_app.core.security import verify_password, create_selection_token
from auth_app.schemas import CompanySelection, CompanyAccessDto
from common.exceptions import UnauthorizedException
from common.repository import BaseRepository

class LoginQuery(IQuery[CompanyAccessDto]):
    def __init__(self, email: EmailStr, password: str):
        self.email = email
        self.password = password

class LoginQueryHandler(IQueryHandler[CompanyAccessDto]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle(self, query: LoginQuery) -> CompanyAccessDto:
        from auth_app.models.user_credential import UserCredential
        # 1. Buscar la credencial por email
        stmt = select(UserCredential).where(
            UserCredential.email == query.email,
            UserCredential.credential_type == "PASSWORD"
        )
        result = await self.db.execute(stmt)
        credential = result.scalar_one_or_none()

        if not credential:
            raise UnauthorizedException(message="Incorrect email or password")

        # 2. Validar credenciales
        if not verify_password(query.password, credential.hashed_password) or not credential.is_active:
            raise UnauthorizedException(message="Incorrect credentials or inactive account")
            
        # Validar que el usuario global esté activo
        user = await self.db.get(User, credential.user_id)
        if not user or not user.is_active:
            raise UnauthorizedException(message="Inactive account")
            
        valid_user = user

        # 3. Handshake Token
        selection_token = create_selection_token(subject=str(valid_user.id))

        # 4. Obtener membresías del usuario
        all_user_ids = [valid_user.id]
        ucr_stmt = (
            select(UserCompanyRole)
            .where(UserCompanyRole.user_id.in_(all_user_ids))
            .options(
                selectinload(UserCompanyRole.company),
                selectinload(UserCompanyRole.role)
            )
        )
        ucr_result = await self.db.execute(ucr_stmt)
        memberships = ucr_result.scalars().all()

        companies_map = {}
        for ucr in memberships:
            if ucr.company and ucr.role:
                c_id = ucr.company.id
                c_str = str(c_id)
                if c_str not in companies_map:
                    companies_map[c_str] = {
                        "company_id": c_id,
                        "company_name": ucr.company.name,
                        "group_id": ucr.company.parent_group_id,
                        "group_name": None, # Future: hydration via BG repo if needed
                        "logo": ucr.company.logo,
                        "role_names": [],
                        "is_new": ucr.is_new
                    }
                companies_map[c_str]["role_names"].append(ucr.role.name)

        companies_data = [CompanySelection(**data) for data in companies_map.values()]

        return CompanyAccessDto(
            selection_token=selection_token,
            user_id=valid_user.id,
            companies=companies_data,
            is_new=any(c.is_new for c in companies_data) if companies_data else True
        )
