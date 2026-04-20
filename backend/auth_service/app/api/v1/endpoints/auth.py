# pyre-ignore-all-errors[21]
"""
auth.py — Interno Core Auth Service
Endpoints: /login, /select-company, /refresh, /request-password-reset,
           /confirm-password-reset, /me
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_db,
    get_selection_payload,
    SelectionTokenPayload,
    get_auth_service,
    get_select_company_handler,
    get_current_tenant_context,
    SecurityContext,
)
from common.responses import ApiResponse
from app.schemas.auth import (
    LoginRequest,
    AccessTokenResponse,
    SelectCompanyRequest,
    CompanyAccessDto,
    RefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
)
from app.services.auth_service import AuthService
from app.commands.select_company_command import SelectCompanyCommandHandler, SelectCompanyCommand
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.company import Company
from app.models.refresh_token import RefreshToken
from common.audit.logger import AuditLogger
from common.security.limiter import limiter

router = APIRouter()


# ── LOGIN ─────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=ApiResponse[CompanyAccessDto])
@limiter.limit("5/minute")
async def login(
    credentials: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = None

    if credentials.email and credentials.password:
        user = await auth_service.authenticate_user(credentials.email, credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
    elif credentials.identity_token:
        user = await auth_service.authenticate_by_identity_token(credentials.identity_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid identity token",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing credentials. Provide email/password or identity_token.",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    selection_token = security.create_selection_token(user.id)
    companies = await auth_service.get_user_companies(user.id)

    await AuditLogger.log_action(
        db=db,
        action="AUTH_LOGIN_HANDSHAKE",
        table_name="users",
        record_id=str(user.id),
        user_id=str(user.id),
        request=request,
    )
    await db.commit()

    return ApiResponse(
        status="success",
        data=CompanyAccessDto(
            selection_token=selection_token,
            user_id=user.id,
            companies=companies,
            is_new=False,
        ),
        message="Login successful. Please select a company.",
    )


# ── SELECT COMPANY ────────────────────────────────────────────────────────────

@router.post(
    "/select-company",
    response_model=ApiResponse[AccessTokenResponse],
    summary="Genera access + refresh token contextualizados a una empresa",
)
@limiter.limit("10/minute")
async def select_company(
    request_body: SelectCompanyRequest,
    request: Request,
    payload: SelectionTokenPayload = Depends(get_selection_payload),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    handler: SelectCompanyCommandHandler = Depends(get_select_company_handler),
):
    user_id = payload.sub
    company_id = request_body.company_id

    command = SelectCompanyCommand(user_id=user_id, company_id=company_id)
    result = await handler.handle(command)
    await db.commit()

    return ApiResponse(
        status="success",
        data=AccessTokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user_id=user_id,
            company_id=company_id,
            roles=result["roles"],
            scopes=result["scopes"],
            permissions=result["permissions"],
        ),
        message="Access token generated successfully.",
    )


# ── REFRESH ───────────────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=ApiResponse[AccessTokenResponse],
    summary="Rota el refresh token y emite un nuevo access token",
)
@limiter.limit("20/minute")
async def refresh_token_endpoint(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh Token Rotation Flow:
    1. Validate JWT signature & expiry (typ must be "refresh").
    2. Look up the token_hash in DB — must exist and not be revoked.
    3. Verify User is still ACTIVE in the DB.
    4. Verify Company is still ACTIVE in the DB.
    5. Revoke the old refresh token immediately (rotation).
    6. Re-fetch permissions (detects revocation scenarios).
    7. Issue new access_token + new refresh_token.
    8. Persist new refresh record atomically.
    """
    _UNAUTHORIZED = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token.",
    )

    # Step 1 — Decode & validate typ claim
    try:
        payload = security.decode_token(body.refresh_token, expected_typ="refresh")
    except ValueError:
        raise _UNAUTHORIZED
    if not payload:
        raise _UNAUTHORIZED

    raw_user_id = payload.get("sub")
    raw_company_id = payload.get("company_id")
    if not raw_user_id or not raw_company_id:
        raise _UNAUTHORIZED

    try:
        user_id = uuid.UUID(raw_user_id)
        company_id = uuid.UUID(raw_company_id)
    except ValueError:
        raise _UNAUTHORIZED

    # Step 2 — Check DB record (must exist and not be revoked)
    token_hash = security.hash_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        raise _UNAUTHORIZED  # Possible replay attack

    # Step 3 — Verify User is ACTIVE
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive.")

    # Step 4 — Verify Company is ACTIVE
    company = await db.get(Company, company_id)
    if not company or company.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company is not active.")

    # Step 5 — Revoke old refresh token (rotation)
    await db.execute(
        update(RefreshToken).where(RefreshToken.id == db_token.id).values(revoked=True)
    )

    # Step 6 — Re-fetch current permissions
    permissions = await auth_service.get_user_permissions_for_company(user_id, company_id)
    roles = await auth_service.get_user_roles_for_company(user_id, company_id)

    # Step 7 — Issue new tokens
    new_access = security.create_access_token(
        subject=str(user_id),
        company_id=str(company_id),
        data={"role_names": roles, "scopes": permissions},
    )
    new_refresh_raw = security.create_refresh_token(subject=user_id, company_id=company_id)

    # Step 8 — Persist new refresh record
    db.add(RefreshToken(
        user_id=user_id,
        company_id=company_id,
        tenant_id=company_id,
        token_hash=security.hash_token(new_refresh_raw),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        revoked=False,
    ))
    await db.commit()

    return ApiResponse(
        status="success",
        data=AccessTokenResponse(
            access_token=new_access,
            refresh_token=new_refresh_raw,
            user_id=user_id,
            company_id=company_id,
            roles=roles,
            scopes=permissions,
            permissions=permissions,
        ),
        message="Token refreshed successfully.",
    )


