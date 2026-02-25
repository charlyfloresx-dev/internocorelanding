from uuid import UUID, uuid4
import logging
from fastapi import status as http_status
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from common.cqrs import ICommand, ICommandHandler
from app.models import UserCompanyRole
from app.core.security import create_access_token
from common.exceptions import UnauthorizedException
from common.repository import BaseRepository
from common.responses import ApiResponse
from app.infrastructure.clients.subscription_client import SubscriptionClient

class SelectCompanyCommand(ICommand):
    def __init__(self, user_id: UUID, company_id: UUID):
        self.user_id = user_id
        self.company_id = company_id

class SelectCompanyCommandHandler(ICommandHandler[dict]):
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def handle(self, command: SelectCompanyCommand) -> dict:
        # 0. Generar Correlation ID para trazabilidad
        correlation_id = str(uuid4())
        self.logger.info(f"🔍 [Handshake Start] Correlation: {correlation_id} | Company: {command.company_id}")

        # 1. Obtener Entitlements (Licencias) - Resiliencia Mejorada
        sub_client = SubscriptionClient()
        modules = ["auth_core", "inventory_core"]
        sub_status = "TRIAL"
        readonly = False
        
        try:
            data = await sub_client.get_company_entitlements(str(command.company_id), correlation_id=correlation_id)
            if isinstance(data, dict):
                modules = data.get("modules", modules)
                sub_status = data.get("status", sub_status)
                
                # Seguridad: Bloqueo por Expiración
                if sub_status == "EXPIRED":
                    self.logger.error(f"🚨 [SECURITY] Subscription EXPIRED for {command.company_id}. Denying access. Correlation: {correlation_id}")
                    # Usamos 402 Payment Required como se pidió
                    return JSONResponse(
                        status_code=402,
                        content={
                            "status": "error",
                            "message": "Suscripción expirada. Por favor, realice el pago.",
                            "meta": {"correlation_id": correlation_id}
                        }
                    )

                # Regla de Negocio: PAST_DUE fuerza readonly
                if sub_status == "PAST_DUE":
                    readonly = True
                    self.logger.warning(f"⚠️ [Handshake] Sesión iniciada en modo restringido (Periodo de Gracia) para {command.company_id}. Correlation: {correlation_id}")

                self.logger.info(f"✅ [Handshake Success] {command.company_id}: {modules} | Correlation: {correlation_id}")
        except Exception as e:
            self.logger.warning(f"⚠️ [Handshake Fallback] Connection failure for {command.company_id}, applying readonly core mode. Error: {e} | Correlation: {correlation_id}")
            readonly = True 

        # 2. Usamos BaseRepository para verificar la asociación (Tenant Guard)
        ucr_repo = BaseRepository(UserCompanyRole, self.db, company_id=command.company_id)
        
        ucr_stmt = (
            select(UserCompanyRole)
            .where(UserCompanyRole.user_id == command.user_id)
            .where(UserCompanyRole.company_id == command.company_id)
            .options(selectinload(UserCompanyRole.role))
        )
        result = await self.db.execute(ucr_stmt)
        ucr = result.scalar_one_or_none()

        if not ucr:
            self.logger.warning(f"🚫 Intento de acceso no autorizado: User {command.user_id} -> Company {command.company_id}")
            raise UnauthorizedException(message="User not associated with this company")

        # 3. Generar Access Token final (Enriquecido con módulos, estado y correlation_id)
        access_token = create_access_token(
            subject=str(command.user_id),
            company_id=str(command.company_id),
            data={
                "role_names": [ucr.role.name],
                "is_new": ucr.is_new,
                "modules": modules,
                "status": sub_status,
                "readonly": readonly,
                "correlation_id": correlation_id
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "company_id": str(command.company_id)
        }
