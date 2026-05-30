"""
Refresh Token Rotation Endpoint — FastAPI Router.

POST /api/v1/auth/refresh — Stateless RTR con mitigación de race conditions.
"""
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

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


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
@limiter.limit("20/minute")
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

    except RefreshTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    except RefreshTokenRevokedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token family revoked: {str(e)}"
        )
    except RefreshTokenReuseDetectedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected—security lockout (family revoked)"
        )
    except CompanyIdMismatchError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token (company binding failed)"
        )
    except RefreshTokenInvalidFamilyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token family not found"
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
