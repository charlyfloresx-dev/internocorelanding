"""
SQLAlchemy Implementation de Refresh Token Repository.

Stateless, sin Redis. Usa optimistic locking + atomicity en DB.
"""
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as ORMSession

from auth_app.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from auth_app.domain.value_objects.token_family import TokenFamily
from auth_app.models.refresh_token_family import RefreshTokenFamily, RefreshTokenRotationAudit
from auth_app.domain.exceptions.refresh_token_exceptions import RefreshTokenInvalidFamilyError
from common.infrastructure.exceptions import OptimisticLockError


class SQLAlchemyRefreshTokenRepository(IRefreshTokenRepository):
    """
    Implementación stateless con PostgreSQL + optimistic locking.

    ATOMICITY:
    - rotate_family_atomically() usa SELECT ... FOR UPDATE + version check
    - revoke_family() usa nested transaction para rollback aislado
    - log_rotation_event() es INSERT append-only (nunca falla en duplicado)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_family(self, family_id: UUID) -> Optional[TokenFamily]:
        """Obtener familia por ID (sin lock)."""
        stmt = select(RefreshTokenFamily).where(RefreshTokenFamily.id == family_id)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_value_object(model)

    async def create_family(
        self,
        user_id: UUID,
        company_id: UUID,
        family_salt: str
    ) -> TokenFamily:
        """Crear nueva familia (al login)."""
        now = datetime.utcnow()
        model = RefreshTokenFamily(
            id=uuid4(),
            company_id=company_id,
            user_id=user_id,
            family_salt=family_salt,
            current_generation=0,
            version_counter=0,
            revoked_at=None,
            last_refresh_at=now,
            refresh_window_expires_at=now
        )
        self.db.add(model)
        await self.db.flush()
        return self._model_to_value_object(model)

    async def rotate_family_atomically(
        self,
        family_id: UUID,
        next_generation: int,
        expected_version: int,
        last_refresh_jti: UUID,
        refresh_window_expires_at: datetime
    ) -> TokenFamily:
        """
        Rotar family atomically con optimistic locking.

        FLUJO:
        1. SELECT ... FOR UPDATE (serializa contra otros rotates)
        2. Validar version_counter == expected_version
        3. Si no → OptimisticLockError
        4. Si sí → actualizar atomically en nested transaction
        """
        # Usar begin_nested() para atomicity + rollback aislado
        async with self.db.begin_nested():
            # SELECT ... FOR UPDATE: lock pessimista en row
            stmt = select(RefreshTokenFamily).where(
                RefreshTokenFamily.id == family_id
            ).with_for_update()

            result = await self.db.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                raise RefreshTokenInvalidFamilyError("Family not found for update")

            # Optimistic lock check
            if model.version_counter != expected_version:
                raise OptimisticLockError(
                    f"Version mismatch: expected {expected_version}, got {model.version_counter}"
                )

            # Actualizar atomically
            model.current_generation = next_generation
            model.version_counter += 1
            model.last_refresh_at = datetime.utcnow()
            model.last_refresh_jti = last_refresh_jti
            model.refresh_window_expires_at = refresh_window_expires_at

            self.db.add(model)
            await self.db.flush()

        return self._model_to_value_object(model)

    async def revoke_family(
        self,
        family_id: UUID,
        reason: str
    ) -> None:
        """Revocar familia entera."""
        async with self.db.begin_nested():
            stmt = select(RefreshTokenFamily).where(
                RefreshTokenFamily.id == family_id
            ).with_for_update()

            result = await self.db.execute(stmt)
            model = result.scalar_one_or_none()

            if model and model.revoked_at is None:
                model.revoked_at = datetime.utcnow()
                model.revocation_reason = reason
                self.db.add(model)
                await self.db.flush()

    async def log_rotation_event(
        self,
        family_id: UUID,
        user_id: UUID,
        company_id: UUID,
        action: str,
        old_generation: Optional[int],
        new_generation: Optional[int],
        ip_address: Optional[str],
        user_agent: Optional[str],
        concurrent_attempt_detected: bool = False,
        failover_detected: bool = False
    ) -> RefreshTokenRotationAudit:
        """Log audit (append-only)."""
        audit = RefreshTokenRotationAudit(
            id=uuid4(),
            family_id=family_id,
            user_id=user_id,
            company_id=company_id,
            action=action,
            old_generation=old_generation,
            new_generation=new_generation,
            ip_address=ip_address,
            user_agent=user_agent,
            concurrent_attempt_detected=concurrent_attempt_detected,
            failover_detected=failover_detected
        )
        self.db.add(audit)
        await self.db.flush()
        return audit

    @staticmethod
    def _model_to_value_object(model: RefreshTokenFamily) -> TokenFamily:
        """Convertir ORM model a value object."""
        return TokenFamily(
            family_id=model.id,
            company_id=model.company_id,
            user_id=model.user_id,
            family_salt=model.family_salt,
            current_generation=model.current_generation,
            version_counter=model.version_counter,
            revoked_at=model.revoked_at,
            revocation_reason=model.revocation_reason,
            last_refresh_at=model.last_refresh_at,
            last_refresh_jti=model.last_refresh_jti,
            refresh_window_expires_at=model.refresh_window_expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
