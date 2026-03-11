import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_selection_payload, SelectionTokenPayload, get_auth_service, get_select_company_handler
from common.responses import ApiResponse
from app.schemas.auth import LoginRequest, AccessTokenResponse, SelectCompanyRequest, CompanyAccessDto
from app.services.auth_service import AuthService
from app.commands.select_company_command import SelectCompanyCommandHandler
from app.core import security
from common.audit.logger import AuditLogger

router = APIRouter()

@router.post("/login", response_model=ApiResponse[CompanyAccessDto])
async def login(
    credentials: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = None
    
    # Bifurcación de lógica: Prioridad Email/Password sobre identity_token
    if credentials.email and credentials.password:
        # Autenticación estándar
        user = await auth_service.authenticate_user(credentials.email, credentials.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    elif credentials.identity_token:
        # Autenticación por RFID/Barcode
        user = await auth_service.authenticate_by_identity_token(credentials.identity_token)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid identity token")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing credentials. Provide email/password or identity_token."
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
        request=request
    )
    
    await db.commit()
    
    return ApiResponse(
        status="success",
        data=CompanyAccessDto(
            selection_token=selection_token,
            user_id=user.id,
            companies=companies,
            is_new=False  # Defaulting to false unless explicit onboarding logic exists
        ),
        message="Login successful. Please select a company."
    )

@router.post(
    "/select-company",
    response_model=ApiResponse[AccessTokenResponse], # Added generic type
    summary="Genera el token de acceso final contextualizado a una empresa",
)
async def select_company(
    request_body: SelectCompanyRequest,
    request: Request,
    # La dependencia debe extraer el user_id del selection_token
    payload: SelectionTokenPayload = Depends(get_selection_payload),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    handler: SelectCompanyCommandHandler = Depends(get_select_company_handler)
):
    user_id = payload.sub
    company_id = request_body.company_id

    # 1. Ejecutar selección de empresa a través del Handler (Compliance: Audit inside)
    from app.commands.select_company_command import SelectCompanyCommand
    command = SelectCompanyCommand(user_id=user_id, company_id=company_id)
    result = await handler.handle(command)

    # 2. Commit atómico
    await db.commit()

    return ApiResponse(
        status="success",
        data=AccessTokenResponse(
            access_token=result["access_token"], 
            user_id=user_id,
            company_id=company_id, 
            roles=result["roles"], 
            scopes=result["scopes"],
            permissions=result["permissions"]
        ),
        message="Access token generated successfully."
    )

from app.schemas.auth import PasswordResetRequest, PasswordResetConfirmRequest

@router.post("/request-password-reset", response_model=ApiResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    # Ignoramos el bool return value en la respuesta para no fugar información
    await auth_service.request_password_reset(request.email)
    
    return ApiResponse(
        status="success",
        data={"email": request.email},
        message="If the email exists, a password reset OTP has been sent."
    )

@router.post("/confirm-password-reset", response_model=ApiResponse)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    success = await auth_service.confirm_password_reset(request.email, request.otp, request.new_password)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP or user not found")
        
    return ApiResponse(
        status="success",
        data={"email": request.email},
        message="Password has been reset successfully. You can now log in."
    )