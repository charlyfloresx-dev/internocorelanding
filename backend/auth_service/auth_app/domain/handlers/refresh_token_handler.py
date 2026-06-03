"""
Refresh Token Rotation Handler — CQRS Pattern.

Orquesta rotación de token con 8 fases de mitigación de race conditions.

FASES:
1. Decodificar token (sin DB)
2. Obtener familia de DB
3. Validar binding criptográfico de company_id
4. Validar que NO esté revocada
5. Idempotency check (RDS failover resilience)
6. Reuse detection (generation gap)
7. Atomic rotation (optimistic locking)
8. Issue token pair + audit
"""
import jwt
import secrets
import logging
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from typing import Optional

from auth_app.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from auth_app.domain.value_objects.token_family import RefreshTokenPayload, TokenFamily
from auth_app.domain.exceptions.refresh_token_exceptions import (
    RefreshTokenExpiredError,
    RefreshTokenRevokedError,
    RefreshTokenReuseDetectedError,
    CompanyIdMismatchError,
    RefreshTokenInvalidFamilyError,
    RefreshTokenInvalidError,
    RefreshTokenConcurrentRaceError
)
from auth_app.infrastructure.clients.notification_client import NotificationClient
from common.exceptions import OptimisticLockError
from auth_app.core.config import settings

logger = logging.getLogger(__name__)


class RefreshTokenCommand:
    """CQRS Command: solicitud de rotación."""
    def __init__(
        self,
        refresh_token: str,
        ip_address: str,
        user_agent: str
    ):
        self.refresh_token = refresh_token
        self.ip_address = ip_address
        self.user_agent = user_agent


class RefreshTokenResponse:
    """Response DTO."""
    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        expires_in: int = 3600
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in
        self.token_type = "Bearer"


