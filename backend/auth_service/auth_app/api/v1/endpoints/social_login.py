"""
social_login.py — Interno Core Auth Service
Endpoint: POST /api/v1/auth/social-login

Flujo:
  1. Recibe token + provider (google | facebook | microsoft)
  2. Valida el token contra el proveedor externo via social_auth_service
  3. Busca o crea el usuario en la DB por email
  4. Emite un selection_token + CompanyAccessDto (mismo contrato que /login)
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth_app.dependencies import get_db, get_auth_service
from auth_app.services.auth_service import AuthService
from auth_app.services.social_auth_service import SocialAuthService
from auth_app.schemas.auth import CompanyAccessDto, CompanySelection
from auth_app.schemas.social_auth import SocialLoginRequest
from auth_app.models.user import User
from auth_app.models.company import Company
from auth_app.core import security
from common.responses import ApiResponse
from common.audit.logger import AuditLogger

router = APIRouter()
_social_auth_service = SocialAuthService()


@router.post(
    "/social-login",
    response_model=ApiResponse[CompanyAccessDto],
    summary="Autenticación via proveedor OAuth social (Google / Facebook / Microsoft)",
    tags=["Auth — Social"],
)
async def social_login(
    body: SocialLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Intercambia un token OAuth social por el selection_token de Interno Core
    y devuelve la lista de empresas (CompanyAccessDto) disponibles para el usuario.
    
    **Flujo completo:**
    1. Valida el token con el proveedor externo.
    2. Busca al usuario en la DB por su email social.
    3. Si no existe, lo crea con rol por defecto "Traveler" en el Tenant de Viatra.
    4. Emite un `selection_token` (typ: "selection") + `CompanyAccessDto`.
    """

    # 1. Validar token con el proveedor externo
    profile = await _social_auth_service.validate(body.token, body.provider)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired {body.provider} token.",
        )

    # 2. Buscar usuario por email
    result = await db.execute(select(User).where(User.email == profile.email))
    user_model = result.scalar_one_or_none()
    is_new = False

    # 3. Si no existe → auto-registro con rol "Traveler"
    if not user_model:
        is_new = True

        # Buscar o crear la empresa raíz de Viatra Core para los viajeros B2C
        viatra_company_result = await db.execute(
            select(Company).where(Company.name == "Viatra Core — Travelers")
        )
        viatra_company = viatra_company_result.scalar_one_or_none()

        if not viatra_company:
            viatra_company = Company(name="Viatra Core — Travelers", status="ACTIVE")
            db.add(viatra_company)
            await db.flush()

        # Crear el nuevo usuario
        user_model = User(
            email=profile.email,
            hashed_password=None,           # Sin contraseña — acceso solo por OAuth
            is_active=True,
            company_id=viatra_company.id,
        )

        # Añadir nombre completo si el modelo lo soporta
        if hasattr(user_model, "full_name"):
            user_model.full_name = profile.full_name

        db.add(user_model)
        await db.flush()

        # Bootstrap de auditoría
        if hasattr(user_model, "created_by"):
            user_model.created_by = user_model.id
        if hasattr(user_model, "last_modified_by"):
            user_model.last_modified_by = user_model.id

        await db.flush()

    # 4. Verificar que el usuario esté activo
    if not user_model.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive.")

    # 5. Emitir selection_token (typ: "selection") — idéntico al flujo /login
    selection_token = security.create_selection_token(user_model.id)

    # 6. Obtener empresas disponibles
    companies = await auth_service.get_user_companies(user_model.id)

    # 7. Audit log
    await AuditLogger.log_action(
        db=db,
        action="AUTH_SOCIAL_LOGIN_HANDSHAKE",
        table_name="users",
        record_id=str(user_model.id),
        user_id=str(user_model.id),
        request=request,
    )
    await db.commit()

    return ApiResponse(
        status="success",
        data=CompanyAccessDto(
            selection_token=selection_token,
            user_id=user_model.id,
            companies=companies,
            is_new=is_new,
        ),
        message=f"Social login via {body.provider} successful. Please select a company.",
    )
