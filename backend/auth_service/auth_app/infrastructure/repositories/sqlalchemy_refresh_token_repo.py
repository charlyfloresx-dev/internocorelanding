"""
SQLAlchemy Implementation de Refresh Token Repository.

Stateless, sin Redis. Usa optimistic locking nativo de SQLAlchemy.
"""
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as ORMSession

from auth_app.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from auth_app.domain.value_objects.token_family import TokenFamily
from auth_app.models.refresh_token_family import RefreshTokenFamily, RefreshTokenRotationAudit
from auth_app.domain.exceptions.refresh_token_exceptions import RefreshTokenInvalidFamilyError
from common.exceptions import OptimisticLockError


class SQLAlchemyRefreshTokenRepository(IRefreshTokenRepository):
    """
    Implementación stateless con PostgreSQL + optimistic locking.

    Usa SQLAlchemy native optimistic locking (version_id_col) para gestionar
    concurrencia automáticamente. No usa version_counter manual.

    ATOMICITY:
    - rotate_family_atomically() usa SELECT ... FOR UPDATE + version check
    - revoke_family() usa nested transaction para rollback aislado
    - log_rotation_event() es INSERT append-only (nunca falla en duplicado)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_family(self, family_id: UUID, company_id: UUID) -> Optional[TokenFamily]:
        """Obtener familia por ID con tenant validation."""
        stmt = select(RefreshTokenFamily).where(
            (RefreshTokenFamily.id == family_id) &
            (RefreshTokenFamily.company_id == company_id)
        )
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
        now = datetime.now(timezone.utc)
        model = RefreshTokenFamily(
            id=uuid4(),
            company_id=company_id,
            tenant_id=company_id,  # MultiTenantBase requiere tenant_id NOT NULL
            user_id=user_id,
            family_salt=family_salt,
            current_generation=0,
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
        company_id: UUID,
        next_generation: int,
        expected_version: int,
        last_refresh_jti: UUID,
        refresh_window_expires_at: datetime
    ) -> TokenFamily:
        """
        Rotar family atomically con optimistic locking y tenant validation.

        FLUJO:
        1. SELECT ... FOR UPDATE (serializa contra otros rotates)
        2. Validar company_id pertenece a tenant
        3. Validar version_id == expected_version
        4. Si no → OptimisticLockError
        5. Si sí → actualizar atomically en nested transaction
        """
        # Usar begin_nested() para atomicity + rollback aislado
        async with self.db.begin_nested():
            # SELECT ... FOR UPDATE: lock pessimista en row
            stmt = select(RefreshTokenFamily).where(
                (RefreshTokenFamily.id == family_id) &
                (RefreshTokenFamily.company_id == company_id)
            ).with_for_update()

            result = await self.db.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                raise RefreshTokenInvalidFamilyError("Family not found for update")

            # Optimistic lock check usando version_id nativo
            if model.version_id != expected_version:
                raise OptimisticLockError(
                    f"Version mismatch: expected {expected_version}, got {model.version_id}"
                )

            # Actualizar atomically - SQLAlchemy incrementará version_id automáticamente
            model.current_generation = next_generation
            from datetime import timezone
            model.last_refresh_at = datetime.now(timezone.utc)
            model.last_refresh_jti = last_refresh_jti
            model.refresh_window_expires_at = refresh_window_expires_at

            self.db.add(model)
            await self.db.flush()
            # Refresh eagerly para recargar columnas server-generated (updated_at, version_id)
            # y evitar MissingGreenlet al acceder a atributos en _model_to_value_object
            await self.db.refresh(model)

        return self._model_to_value_object(model)

    async def revoke_family(
        self,
        family_id: UUID,
        company_id: UUID,
        reason: str
    ) -> None:
        """Revocar familia entera con tenant validation."""
        async with self.db.begin_nested():
            stmt = select(RefreshTokenFamily).where(
                (RefreshTokenFamily.id == family_id) &
                (RefreshTokenFamily.company_id == company_id)
            ).with_for_update()

            result = await self.db.execute(stmt)
            model = result.scalar_one_or_none()

            if model and model.revoked_at is None:
                from datetime import timezone
                model.revoked_at = datetime.now(timezone.utc)
                model.revocation_reason = reason
                self.db.add(model)
                await self.db.flush()
                await self.db.refresh(model)

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
            tenant_id=company_id,
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
            version_id=model.version_id,
            revoked_at=model.revoked_at,
            revocation_reason=model.revocation_reason,
            last_refresh_at=model.last_refresh_at,
            last_refresh_jti=model.last_refresh_jti,
            refresh_window_expires_at=model.refresh_window_expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
