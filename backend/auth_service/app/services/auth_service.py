import uuid
from typing import List, Tuple, Optional

from app.domain.repositories.user_repository import IUserRepository
from app.core.security import verify_password
from app.domain.entities.user_aggregate import UserEntity

class AuthService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

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

    async def get_user_companies(self, user_id: uuid.UUID) -> List[dict]:
        ucr_entities = await self.user_repo.get_user_companies(user_id)
        
        companies = []
        for ucr in ucr_entities:
            companies.append({
                "company_id": ucr.company_id,
                "company_name": ucr.company_name,
                "group_id": ucr.group_id,
                "group_name": None, # Esto requeriría otro join, pero como estaba mockeado en la v anterior, lo dejamos None por ahora o lo pasamos si existe
                "logo": ucr.logo,
                "is_new": ucr.is_new,
                "role_names": ucr.role_names
            })
        return companies

    async def get_user_context_for_company(
        self, user_id: uuid.UUID, company_id: uuid.UUID
    ) -> Tuple[List[str], List[str], Optional[uuid.UUID]]:
        """
        Obtiene los roles y scopes de un usuario para una compañía específica, así como el group_id de la compañía.
        """
        return await self.user_repo.get_user_context_for_company(user_id, company_id)

    async def request_password_reset(self, email: str) -> bool:
        """
        Global password reset request (agnostic to company).
        In a real scenario, this would generate an OTP, save it securely, and send an email.
        For now, we just mock the successful generation.
        """
        user = await self.user_repo.get_by_email(email)
        
        if not user:
            return False

        # TODO: Generate OTP, store it in memory/redis/db, and trigger email job
        # For demonstration purposes: we pretend OTP is "123456" for any reset
        return True

    async def confirm_password_reset(self, email: str, otp: str, new_password: str) -> bool:
        """
        Validates OTP and resets password.
        """
        user = await self.user_repo.get_by_email(email)

        if not user:
            return False
            
        # TODO: Validate OTP against stored value
        if otp != "123456": # Hardcoded mock
            return False

        from app.core.security import get_password_hash
        return await self.user_repo.update_user_password(user.id, get_password_hash(new_password))