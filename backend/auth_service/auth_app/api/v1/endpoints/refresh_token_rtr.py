"""
Refresh Token Rotation Endpoint — FastAPI Router.

POST /api/v1/auth/refresh — Stateless RTR con mitigación de race conditions.

Rate Limiting:
  Per-User: 10/minute (prevents single attacker monopolizing quota)
  Global: 20/minute (prevents service-level DDoS)
"""
import jwt
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from auth_app.domain.handlers.refresh_token_handler import (
    RefreshTokenHandler,
    RefreshTokenCommand,
    RefreshTokenResponse
)
from auth_app.domain.exceptions.refresh_token_exceptions import (
    RefreshTokenExpiredError,
    RefreshTokenRevokedError,
    RefreshTokenReuseDetectedError,
    CompanyIdMismatchError,
    RefreshTokenInvalidFamilyError,
    RefreshTokenInvalidError,
    RefreshTokenConcurrentRaceError
)
from auth_app.infrastructure.repositories.sqlalchemy_refresh_token_repo import (
    SQLAlchemyRefreshTokenRepository
)
from auth_app.core.config import settings
from auth_app.dependencies import get_db
from common.responses import ApiResponse
from common.security.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_user_rate_limit_key(request: Request) -> str:
    """
    Extract user ID from refresh_token JWT for per-user rate limiting.

    If JWT is not decodable (malformed), falls back to IP address.

    This key is used to rate-limit per-user at 10/minute, preventing a single
    attacker from monopolizing the quota and affecting legitimate users.

    Args:
        request: FastAPI request object

    Returns:
        rate limit key: "user:<user_id>" or "ip:<client_ip>"
    """
    try:
        # Try to extract body from scope (stored by middleware during request)
        raw_body = request.scope.get("_body")
        if not raw_body:
            # Fallback to IP if body not available
            client_ip = request.client.host if request.client else "0.0.0.0"
            return f"ip:{client_ip}"

        import json
        body = json.loads(raw_body)
        token_str = body.get("refresh_token", "")

        if not token_str:
            client_ip = request.client.host if request.client else "0.0.0.0"
            return f"ip:{client_ip}"

        # Decode without verification (just to extract sub claim)
        # Signature will be verified later in the handler
        payload = jwt.decode(
            token_str,
            options={"verify_signature": False}
        )

        user_id = payload.get("sub")
        if user_id:
            return f"user:{user_id}"

    except Exception as e:
        logger.debug(f"Failed to extract user_id from token for rate limiting: {e}")

    # Fallback to IP address if JWT extraction fails
    client_ip = request.client.host if request.client else "0.0.0.0"
    return f"ip:{client_ip}"


class RefreshTokenRequest(BaseModel):
    """Request body."""
    refresh_token: str


class RefreshTokenResponseDto(BaseModel):
    """Response DTO."""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str


@router.post(
    "/refresh",
    response_model=ApiResponse[RefreshTokenResponseDto],
    summary="Rotar refresh token — Stateless RTR con race condition mitigation"
)
@limiter.limit("10/minute", key_func=get_user_rate_limit_key)  # Per-user limit
@limiter.limit("20/minute")  # Global fallback limit
async def refresh_token_rtr(
    request_body: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    POST /api/v1/auth/refresh

    Refresh Token Rotation Stateless — 8 Fases:

    **FASES:**
    1. Decodificar token JWT (sin DB)
    2. Obtener familia de DB
    3. Validar company_id binding criptográfico (HMAC)
    4. Validar que NO esté revocada
    5. Idempotency check (failover RDS resilience)
    6. Reuse detection (generation gap → breach)
    7. Atomic rotation (optimistic locking)
    8. Issue new token pair + audit

    **INVARIANTES:**
    - company_id NUNCA viene del cliente (cryptographically sealed)
    - Generation gap → entire family revoked (breach detected)
    - Concurrent requests → loser gracefully returns winner's tokens
    - RDS failover → 2-second idempotency window

    **STATUS CODES:**
    - 200: Tokens emitted successfully
    - 400: Token format invalid, tampering detected
    - 401: Token expired, revoked, or security lockout
    - 429: Rate limit exceeded

    **ERRORS (401 Unauthorized):**
    - RefreshTokenExpiredError: exp < now
    - RefreshTokenRevokedError: family revoked (breach or logout)
    - RefreshTokenReuseDetectedError: generation gap (security lockout)
    - CompanyIdMismatchError: HMAC validation failed (tampering)
    - RefreshTokenInvalidFamilyError: family not found

    **ERRORS (400 Bad Request):**
    - RefreshTokenInvalidError: malformed JWT
    """

    refresh_token_str = request_body.refresh_token
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token field required"
        )

    try:
        # Setup
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(
            token_repo=repo,
            secret_key=settings.CORE_SECRET_KEY,
            access_token_ttl_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        # Execute command
        cmd = RefreshTokenCommand(
            refresh_token=refresh_token_str,
            ip_address=request.client.host if request.client else "0.0.0.0",
            user_agent=request.headers.get("User-Agent", "")
        )

        response = await handler.execute(cmd)
        await db.commit()

        return ApiResponse(
            status="success",
            data=RefreshTokenResponseDto(
                access_token=response.access_token,
                refresh_token=response.refresh_token,
                expires_in=response.expires_in,
                token_type=response.token_type
            ),
            message="Refresh token rotated successfully"
        )

    except RefreshTokenExpiredError as e:
        logger.info(f"Token refresh denied: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except RefreshTokenRevokedError as e:
        logger.info(f"Token refresh denied (revoked): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except RefreshTokenReuseDetectedError as e:
        logger.warning(f"Security breach detected: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except CompanyIdMismatchError as e:
        logger.warning(f"Company binding validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except RefreshTokenInvalidFamilyError as e:
        logger.info(f"Token refresh denied (family not found): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except RefreshTokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token format: {str(e)}"
        )
    except RefreshTokenConcurrentRaceError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Concurrent refresh race—retry with exponential backoff"
        )
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Refresh token endpoint error: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )
