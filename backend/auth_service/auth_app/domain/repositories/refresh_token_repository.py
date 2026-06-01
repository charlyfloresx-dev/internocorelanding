"""
Repository Interface para Refresh Token Families.

Define contrato para persistencia stateless sin implementación concreta.
"""
from abc import ABC, abstractmethod
from uuid import UUID
from datetime import datetime
from typing import Optional

from auth_app.domain.value_objects.token_family import TokenFamily
from auth_app.models.refresh_token_family import RefreshTokenRotationAudit


class IRefreshTokenRepository(ABC):
    """
    Contrato de persistencia para token families.

    INVARIANTES:
    - get_family() retorna TokenFamily (value object) o None
    - create_family() retorna nueva familia con generation=0, version_id=1
    - rotate_family_atomically() usa optimistic locking (version_id)
      Si esperado version_id ≠ actual → OptimisticLockError
    - revoke_family() es idempotente (puede ser llamada múltiples veces)
    - log_rotation_event() es append-only (nunca UPDATE/DELETE)
    """

    @abstractmethod
    async def get_family(self, family_id: UUID, company_id: UUID) -> Optional[TokenFamily]:
        """
        Obtener familia por ID con tenant validation.

        CRÍTICO: company_id DEBE ser incluido en WHERE clause para IDOR prevention.

        Args:
            family_id: UUID de la familia
            company_id: UUID de la empresa (del JWT verificado, nunca del cliente)

        Returns:
            TokenFamily si existe Y pertenece a company_id, None en caso contrario
        """
        pass

    @abstractmethod
    async def create_family(
        self,
        user_id: UUID,
        company_id: UUID,
        family_salt: str
    ) -> TokenFamily:
        """
        Crear nueva familia (típicamente al login).

        Args:
            user_id: UUID del usuario
            company_id: UUID de la empresa
            family_salt: 64-char hex (32 bytes), único

        Returns:
            TokenFamily con generation=0, version_id=1 (inicializado por SQLAlchemy)

        Raises:
            IntegrityError si family_salt ya existe (unique constraint)
        """
        pass

    @abstractmethod
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
        Rotar familia atomically con optimistic locking y tenant validation.

        CRÍTICO: company_id DEBE ser incluido en WHERE clause para IDOR prevention.

        El caller debe:
        1. Fetch familia con version_id = X
        2. Llamar rotate_family_atomically(..., company_id=..., expected_version=X, next_generation=X+1)
        3. Si OptimisticLockError: otro request ganó; retry o retornar sus tokens

        Args:
            family_id: UUID de la familia
            company_id: UUID de la empresa (validación multi-tenant)
            next_generation: Nueva generación (current_generation + 1)
            expected_version: version_id esperado (para optimistic lock)
            last_refresh_jti: JTI del nuevo token (para idempotencia)
            refresh_window_expires_at: Ventana idempotencia expires

        Returns:
            TokenFamily actualizada con nueva generation (version_id incrementado automáticamente)

        Raises:
            OptimisticLockError si version_id ≠ expected_version
            RefreshTokenInvalidFamilyError si family no existe o company_id no coincide
        """
        pass

    @abstractmethod
    async def revoke_family(
        self,
        family_id: UUID,
        company_id: UUID,
        reason: str
    ) -> None:
        """
        Revocar familia entera con tenant validation (breach detectado).

        IDEMPOTENTE: puede ser llamada varias veces sin error.

        CRÍTICO: company_id DEBE ser incluido en WHERE clause para IDOR prevention.

        Args:
            family_id: UUID de la familia
            company_id: UUID de la empresa (validación multi-tenant)
            reason: Razón de revocación ('REUSE_DETECTED', 'USER_LOGOUT', etc.)
        """
        pass

    @abstractmethod
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
        """
        Log audit event (append-only).

        Args:
            family_id: UUID de la familia
            user_id: UUID del usuario
            company_id: UUID de la empresa
            action: 'CREATED' | 'ROTATED' | 'REUSE_DETECTED' | 'REVOKED' | ...
            old_generation: Generación anterior (None si N/A)
            new_generation: Nueva generación (None si N/A)
            ip_address: IP del cliente (para investigación)
            user_agent: User-Agent (para investigación)
            concurrent_attempt_detected: True si race condition detected
            failover_detected: True si RDS failover idempotencia

        Returns:
            RefreshTokenRotationAudit record creado
        """
        pass
