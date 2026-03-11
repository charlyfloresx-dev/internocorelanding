from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.cqrs import ICommand, ICommandHandler
from app.models import UserCompanyRole
from common.exceptions import NotFoundException
from common.repository import BaseRepository
from common.services.audit_service import AuditService

class CompleteOnboardingCommand(ICommand):
    def __init__(self, user_id: UUID, company_id: UUID):
        self.user_id = user_id
        self.company_id = company_id

class CompleteOnboardingCommandHandler(ICommandHandler[dict]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle(self, command: CompleteOnboardingCommand) -> dict:
        # Usamos BaseRepository para integridad multi-tenant
        ucr_repo = BaseRepository(UserCompanyRole, self.db, company_id=command.company_id)
        
        stmt = select(UserCompanyRole).where(
            (UserCompanyRole.user_id == command.user_id) & 
            (UserCompanyRole.company_id == command.company_id)
        )
        result = await self.db.execute(stmt)
        user_company_role = result.scalar_one_or_none()
        
        if not user_company_role:
            raise NotFoundException(entity="UserCompanyRole", entity_id=f"{command.user_id}-{command.company_id}")
        
        user_company_role.is_new = False
        
        # 3. Audit Trail Injection
        await AuditService.log_change(
            db=self.db,
            company_id=command.company_id,
            event_type="ONBOARDING_COMPLETED",
            entity_name="UserCompanyRole",
            entity_id=str(user_company_role.id),
            description=f"User {command.user_id} completed onboarding for company {command.company_id}"
        )
        
        await self.db.commit()
        
        return {"is_new": False}
