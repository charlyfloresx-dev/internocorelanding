"""
Excepciones de dominio para Refresh Token Rotation.

Todas heredan de DomainException (del backend/common).
"""
from common.exceptions import DomainException


class RefreshTokenExpiredError(DomainException):
    """Refresh token fuera de su lifetime (exp < now)."""
    pass


class RefreshTokenRevokedError(DomainException):
    """Token family fue revocada (breach detectado o logout)."""
    pass


class RefreshTokenReuseDetectedError(DomainException):
    """
    Brecha en generación detectada.

    Indica replay attack, breach, o concurrencia sin sincronización.
    ACCIÓN: Revocar familia entera.
    """
    pass


class CompanyIdMismatchError(DomainException):
    """
    company_id binding inválido (tampering o forging).

    Token reclama pertenecer a una empresa pero el HMAC no coincide.
    """
    pass


class RefreshTokenInvalidFamilyError(DomainException):
    """
    Token family no existe en DB o está corrupta.

    Posible: token es falso, family fue eliminada, datos inconsistentes.
    """
    pass


class RefreshTokenInvalidError(DomainException):
    """
    Token signature/format inválido o no decodificable.

    JWT malformado, firma inválida, encoding incorrecto.
    """
    pass


class RefreshTokenConcurrentRaceError(DomainException):
    """
    Concurrent request ganó optimistic lock.

    Ocurre cuando dos requests simultáneos intentan refrescar.
    El loser debe retry con backoff exponencial.
    """
    pass