# ── PASSWORD RESET ────────────────────────────────────────────────────────────
@router.post("/request-password-reset", response_model=ApiResponse)
@limiter.limit("3/minute")
async def request_password_reset(
    request_body: PasswordResetRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.request_password_reset(request_body.email)
    return ApiResponse(
        status="success",
        data={"email": request_body.email},
        message="If the email exists, a password reset OTP has been sent.",
    )


@router.post("/confirm-password-reset", response_model=ApiResponse)
@limiter.limit("5/minute")
async def confirm_password_reset(
    request_body: PasswordResetConfirmRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    success = await auth_service.confirm_password_reset(
        request_body.email, request_body.otp, request_body.new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP or user not found",
        )
    return ApiResponse(
        status="success",
        data={"email": request.email},
        message="Password has been reset successfully. You can now log in.",
    )


# ── ME (Zero Trust Validation) ────────────────────────────────────────────────

@router.get("/me", response_model=ApiResponse[AccessTokenResponse])
async def get_current_user_info(
    request: Request,
    context: SecurityContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Endpoint de Validación Zero Trust.
    Verifica token + empresa en headers; retorna sesión completa para hidratar el frontend.
    """
    if context.role == "collaborator":
        return ApiResponse(
            status="success",
            data=AccessTokenResponse(
                access_token=request.headers.get("Authorization", "").replace("Bearer ", ""),
                user_id=context.user_id,
                company_id=context.company_id,
                roles=["collaborator"],
                permissions=context.scopes,
                scopes=context.scopes,
                user_full_name=context.full_name or "Industrial Operator",
                user_email=None
            ),
            message="Collaborator session validated successfully."
        )

    user = await db.get(User, context.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return ApiResponse(
        status="success",
        data=AccessTokenResponse(
            access_token=request.headers.get("Authorization", "").replace("Bearer ", ""),
            user_id=user.id,
            company_id=context.company_id,
            roles=[],
            permissions=context.scopes,
            scopes=context.scopes,
            user_full_name=getattr(user, "full_name", None) or user.email,
            user_email=user.email,
        ),
        message="Session validated successfully.",
    )