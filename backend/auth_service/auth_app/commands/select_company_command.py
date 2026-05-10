from uuid import UUID, uuid4
import logging
from datetime import datetime, timezone, timedelta

from auth_app.domain.repositories.user_company_role_repository import IUserCompanyRoleRepository
from auth_app.domain.repositories.permission_repository import IPermissionRepository
from auth_app.services.permission_checker import PermissionChecker
from common.cqrs import ICommand, ICommandHandler
from auth_app.core.security import create_access_token, create_refresh_token, hash_token
from auth_app.core.config import settings
from auth_app.models.refresh_token import RefreshToken
from auth_app.models.user import User
from auth_app.models.company import Company
from common.exceptions import UnauthorizedException
from common.responses import ApiResponse
from auth_app.infrastructure.clients.subscription_client import SubscriptionClient
from common.services.audit_service import AuditService
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from fastapi import status

# 🗺️ SCOPE RESOLVER: Mapea roles → scopes del sidebar (frontend)
# Fuente de verdad: frontend/src/app/core/services/navigation.service.ts
ROLE_SCOPE_MAP = {
    "admin": ["*", "investments:manage", "investments:admin"],
    "owner": ["*", "investments:manage", "investments:admin"],
    "manager": [
        "inv:movements:manage", "inv:warehouse:manage", "inventory:admin",
        "master:catalog:manage", "catalog:admin",
        "wms:manage",
        "auth:user:manage",
        "investments:manage",
    ],
    "warehouse_operator": [
        "inv:movements:manage", "inv:warehouse:manage",
        "master:catalog:manage",
    ],
    "collaborator": [
        "inv:movements:manage",
    ],
}

def resolve_scopes(role_names: list, explicit_scopes: list) -> list:
    """Resuelve scopes: usa los explícitos si existen, sino los deriva del rol."""
    if explicit_scopes:
        if "*" in explicit_scopes:
            # Expand to ALL known scopes if super-admin
            all_scopes = set()
            for scopes in ROLE_SCOPE_MAP.values():
                all_scopes.update(scopes)
            return list(all_scopes)
        return explicit_scopes
    resolved = set()
    for role in role_names:
        key = role.lower().strip()
        if key in ROLE_SCOPE_MAP:
            resolved.update(ROLE_SCOPE_MAP[key])
    if "*" in resolved:
        all_scopes = set()
        for scopes in ROLE_SCOPE_MAP.values():
            all_scopes.update(scopes)
        return list(all_scopes)
    return list(resolved) if resolved else ["inv:movements:manage"]

class SelectCompanyCommand(ICommand):
    def __init__(self, user_id: UUID, company_id: UUID):
        self.user_id = user_id
        self.company_id = company_id


