import uuid
from typing import List, Tuple, Optional

from auth_app.domain.repositories.user_repository import IUserRepository
from auth_app.core.security import verify_password
from auth_app.domain.entities.user_aggregate import UserEntity


class AuthService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    # ── USER QUERIES ──────────────────────────────────────────────────────────

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserEntity]:
        return await self.user_repo.get_by_id(user_id)

    async def authenticate_user(self, email: str, password: str) -> Optional[UserEntity]:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        if not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def authenticate_by_identity_token(self, token: str) -> Optional[UserEntity]:
        return await self.user_repo.get_by_identity_token(token)

    # ── COMPANY / PERMISSION QUERIES ──────────────────────────────────────────

    async def get_user_companies(self, user_id: uuid.UUID) -> List[dict]:
        ucr_entities = await self.user_repo.get_user_companies(user_id)
        
        # Mapa para dedup: {company_id: company_data}
        dedup_map = {}
        
        # Jerarquía de roles para la etiqueta (Admin > Manager > Collaborator)
        def get_priority(roles):
            if not roles: return 0
            lowered = [r.lower() for r in roles]
            if "admin" in lowered or "owner" in lowered: return 10
            if "manager" in lowered: return 5
            return 1

        for ucr in ucr_entities:
            c_id = ucr.company_id
            if c_id not in dedup_map:
                dedup_map[c_id] = {
                    "company_id": c_id,
                    "company_name": ucr.company_name,
                    "group_id": ucr.group_id,
                    "group_name": None,
                    "logo": ucr.logo,
                    "is_new": ucr.is_new,
                    "role_names": ucr.role_names,
                    "priority": get_priority(ucr.role_names)
                }
            else:
                # Si ya existe, comparar prioridad y combinar roles
                current = dedup_map[c_id]
                new_priority = get_priority(ucr.role_names)
                if new_priority > current["priority"]:
                    current["role_names"] = ucr.role_names
                    current["priority"] = new_priority
                
        # Limpiar y retornar lista
        result = []
        for c in dedup_map.values():
            c.pop("priority", None)
            result.append(c)
            
        return result

    async def get_user_context_for_company(
        self, user_id: uuid.UUID, company_id: uuid.UUID
    ) -> Tuple[List[str], List[str], Optional[uuid.UUID]]:
        """Gets (roles, scopes, group_id) for a user in a specific company."""
        return await self.user_repo.get_user_context_for_company(user_id, company_id)

    async def get_user_permissions_for_company(
        self, user_id: uuid.UUID, company_id: uuid.UUID
    ) -> List[str]:
        """
        Returns the current scopes/permissions for a user in a company.
        Used by POST /refresh to re-validate privileges during token rotation.
        """
        _roles, scopes, _ = await self.user_repo.get_user_context_for_company(user_id, company_id)
        return scopes

    async def get_user_roles_for_company(
        self, user_id: uuid.UUID, company_id: uuid.UUID
    ) -> List[str]:
        """
        Returns the current role names for a user in a company.
        Used by POST /refresh to re-validate privileges during token rotation.
        """
        roles, _scopes, _ = await self.user_repo.get_user_context_for_company(user_id, company_id)
        return roles

    # ── PASSWORD RESET ────────────────────────────────────────────────────────

    async def request_password_reset(self, email: str) -> bool:
        """
        Agnostic company reset. In production: generate OTP, store, send email.
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            return False
        # TODO: Generate OTP, store it, trigger email job
        return True

    async def confirm_password_reset(self, email: str, otp: str, new_password: str) -> bool:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return False
        # TODO: Validate OTP against stored value
        if otp != "123456":  # Hardcoded mock — replace with real OTP storage
            return False
        from auth_app.core.security import get_password_hash
        return await self.user_repo.update_user_password(
            user.id, get_password_hash(new_password)
        )