class RefreshTokenHandler:
    """
    Orquesta rotación de token con 8 fases.

    INVARIANTES:
    - company_id NUNCA viene del cliente (extraído del HMAC)
    - generation gap → familia revocada (breach)
    - Concurrent requests → loser retorna tokens del ganador (grace)
    - RDS failover → idempotencia dentro de 2 segundos
    """

    def __init__(
        self,
        token_repo: IRefreshTokenRepository,
        secret_key: str,
        access_token_ttl_minutes: int = 720
    ):
        self.token_repo = token_repo
        self.secret_key = secret_key
        self.access_token_ttl_minutes = access_token_ttl_minutes

    async def execute(self, cmd: RefreshTokenCommand) -> RefreshTokenResponse:
        """
        Ejecutar rotación con todas las mitigaciones.

        Retorna: RefreshTokenResponse (access + refresh tokens)
        Lanza: RefreshTokenExpiredError, RefreshTokenRevokedError, etc.
        """

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FASE 1: Decodificar token (sin DB aún)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        try:
            payload = jwt.decode(cmd.refresh_token, self.secret_key, algorithms=["HS256"])
            token_payload = RefreshTokenPayload.from_jwt_payload(payload)
        except jwt.ExpiredSignatureError:
            raise RefreshTokenExpiredError("Refresh token lifetime exceeded")
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError) as e:
            raise RefreshTokenInvalidError(f"Token inválido: {str(e)}")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FASE 2: Obtener familia de DB (con tenant validation)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        family = await self.token_repo.get_family(token_payload.family_id, token_payload.company_id)
        if not family:
            raise RefreshTokenInvalidFamilyError("Token family not found")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FASE 3: Validar binding criptográfico de company_id
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        if not token_payload.validate_company_binding(self.secret_key, family.family_salt):
            raise CompanyIdMismatchError("Company binding signature invalid")

        if family.company_id != token_payload.company_id:
            raise CompanyIdMismatchError("Token company_id ≠ family company_id")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FASE 4: Validar que NO esté revocada
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        if not family.is_active():
            await self.token_repo.log_rotation_event(
                family_id=family.family_id,
                user_id=family.user_id,
                company_id=family.company_id,
                action="REFRESH_AFTER_REVOCATION",
                old_generation=None,
                new_generation=None,
                ip_address=cmd.ip_address,
                user_agent=cmd.user_agent
            )
            raise RefreshTokenRevokedError(
                f"Token family revoked: {family.revocation_reason}"
            )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FASE 5: Idempotency check (RDS failover resilience)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        now = datetime.now(timezone.utc)

        if (family.last_refresh_jti == token_payload.jti and
            now < family.refresh_window_expires_at):

            await self.token_repo.log_rotation_event(
                family_id=family.family_id,
                user_id=family.user_id,
                company_id=family.company_id,
                action="IDEMPOTENT_RETRY_DETECTED",
                old_generation=family.current_generation,
                new_generation=family.current_generation,
                ip_address=cmd.ip_address,
                user_agent=cmd.user_agent,
                failover_detected=True
            )

            return await self._return_cached_tokens(family)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FASE 6: Reuse detection (generation gap)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        if token_payload.generation < family.current_generation - 1:
            # Brecha detectada → breach
            await self._revoke_family_for_breach(
                family,
                reason="REUSE_DETECTED",
                detail=f"Token gen {token_payload.generation} < current {family.current_generation} - 1",
                ip_address=cmd.ip_address
            )
            raise RefreshTokenReuseDetectedError(
                "Token generation gap detected—family revoked"
            )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FASE 7: Atomic rotation (optimistic locking)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        next_generation = family.current_generation + 1
        old_version = family.version_id

        try:
            updated_family = await self.token_repo.rotate_family_atomically(
                family_id=family.family_id,
                company_id=token_payload.company_id,
                next_generation=next_generation,
                expected_version=old_version,
                last_refresh_jti=token_payload.jti,
                refresh_window_expires_at=now + timedelta(seconds=2)
            )
        except OptimisticLockError:
            # Otro request ganó la race → fetch estado actual
            current_family = await self.token_repo.get_family(family.family_id, token_payload.company_id)

            if current_family and current_family.current_generation > family.current_generation:
                # El ganador está adelante → grace: retornar sus tokens
                await self.token_repo.log_rotation_event(
                    family_id=family.family_id,
                    user_id=family.user_id,
                    company_id=family.company_id,
                    action="CONCURRENT_REFRESH_GRACEFUL",
                    old_generation=family.current_generation,
                    new_generation=current_family.current_generation,
                    ip_address=cmd.ip_address,
                    user_agent=cmd.user_agent,
                    concurrent_attempt_detected=True
                )
                return await self._return_cached_tokens(current_family)

            # Retry (client: exponential backoff)
            raise RefreshTokenConcurrentRaceError(
                "Concurrent refresh race—retry with exponential backoff"
            )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FASE 8: Issue token pair + audit
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        new_refresh_token = self._issue_refresh_token(updated_family)
        new_access_token = self._issue_access_token(
            updated_family.user_id,
            updated_family.company_id
        )

        await self.token_repo.log_rotation_event(
            family_id=updated_family.family_id,
            user_id=updated_family.user_id,
            company_id=updated_family.company_id,
            action="ROTATED",
            old_generation=family.current_generation,
            new_generation=updated_family.current_generation,
            ip_address=cmd.ip_address,
            user_agent=cmd.user_agent
        )

        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=3600
        )

    # ────────────────────────────────────────────────────────────────────────
    # Private Helpers
    # ────────────────────────────────────────────────────────────────────────

    async def _return_cached_tokens(self, family: TokenFamily) -> RefreshTokenResponse:
        """Retornar tokens en cache (idempotencia failover)."""
        refresh_token = self._issue_refresh_token(family)
        access_token = self._issue_access_token(family.user_id, family.company_id)
        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600
        )

    async def _revoke_family_for_breach(
        self,
        family: TokenFamily,
        reason: str,
        detail: str,
        ip_address: str
    ) -> None:
        """
        Revocar familia por breach detectado.

        Atomic revocation + fire-and-forget alert. Alert failures never block revocation.
        """
        await self.token_repo.revoke_family(family.family_id, family.company_id, reason)

        await self.token_repo.log_rotation_event(
            family_id=family.family_id,
            user_id=family.user_id,
            company_id=family.company_id,
            action="REUSE_DETECTED",
            old_generation=family.current_generation,
            new_generation=None,
            ip_address=ip_address,
            user_agent=None
        )

        # Send security breach alert (best-effort, never blocks revocation)
        try:
            notification_client = NotificationClient()
            await notification_client.send_breach_alert(
                company_id=family.company_id,
                user_id=family.user_id,
                reason=reason,
                ip_address=ip_address,
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(
                f"Failed to send RTR breach alert (continuing anyway): {type(e).__name__}: {e}",
                exc_info=False
            )

    def _issue_refresh_token(self, family: TokenFamily) -> str:
        """Emitir JWT refresh con binding criptográfico."""
        now = datetime.now(timezone.utc)
        family_hash = family.compute_family_hash(self.secret_key)

        payload = {
            "jti": str(uuid4()),
            "sub": str(family.user_id),
            "fam": str(family.family_id),
            "gen": family.current_generation,
            "co": str(family.company_id),
            "fam_hash": family_hash,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=30)).timestamp()),
            "typ": "refresh"
        }

        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def _issue_access_token(self, user_id: UUID, company_id: UUID) -> str:
        """Emitir JWT access (standard)."""
        now = datetime.now(timezone.utc)

        # TODO: Obtener roles/scopes del usuario desde DB
        payload = {
            "sub": str(user_id),
            "company_id": str(company_id),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self.access_token_ttl_minutes)).timestamp()),
            "typ": "access"
        }

        return jwt.encode(payload, self.secret_key, algorithm="HS256")