class SelectCompanyCommandHandler(ICommandHandler[dict]):
    def __init__(
        self,
        ucr_repo: IUserCompanyRoleRepository,
        permission_repo: IPermissionRepository,
        db: AsyncSession,
    ):
        self.ucr_repo = ucr_repo
        self.db = db
        self.permission_checker = PermissionChecker(permission_repo)
        self.logger = logging.getLogger(__name__)

    async def handle(self, command: SelectCompanyCommand) -> dict:
        correlation_id = str(uuid4())
        self.logger.info(
            f"🔍 [Handshake Start] Correlation: {correlation_id} | Company: {command.company_id}"
        )

        # 1. Obtener Entitlements (Licencias)
        # We need an AuthService instance here, but for now we'll keep it simple or inject it.
        # Actually, let's keep it as is or use the new service if possible.
        # Since I'm refactoring, I'll pass auth_service to handle() or constructor.
        # But wait, I'll just keep it here for now to avoid breaking too much, 
        # but I'll update it to match the logic of the service.
        sub_client = SubscriptionClient()
        modules = ["auth_core", "inventory_core"]
        sub_status = "TRIAL"
        readonly = False

        try:
            data = await sub_client.get_company_entitlements(
                str(command.company_id), correlation_id=correlation_id
            )
            entitlements = data.get("data", data) if isinstance(data, dict) else {}
            meta = data.get("meta", {}) if isinstance(data, dict) else {}
            
            sub_status = meta.get("status", entitlements.get("status", "TRIAL"))
            readonly = entitlements.get("readonly", False)
            modules = meta.get("modules", entitlements.get("modules", modules))
            
            if sub_status == "EXPIRED":
                return ApiResponse.error(message="Subscription expired", status_code=402)
            if sub_status == "PAST_DUE":
                readonly = True
        except Exception as e:
            self.logger.warning(f"⚠️ [Handshake Fallback]: {e}")
            readonly = True
            sub_status = "PAST_DUE"

        # 2. Verificar Asociación y Obtener Permisos via Repositories (Pure Domain)
        ucr = await self.ucr_repo.get_by_user_and_company(command.user_id, command.company_id)

        if not ucr:
            # FALLBACK: Verificación Industrial (Colaborador)
            # Si no existe en Auth asocialo a un flujo de colaborador en HR
            self.logger.info(f"⚠️ [Collaborator Check] ID {command.user_id} not in Auth. Checking HR Service...")
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    hr_res = await client.post(
                        f"{settings.HCM_SERVICE_URL}/api/v1/internal/collaborators/verify",
                        json={
                            "company_id": str(command.company_id),
                            "internal_id": None, # Usamos discovery por UUID de colaborador
                            "rfid_tag": None,
                            "collaborator_id": str(command.user_id) # Debemos asegurar que el endpoint de HR soporte esto
                        },
                        headers={"X-Internal-Api-Key": settings.INTERNAL_API_KEY},
                    )
                
                if hr_res.status_code == 200:
                    hr_response = hr_res.json()
                    hr_data = hr_response.get("data", {})
                    matches = hr_data.get("matches", [])
                    if matches:
                        # ¡Luis Torres detectado para esta empresa!
                        match = matches[0]
                        self.logger.info(f"✅ [Collaborator Success] {match['full_name']} verified for {command.company_id}")
                        
                        # Construir Scopes y Permisos dinámicamente
                        is_sup = match.get("is_supervisor", False)
                        dept = match.get("department", "")
                        
                        coll_perms = ["PHYSICAL_SCAN"] # Permisos granulares de acción
                        coll_roles = ["collaborator"]
                        
                        if is_sup or dept == "Warehouse":
                            coll_perms.extend(["INVENTORY_READ", "INVENTORY_WRITE"])
                            coll_roles.append("warehouse_operator")
                        
                        # Resolver scopes del sidebar basado en roles
                        coll_scopes = resolve_scopes(coll_roles, [])
                        
                        # Generar Token de Colaborador con el ID REAL de esa empresa
                        return await self._generate_collaborator_response(
                            command=command,
                            real_collaborator_id=match["collaborator_id"],
                            full_name=match["full_name"],
                            internal_id=match["internal_id"],
                            is_supervisor=is_sup,
                            warehouse_id=match.get("home_warehouse_id"),
                            department=dept,
                            permissions=coll_perms,
                            scopes=coll_scopes,
                            modules=modules,
                            sub_status=sub_status,
                            readonly=readonly,
                            correlation_id=correlation_id
                        )
            except Exception as e:
                self.logger.error(f"❌ HR Fallback failed: {e}")
            
            raise UnauthorizedException(message="User not associated with this company")

        # HIDRATACIÓN DINÁMICA
        permissions = list(
            await self.permission_checker.get_user_permissions(command.user_id, command.company_id)
        )

        # 3. Generar Access Token final (15 min, typ: "access")
        access_token = create_access_token(
            subject=str(command.user_id),
            company_id=str(command.company_id),
            data={
                "role_names": ucr.role_names,
                "permissions": permissions,
                "scopes": resolve_scopes(ucr.role_names, ucr.scopes),
                "modules": modules,
                "status": sub_status,
                "readonly": readonly,
                "correlation_id": correlation_id,
                "group_id": str(ucr.group_id) if ucr.group_id else None,
            },
        )

        # 4. Generar Refresh Token (30 días, typ: "refresh", persistido en DB)
        raw_refresh = create_refresh_token(
            subject=command.user_id,
            company_id=command.company_id,
        )
        refresh_record = RefreshToken(
            user_id=command.user_id,
            company_id=command.company_id,
            tenant_id=command.company_id,
            token_hash=hash_token(raw_refresh),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
            revoked=False,
        )
        self.db.add(refresh_record)

        # 5. Audit logging (Atomic with Transaction)
        await AuditService.log_action(
            db=self.db,
            user_id=command.user_id,
            action="SELECT_COMPANY",
            entity_name="CompanyAccess",
            entity_id=command.company_id,
            details=f"method: X-Selection-Token, correlation_id: {correlation_id}",
        )

        # Fetch user to hydrate email in response
        user_obj = await self.db.get(User, command.user_id)
        from auth_app.models.user_credential import UserCredential
        from sqlalchemy import select
        cred = await self.db.execute(select(UserCredential).where(UserCredential.user_id == command.user_id))
        primary_cred = cred.first()
        user_email = primary_cred[0].email if primary_cred else None
        
        full_name = getattr(user_obj, "full_name", None)
        if not full_name and user_obj:
            first = getattr(user_obj, "first_name", "") or ""
            last = getattr(user_obj, "last_name_pat", "") or ""
            full_name = f"{first} {last}".strip()

        resolved_scopes = resolve_scopes(ucr.role_names, ucr.scopes)

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "token_type": "bearer",
            "user_id": str(command.user_id),
            "company_id": str(command.company_id),
            "company_name": ucr.company_name or "Interno Core",
            "group_id": str(ucr.group_id) if ucr.group_id else None,
            "roles": ucr.role_names,
            "scopes": resolved_scopes,
            "permissions": permissions,
            "user_email": user_email,
            "user_full_name": full_name or user_email,
            "user": {
                "id": str(command.user_id),
                "email": user_email,
                "full_name": full_name or user_email,
                "is_active": True
            },
            "status": sub_status,
            "readonly": readonly,
            "default_tax_rate": getattr(ucr, "default_tax_rate", 0.16) if ucr else 0.16,
        }
    async def _generate_collaborator_response(
        self, command, real_collaborator_id, full_name, internal_id, is_supervisor, warehouse_id, department, 
        permissions, scopes, modules, sub_status, readonly, correlation_id
    ) -> dict:
        """Helper para generar el JWT y la respuesta final para un colaborador industrial."""
        access_token = create_access_token(
            subject=str(real_collaborator_id), # Usamos el ID específico de la empresa
            company_id=str(command.company_id),
            data={
                "role_names": ["collaborator"],
                "permissions": permissions,
                "scopes": scopes, # Lo que el Menú sidebar necesita leer
                "modules": modules,
                "status": sub_status,
                "readonly": readonly,
                "correlation_id": correlation_id,
                # Campos extra para el Kiosco
                "is_supervisor": is_supervisor,
                "internal_id": internal_id,
                "full_name": full_name,
                "department": department,
                "warehouse_id": str(warehouse_id) if warehouse_id else None,
                "role": "collaborator"
            },
        )
        
        # Auditoría del login industrial
        await AuditService.log_action(
            db=self.db,
            user_id=command.user_id,
            action="COLLABORATOR_SELECT_COMPANY",
            entity_name="CollaboratorAccess",
            entity_id=command.company_id,
            details=f"Identity: {full_name} ({internal_id})",
        )
 
        # Resolve company name for the header
        company_obj = await self.db.get(Company, command.company_id)
        company_name = company_obj.name if company_obj else "Interno Core"
 
        return {
            "access_token": access_token,
            "refresh_token": None, 
            "token_type": "bearer",
            "user_id": str(real_collaborator_id),
            "company_id": str(command.company_id),
            "company_name": company_name,
            "group_id": str(company_obj.parent_group_id) if company_obj and company_obj.parent_group_id else None,
            "roles": ["collaborator"],
            "scopes": scopes,
            "permissions": permissions,
            "user_full_name": full_name,
            "user": {
                "id": str(real_collaborator_id),
                "email": None,
                "full_name": full_name,
                "is_active": True
            },
            "status": sub_status,
            "readonly": readonly,
            "default_tax_rate": getattr(company_obj, "default_tax_rate", 0.16) if company_obj else 0.16,
        }
