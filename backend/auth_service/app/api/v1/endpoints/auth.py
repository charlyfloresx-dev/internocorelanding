import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_selection_payload, SelectionTokenPayload
from app.services.auth_service import AuthService
from app.core import security
from app.core.database import get_db
from common.responses import ApiResponse
from app.schemas.auth import LoginRequest, AccessTokenResponse, SelectCompanyRequest, LoginResponseData

router = APIRouter()

@router.post("/login", response_model=ApiResponse[LoginResponseData])
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    selection_token = security.create_selection_token(user.id)
    companies = await AuthService.get_user_companies(db, user.id)
    
    return ApiResponse(
        status="success",
        data=LoginResponseData(
            selection_token=selection_token,
            companies=companies
        ),
        message="Login successful. Please select a company."
    )

@router.post(
    "/select-company",
    response_model=ApiResponse,
    summary="Genera el token de acceso final contextualizado a una empresa",
)
async def select_company(
    request_body: SelectCompanyRequest,
    # La dependencia debe extraer el user_id del selection_token
    payload: SelectionTokenPayload = Depends(get_selection_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = payload.sub
    company_id = request_body.company_id

    # 1. Llamar al servicio CORREGIDO
    roles, scopes = await AuthService.get_user_context_for_company(db, user_id, company_id)

    if not roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have access to this company.")

    # 2. Crear el JWT final, ahora con scopes
    access_token = security.create_final_access_token(user_id, company_id, roles, scopes)

    # 3. Retornar la respuesta completa, cumpliendo el DTO
    return ApiResponse(
        status="success",
        data=AccessTokenResponse(
            access_token=access_token, 
            user_id=user_id,      # <--- ESTO ES LO QUE FALTABA
            company_id=company_id, 
            roles=roles, 
            scopes=scopes,
            permissions=scopes     # Usamos scopes como permisos para el DTO
        ),
        message="Access token generated successfully."
    )