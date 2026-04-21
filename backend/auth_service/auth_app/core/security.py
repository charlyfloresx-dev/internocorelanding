"""
security.py — Interno Core Auth Service
JWT creation, verification, and password hashing utilities.

Token Taxonomy (enforced via `typ` claim):
  - "selection"  → Short-lived, single-use, company-selection phase.
  - "access"     → Final JWT, 15 min, carries roles/scopes/company_id.
  - "refresh"    → Long-lived (30 days), persisted in DB, rotated on use.
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from auth_app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── PASSWORD UTILITIES ────────────────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Compatibility alias used by users.py and other modules.
hash_password = get_password_hash


# ── TOKEN HELPERS ─────────────────────────────────────────────────────────────

def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def hash_token(raw_token: str) -> str:
    """SHA-256 hex digest of a raw token (for safe DB storage)."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ── SELECTION TOKEN ───────────────────────────────────────────────────────────

def create_selection_token(subject: uuid.UUID) -> str:
    """
    Phase-1 token: issued after credential verification, before company selection.
    Carries `typ: "selection"` — rejected by all protected endpoints.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.SELECTION_TOKEN_EXPIRE_MINUTES
    )
    return _encode({
        "exp": expire,
        "sub": str(subject),
        "typ": "selection",
    })


# ── ACCESS TOKEN ──────────────────────────────────────────────────────────────

def create_final_access_token(
    subject: uuid.UUID,
    company_id: uuid.UUID,
    roles: List[str],
    scopes: List[str],
    group_id: Optional[uuid.UUID] = None,
    modules: List[str] = None,
    status: str = "TRIAL",
    readonly: bool = False,
    correlation_id: Optional[str] = None,
) -> str:
    """
    Phase-2 token: final JWT scoped to a specific company.
    Carries `typ: "access"`.
    Lifespan: ACCESS_TOKEN_EXPIRE_MINUTES (default 15 min).
    """
    if modules is None:
        modules = ["auth_core", "inventory_core"]

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return _encode({
        "exp": expire,
        "sub": str(subject),
        "typ": "access",
        "company_id": str(company_id),
        "group_id": str(group_id) if group_id else None,
        "role_names": roles,
        "scopes": scopes,
        "modules": modules,
        "status": status,
        "readonly": readonly,
        "correlation_id": correlation_id,
    })


def create_access_token(subject: str, company_id: str, data: dict) -> str:
    """
    Compatibility shim — wraps create_final_access_token with string inputs.
    Used by SelectCompanyCommandHandler and other legacy callers.
    """
    return create_final_access_token(
        subject=uuid.UUID(subject),
        company_id=uuid.UUID(company_id),
        roles=data.get("role_names", []),
        scopes=data.get("scopes", []),
        group_id=uuid.UUID(str(data["group_id"])) if data.get("group_id") else None,
        modules=data.get("modules"),
        status=data.get("status", "TRIAL"),
        readonly=data.get("readonly", False),
        correlation_id=data.get("correlation_id"),
    )


# ── REFRESH TOKEN ─────────────────────────────────────────────────────────────

def create_refresh_token(subject: uuid.UUID, company_id: uuid.UUID) -> str:
    """
    Refresh token scoped to a specific company.
    Carries `typ: "refresh"` — rejected by all protected endpoints.
    Lifespan: REFRESH_TOKEN_EXPIRE_MINUTES (default 30 days).

    The raw token string must be stored as hash_token(raw) in the DB.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    return _encode({
        "exp": expire,
        "sub": str(subject),
        "typ": "refresh",
        "company_id": str(company_id),
        # jti (JWT ID) makes every token unique even for the same user/company.
        "jti": str(uuid.uuid4()),
    })


# ── DECODE / VALIDATE ─────────────────────────────────────────────────────────

def decode_token(token: str, expected_typ: Optional[str] = None) -> Optional[dict]:
    """
    Decode and verify a JWT.

    Args:
        token: Raw JWT string.
        expected_typ: If provided, raises ValueError if `typ` claim does not match.
                      Pass "access" for protected endpoints, "refresh" for /refresh.
    Returns:
        Decoded payload dict, or None if the token is invalid / expired.
    Raises:
        ValueError: If `expected_typ` is set but the token's `typ` claim does not match.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if expected_typ and payload.get("typ") != expected_typ:
            raise ValueError(
                f"Invalid token type. Expected '{expected_typ}', "
                f"got '{payload.get('typ')}'."
            )
        return payload
    except JWTError:
        return None


# ── GOD MODE (Break-Glass) ────────────────────────────────────────────────────

def create_admin_god_token(
    subject: uuid.UUID,
    correlation_id: Optional[str] = None,
) -> str:
    """
    Technical Rescue Token (God Mode).
    Carries bypass_tenant=True. Hard-coded 30-min life.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    return _encode({
        "exp": expire,
        "sub": str(subject),
        "typ": "access",          # passes the typ guard on protected endpoints
        "bypass_tenant": True,
        "role_names": ["GOD_MODE_ADMIN"],
        "scopes": ["*"],
        "modules": ["*"],
        "status": "ADMIN",
        "correlation_id": correlation_id,
    })
