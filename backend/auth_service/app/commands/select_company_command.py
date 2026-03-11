from uuid import UUID, uuid4
import logging
from app.domain.repositories.user_company_role_repository import IUserCompanyRoleRepository
from app.domain.repositories.permission_repository import IPermissionRepository
from app.services.permission_checker import PermissionChecker
from common.cqrs import ICommand, ICommandHandler
from app.core.security import create_access_token
from common.exceptions import UnauthorizedException
from common.responses import ApiResponse
from app.infrastructure.clients.subscription_client import SubscriptionClient
from common.services.audit_service import AuditService
from sqlalchemy.ext.asyncio import AsyncSession

class SelectCompanyCommand(ICommand):
    def __init__(self, user_id: UUID, company_id: UUID):
        self.user_id = user_id
        self.company_id = company_id

class SelectCompanyCommandHandler(ICommandHandler[dict]):
    def __init__(self, ucr_repo: IUserCompanyRoleRepository, permission_repo: IPermissionRepository, db: AsyncSession):
        self.ucr_repo = ucr_repo
        self.db = db
        self.permission_checker = PermissionChecker(permission_repo)
        self.logger = logging.getLogger(__name__)

    async def handle(self, command: SelectCompanyCommand) -> dict:
        correlation_id = str(uuid4())
        self.logger.info(f"🔍 [Handshake Start] Correlation: {correlation_id} | Company: {command.company_id}")

        # 1. Obtener Entitlements (Licencias)
        sub_client = SubscriptionClient()
        modules = ["auth_core", "inventory_core"]
        sub_status = "TRIAL"
        readonly = False
        
        try:
            data = await sub_client.get_company_entitlements(str(command.company_id), correlation_id=correlation_id)
            if isinstance(data, dict):
                meta = data.get("meta", {})
                modules = meta.get("modules", modules)
                sub_status = meta.get("status", sub_status)
                if sub_status == "EXPIRED":
                    return ApiResponse.error(message="Suscripción expirada", status_code=402)
                if sub_status == "PAST_DUE":
                    readonly = True
        except Exception as e:
            self.logger.warning(f"⚠️ [Handshake Fallback]: {e}")
            readonly = True 

        # 2. Verificar Asociación y Obtener Permisos via Repositories (Pure Domain)
        ucr = await self.ucr_repo.get_by_user_and_company(command.user_id, command.company_id)

        if not ucr:
            raise UnauthorizedException(message="User not associated with this company")

        # HIDRATACIÓN DINÁMICA
        permissions = list(await self.permission_checker.get_user_permissions(command.user_id, command.company_id))
        
        # 3. Generar Access Token final
        access_token = create_access_token(
            subject=str(command.user_id),
            company_id=str(command.company_id),
            data={
                "role_names": ucr.role_names,
                "permissions": permissions,
                "scopes": ucr.scopes,
                "modules": modules,
                "status": sub_status,
                "readonly": readonly,
                "correlation_id": correlation_id
            }
        )
        
        # 4. Audit logging (Atomic with Transaction)
        await AuditService.log_action(
            db=self.db,
            user_id=command.user_id,
            action="SELECT_COMPANY",
            entity_name="CompanyAccess",
            entity_id=command.company_id,
            details=f"method: X-Selection-Token, correlation_id: {correlation_id}"
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "company_id": str(command.company_id),
            "roles": ucr.role_names,
            "scopes": ucr.scopes,
            "permissions": permissions
        }
