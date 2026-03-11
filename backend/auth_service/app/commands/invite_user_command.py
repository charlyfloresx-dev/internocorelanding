import uuid
import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.cqrs import ICommand, ICommandHandler
from app.models import User, Invitation, Company, Role
from common.exceptions import NotFoundException, ConflictException
from common.services.audit_service import AuditService
from app.schemas.invitation import InvitationCreate, InvitationResponse

class InviteUserCommand(ICommand):
    def __init__(self, email: str, role_id: uuid.UUID, company_id: uuid.UUID):
        self.email = email
        self.role_id = role_id
        self.company_id = company_id

class InviteUserCommandHandler(ICommandHandler[InvitationResponse]):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_code(self, length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    async def handle(self, command: InviteUserCommand) -> InvitationResponse:
        # 1. Verificar que la empresa existe
        company_stmt = select(Company).where(Company.id == command.company_id)
        company_result = await self.db.execute(company_stmt)
        if not company_result.scalar_one_or_none():
            raise NotFoundException(entity="Company", entity_id=str(command.company_id))

        # 2. Verificar que el rol existe
        role_stmt = (
            select(Role)
            .where(Role.id == command.role_id)
            .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
        )
        role_result = await self.db.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException(entity="Role", entity_id=str(command.role_id))

        # --- GATING DE SUSCRIPCIÓN DINÁMICO ---
        from common.context import request_context
        ctx = request_context.get()
        if ctx and hasattr(ctx, "entitlements") and ctx.entitlements:
            active_modules = ctx.entitlements.get("modules", [])
            
            # Verificar si el rol tiene al menos un permiso de un módulo no suscrito
            for rp in role.role_permissions:
                if rp.permission.module_name not in active_modules:
                    raise ConflictException(message=f"MODULE_NOT_SUBSCRIBED: El rol '{role.name}' contiene permisos del módulo '{rp.permission.module_name}' que no está activo.")

        # 3. Crear usuario "stub" si no existe
        user_stmt = select(User).where(User.email == command.email)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            user = User(
                email=command.email,
                hashed_password=None, # Pendiente de registro
                company_id=command.company_id,
                is_active=True
            )
            self.db.add(user)
            await self.db.flush() # Para obtener el ID del usuario si se necesita

        # 4. Generar código único de invitación
        code = self._generate_code()
        
        # 5. Crear invitación
        invitation = Invitation(
            email=command.email,
            code=code,
            role_id=command.role_id,
            company_id=command.company_id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.db.add(invitation)
        
        # 6. Audit Log
        await AuditService.log_change(
            db=self.db,
            company_id=command.company_id,
            event_type="USER_INVITED",
            entity_name="Invitation",
            entity_id=str(invitation.id),
            description=f"User {command.email} invited to company {command.company_id} with role {command.role_id}"
        )
        
        await self.db.commit()
        await self.db.refresh(invitation)
        
        return InvitationResponse.from_orm(invitation)
