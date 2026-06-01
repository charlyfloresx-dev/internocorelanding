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

_ADMIN_ROLES = {"admin", "owner"}


def _build_scopes(role_names: list, ucr_scopes: list, db_permissions: list) -> list:
    """Returns JWT scopes from DB permission slugs. Admin/owner roles → wildcard ["*"]."""
    if ucr_scopes and "*" in ucr_scopes:
        return ["*"]
    if any(r.lower() in _ADMIN_ROLES for r in (role_names or [])):
        return ["*"]
    return list(db_permissions) if db_permissions else []


async def _load_role_slugs_by_name(db, role_name: str) -> list:
    """Loads Permission slugs for a system role (company_id IS NULL) from DB."""
    from sqlalchemy import text
    result = await db.execute(text("""
        SELECT p.slug FROM permissions p
        JOIN role_permissions rp ON rp.permission_id = p.id
        JOIN roles r ON r.id = rp.role_id
        WHERE r.name = :role_name AND r.company_id IS NULL AND r.is_active = true
        ORDER BY p.slug
    """), {"role_name": role_name})
    return [row[0] for row in result.fetchall()]


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
            self.logger.warning(f"[Handshake Fallback]: {e}")
            readonly = True
            sub_status = "PAST_DUE"

        # 2. Verificar Asociación y Obtener Permisos via Repositories (Pure Domain)
        ucr = await self.ucr_repo.get_by_user_and_company(command.user_id, command.company_id)

        if not ucr:
            # FALLBACK: Verificación Industrial (Colaborador)
            # Si no existe en Auth asocialo a un flujo de colaborador en HR
            self.logger.info(f"[Collaborator Check] ID {command.user_id} not in Auth. Checking HR Service...")
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
                        self.logger.info(f"[Collaborator Success] {match['full_name']} verified for {command.company_id}")
                        
                        # Construir Scopes y Permisos dinámicamente
                        is_sup = match.get("is_supervisor", False)
                        dept = match.get("department", "")
                        
                        coll_perms = ["PHYSICAL_SCAN"] # Permisos granulares de acción
                        coll_roles = ["collaborator"]
                        
                        if is_sup or dept == "Warehouse":
                            coll_perms.extend(["INVENTORY_READ", "INVENTORY_WRITE"])
                            coll_roles.append("warehouse_operator")
                        
                        # Load collaborator Permission slugs from DB (system role)
                        coll_scopes = await _load_role_slugs_by_name(self.db, "collaborator")
                        if not coll_scopes:
                            coll_scopes = ["inventory.stock.read", "inventory.document.create", "master_data.product.read", "master_data.price.read", "pos.checkout"]
                        
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
                self.logger.error(f"HR Fallback failed: {e}")
            
            raise UnauthorizedException(message="User not associated with this company")

        # HIDRATACIÓN DINÁMICA
        permissions = list(
            await self.permission_checker.get_user_permissions(command.user_id, command.company_id)
        )

        # 3. Generar Access Token final (15 min, typ: "access")
        scopes = _build_scopes(ucr.role_names, ucr.scopes, permissions)
        
        company_obj = await self.db.get(Company, command.company_id)
        company_timezone = company_obj.timezone if company_obj else "UTC"

        access_token = create_access_token(
            subject=str(command.user_id),
            company_id=str(command.company_id),
            data={
                "role_names": ucr.role_names,
                "permissions": permissions,
                "scopes": scopes,
                "modules": modules,
                "status": sub_status,
                "readonly": readonly,
                "correlation_id": correlation_id,
                "group_id": str(ucr.group_id) if ucr.group_id else None,
                "timezone": company_timezone,
            },
        )

        # 4. RTR: Crear familia de tokens (generación 0, stateless)
        import secrets
        from auth_app.infrastructure.repositories.sqlalchemy_refresh_token_repo import SQLAlchemyRefreshTokenRepository
        from auth_app.domain.handlers.refresh_token_handler import RefreshTokenHandler

        rtr_repo = SQLAlchemyRefreshTokenRepository(self.db)
        family = await rtr_repo.create_family(
            user_id=command.user_id,
            company_id=command.company_id,
            family_salt=secrets.token_hex(32),  # 64 hex chars únicos por sesión
        )
        rtr_handler = RefreshTokenHandler(rtr_repo, settings.SECRET_KEY)
        raw_refresh = rtr_handler._issue_refresh_token(family)

        async with self.db.begin_nested():
            # 5. Audit logging (Atomic with Transaction)
            await AuditService.log_action(
                db=self.db,
                user_id=command.user_id,
                action="SELECT_COMPANY",
                entity_name="CompanyAccess",
                entity_id=command.company_id,
                details=f"method: X-Selection-Token, rtr_family_id: {family.family_id}, correlation_id: {correlation_id}",
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

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "token_type": "bearer",
            "user_id": str(command.user_id),
            "company_id": str(command.company_id),
            "company_name": ucr.company_name or "Interno Core",
            "group_id": str(ucr.group_id) if ucr.group_id else None,
            "roles": ucr.role_names,
            "scopes": scopes,
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
            "timezone": company_timezone,
        }

    async def _generate_collaborator_response(
        self, command, real_collaborator_id, full_name, internal_id, is_supervisor, warehouse_id, department, 
        permissions, scopes, modules, sub_status, readonly, correlation_id
    ) -> dict:
        """Helper para generar el JWT y la respuesta final para un colaborador industrial."""
        company_obj = await self.db.get(Company, command.company_id)
        company_timezone = company_obj.timezone if company_obj else "UTC"
        company_name = company_obj.name if company_obj else "Interno Core"

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
                "role": "collaborator",
                "timezone": company_timezone,
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
            "timezone": company_timezone,
        }
