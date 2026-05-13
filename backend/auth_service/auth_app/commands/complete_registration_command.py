import uuid
from passlib.context import CryptContext
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from common.cqrs import ICommand, ICommandHandler
from auth_app.models import User, Invitation, UserCompanyRole
from common.exceptions import NotFoundException, UnauthorizedException, ConflictException
from common.services.audit_service import AuditService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

class CompleteRegistrationCommand(ICommand):
    def __init__(self, code: str, password: str, full_name: str):
        self.code = code
        self.password = password
        self.full_name = full_name

class CompleteRegistrationCommandHandler(ICommandHandler[dict]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle(self, command: CompleteRegistrationCommand) -> dict:
        async with self.db.begin():
            # 1. Validar código de invitación
            inv_stmt = select(Invitation).where(
                (Invitation.code == command.code) & 
                (Invitation.is_used == False)
            )
            inv_result = await self.db.execute(inv_stmt)
            invitation = inv_result.scalar_one_or_none()
            
            if not invitation:
                raise NotFoundException(message=f"Invitation {command.code} not found")
                
            if invitation.expires_at < datetime.utcnow():
                raise UnauthorizedException(message="Invitation code has expired")

            # 2. Buscar usuario asociado ( stub )
            user_stmt = select(User).where(User.email == invitation.email)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise NotFoundException(message=f"User {invitation.email} not found")

            # 3. Establecer contraseña
            user.hashed_password = pwd_context.hash(command.password)

            # 4. Crear UserCompanyRole
            ucr = UserCompanyRole(
                user_id=user.id,
                company_id=invitation.company_id,
                role_id=invitation.role_id,
                is_new=False
            )
            self.db.add(ucr)
            
            # 5. Marcar invitación como usada
            invitation.is_used = True
            
            # 6. Audit Log
            await AuditService.log_change(
                db=self.db,
                company_id=invitation.company_id,
                event_type="USER_REGISTRATION_COMPLETED",
                entity_name="User",
                entity_id=str(user.id),
                description=f"User {user.email} completed registration via invitation code {command.code}"
            )
            
            # El commit se hace automáticamente al salir del bloque 'async with self.db.begin()'
        
        return {"status": "success", "message": "Registration completed successfully"}
