import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.cqrs import ICommand, ICommandHandler
from app.models import User, Role, UserCompanyRole
from common.exceptions import NotFoundException, ConflictException
from common.services.audit_service import AuditService

class AssignRoleCommand(ICommand):
    def __init__(self, email: str, role_id: uuid.UUID, company_id: uuid.UUID):
        self.email = email
        self.role_id = role_id
        self.company_id = company_id

class AssignRoleCommandHandler(ICommandHandler[dict]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle(self, command: AssignRoleCommand) -> dict:
        # 1. Buscar el usuario globalmente
        user_stmt = select(User).where(User.email == command.email)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException(entity="User", entity_id=command.email)

        # 2. Verificar que el rol existe
        role_stmt = select(Role).where(Role.id == command.role_id)
        role_result = await self.db.execute(role_stmt)
        if not role_result.scalar_one_or_none():
            raise NotFoundException(entity="Role", entity_id=str(command.role_id))

        # 3. Verificar si ya existe el rol para esa empresa
        ucr_stmt = select(UserCompanyRole).where(
            (UserCompanyRole.user_id == user.id) &
            (UserCompanyRole.company_id == command.company_id) &
            (UserCompanyRole.role_id == command.role_id)
        )
        ucr_result = await self.db.execute(ucr_stmt)
        if ucr_result.scalar_one_or_none():
            raise ConflictException(message=f"User already has this role in the specified company")

        # 4. Crear la relación
        ucr = UserCompanyRole(
            user_id=user.id,
            company_id=command.company_id,
            role_id=command.role_id,
            is_new=False # No es nuevo si es asignado por admin
        )
        self.db.add(ucr)
        
        # 5. Audit Log
        await AuditService.log_change(
            db=self.db,
            company_id=command.company_id,
            event_type="ROLE_ASSIGNED_BY_ADMIN",
            entity_name="UserCompanyRole",
            entity_id=f"{user.id}-{command.role_id}",
            description=f"Admin assigned role {command.role_id} to user {user.id} in company {command.company_id}"
        )
        
        await self.db.commit()
        
        return {"status": "success", "message": "Role assigned successfully"}
