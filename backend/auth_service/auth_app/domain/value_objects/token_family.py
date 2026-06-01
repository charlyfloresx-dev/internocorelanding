"""
Value Objects para Refresh Token Rotation Stateless.

Implementa:
- TokenFamily: Inmutable token family con binding criptográfico
- RefreshTokenPayload: Payload decodificado del JWT refresh token
"""
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import hmac
import hashlib
import re


@dataclass(frozen=True)
class TokenFamily:
    """
    Inmutable token family con binding criptográfico de company_id.

    INVARIANTES:
    - family_id: UUID único de la familia
    - company_id: Sellado criptográficamente (HMAC-SHA256)
    - generation: Incrementa con cada refresh exitoso
    - version_id: Used for optimistic locking (hereda de BaseDomainEntity)
    - revoked_at: NULL = activa, NOT NULL = revocada (breach)
    """
    family_id: UUID
    company_id: UUID
    user_id: UUID
    family_salt: str                            # 32 bytes hex (64 chars)
    current_generation: int
    version_id: int                             # Optimistic locking (hereda de ORM)
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    last_refresh_at: Optional[datetime] = None
    last_refresh_jti: Optional[UUID] = None
    refresh_window_expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validar family_salt es exactamente 64 caracteres hexadecimales."""
        if not re.fullmatch(r'^[0-9a-f]{64}$', self.family_salt):
            raise ValueError(
                f"family_salt must be exactly 64 hexadecimal characters (32 bytes). "
                f"Got: {len(self.family_salt)} chars, valid_hex={bool(re.fullmatch(r'^[0-9a-f]*$', self.family_salt))}"
            )

    def is_active(self) -> bool:
        """Retorna True si la familia NO está revocada."""
        return self.revoked_at is None

    def compute_family_hash(self, secret_key: str) -> str:
        """
        Compute HMAC-SHA256 para sellar company_id criptográficamente.

        Previene:
        - Tampering de company_id en tránsito
        - Forging de tokens para otra empresa

        Args:
            secret_key: CORE_SECRET_KEY del servidor

        Returns:
            Hex digest de HMAC-SHA256
        """
        message = f"{self.family_id}||{self.company_id}||{self.user_id}||{self.family_salt}"
        return hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()


@dataclass(frozen=True)
class RefreshTokenPayload:
    """
    Payload extraído y decodificado del JWT refresh token.

    Representa el contrato entre el token emitido y lo que el servidor espera.
    """
    jti: UUID                                   # JWT ID único por token
    family_id: UUID
    company_id: UUID
    user_id: UUID
    generation: int                             # Generación en momento de emisión
    issued_at: datetime
    expires_at: datetime
    family_hash: str                            # HMAC binding de company_id

    @classmethod
    def from_jwt_payload(cls, payload: dict) -> "RefreshTokenPayload":
        """
        Factory: mapea claves JWT cortas a los campos del VO.

        JWT usa claves compactas (fam, co, gen, fam_hash) para reducir tamaño del token.
        Este método normaliza al contrato del dominio.
        """
        return cls(
            jti=UUID(payload["jti"]),
            family_id=UUID(payload["fam"]),
            company_id=UUID(payload["co"]),
            user_id=UUID(payload["sub"]),
            generation=int(payload["gen"]),
            issued_at=datetime.fromtimestamp(payload["iat"]),
            expires_at=datetime.fromtimestamp(payload["exp"]),
            family_hash=payload["fam_hash"],
        )

    def validate_company_binding(
        self,
        secret_key: str,
        family_salt: str
    ) -> bool:
        """
        Validar que company_id no fue adulterado en tránsito.

        CRÍTICO: company_id NUNCA viene del cliente (header/path param).
        Solo se extrae criptográficamente de este hash.

        Args:
            secret_key: CORE_SECRET_KEY
            family_salt: Salt de la familia (obtenido del DB)

        Returns:
            True si el hash es válido (company_id no fue modificado)
        """
        expected_hash = hmac.new(
            secret_key.encode(),
            f"{self.family_id}||{self.company_id}||{self.user_id}||{family_salt}".encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(self.family_hash, expected_hash)
