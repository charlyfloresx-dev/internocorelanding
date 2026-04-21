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
        # 1. Buscar identidades asociadas al email (BaseRepository para User)
        user_repo = BaseRepository(User, self.db)
        
        # Filtramos manualmente por email ya que no hay company_id en este punto (identidad multi-silo)
        stmt = select(User).where(User.email == query.email)
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        if not users:
            raise UnauthorizedException(message="Incorrect email or password")

        # 2. Validar credenciales
        valid_user = None
        for u in users:
            if verify_password(query.password, u.hashed_password) and u.is_active:
                valid_user = u
                break
        
        if not valid_user:
            raise UnauthorizedException(message="Incorrect credentials or inactive account")

        # 3. Handshake Token
        selection_token = create_selection_token(subject=str(valid_user.id))

        # 4. Obtener membresías de todas las identidades encontradas
        all_user_ids = [u.id for u in users]
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
