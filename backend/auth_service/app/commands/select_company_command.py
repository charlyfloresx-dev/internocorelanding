from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from common.cqrs import ICommand, ICommandHandler
from app.models import UserCompanyRole
from app.core.security import create_access_token
from common.exceptions import UnauthorizedException
from common.repository import BaseRepository

class SelectCompanyCommand(ICommand):
    def __init__(self, user_id: UUID, company_id: UUID):
        self.user_id = user_id
        self.company_id = company_id

class SelectCompanyCommandHandler(ICommandHandler[dict]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle(self, command: SelectCompanyCommand) -> dict:
        # Usamos BaseRepository para verificar la asociación (Tenant Guard)
        ucr_repo = BaseRepository(UserCompanyRole, self.db, company_id=command.company_id)
        
        # El repositorio ya filtrará por company_id
        ucr_stmt = (
            select(UserCompanyRole)
            .where(UserCompanyRole.user_id == command.user_id)
            .where(UserCompanyRole.company_id == command.company_id)
            .options(selectinload(UserCompanyRole.role))
        )
        result = await self.db.execute(ucr_stmt)
        ucr = result.scalar_one_or_none()

        if not ucr:
            raise UnauthorizedException(message="User not associated with this company")

        # Generar Access Token final
        access_token = create_access_token(
            subject=str(command.user_id),
            company_id=str(command.company_id),
            data={
                "role_names": [ucr.role.name],
                "is_new": ucr.is_new
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "company_id": str(command.company_id)
        }
