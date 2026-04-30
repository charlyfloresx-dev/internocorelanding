import uuid
import json
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth_app.core.database import get_db
from auth_app.models.user import User
from auth_app.models.user_credential import UserCredential
from auth_app.services.biometric_service import BiometricService
from common.responses import ApiResponse

router = APIRouter()
biometric_service = BiometricService()

# ---------------------------------------------------------------------------
# POST /biometric/register/begin
# Inicia el proceso de registro de una credencial biométrica WebAuthn.
# El frontend llama a este endpoint ANTES de ejecutar navigator.credentials.create()
# ---------------------------------------------------------------------------
@router.post("/register/begin", summary="Iniciar registro biométrico WebAuthn")
async def register_begin(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Recibe: { user_id: UUID }
    Devuelve las PublicKeyCredentialCreationOptions para el dispositivo.
    El frontend debe pasar este objeto a navigator.credentials.create({ publicKey: ... })
    """
    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="user_id requerido")

    try:
        user_id = uuid.UUID(str(user_id_str))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="user_id inválido")

    # Buscar el usuario global
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # Obtener email desde sus credenciales existentes (UserCredential)
    cred_result = await db.execute(
        select(UserCredential).where(UserCredential.user_id == user_id).limit(1)
    )
    credential = cred_result.scalar_one_or_none()
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene credenciales de email registradas. Registra primero con contraseña."
        )

    # Generar las opciones para el cliente
    user_id_bytes = user_id.bytes
    display_name = f"{user.first_name or ''} {user.last_name_pat or ''}".strip() or credential.email
    registration_options, state = biometric_service.register_begin(
        user_id=user_id_bytes,
        user_email=credential.email,
        user_name=display_name
    )

    # El state se guarda temporalmente — en producción usar Redis con TTL de 5 min
    # Por ahora lo retornamos como parte de la respuesta (el cliente lo devuelve en /complete)
    return ApiResponse.success(
        data={
            "options": registration_options,
            "state": state  # El cliente DEBE devolver esto en /register/complete
        },
        message="Challenge de registro generado. Procede con navigator.credentials.create()"
    )


# ---------------------------------------------------------------------------
# POST /biometric/register/complete
# Valida la respuesta del dispositivo y guarda la llave pública.
# ---------------------------------------------------------------------------
@router.post("/register/complete", summary="Completar registro biométrico WebAuthn")
async def register_complete(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Recibe: { user_id: UUID, state: dict, client_response: dict }
    El client_response es la respuesta de navigator.credentials.create() serializada.
    """
    user_id_str = payload.get("user_id")
    state = payload.get("state")
    client_response = payload.get("client_response")

    if not all([user_id_str, state, client_response]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Se requieren: user_id, state y client_response"
        )

    try:
        user_id = uuid.UUID(str(user_id_str))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="user_id inválido")

    # Verificar y extraer la llave pública del dispositivo
    try:
        credential_data_bytes = biometric_service.register_complete(
            state=state,
            client_response=client_response
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registro biométrico rechazado: {str(e)}"
        )

    # Guardar la credencial WebAuthn en user_credentials
    device_name = payload.get("device_name", "Dispositivo Principal")
    new_webauthn_credential = UserCredential(
        user_id=user_id,
        email=f"webauthn_{user_id.hex[:8]}@device.internal",  # Email sintético interno
        credential_type="WEBAUTHN",
        public_key=credential_data_bytes,
        device_fingerprint=device_name,
        is_active=True
    )
    db.add(new_webauthn_credential)
    
    # Marcar biometría como habilitada en el perfil del usuario
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_biometric_enabled = True

    await db.commit()

    return ApiResponse.success(
        data={"biometric_enabled": True, "device": device_name},
        message="Credencial biométrica registrada exitosamente."
    )


# ---------------------------------------------------------------------------
# POST /biometric/auth/begin
# Inicia el challenge de autenticación para un usuario registrado con WebAuthn.
# ---------------------------------------------------------------------------
@router.post("/auth/begin", summary="Iniciar autenticación biométrica")
async def auth_begin(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Recibe: { email: str }  — el email de la credencial de contraseña vinculada al User
    Devuelve: las PublicKeyCredentialRequestOptions para el dispositivo.
    El frontend pasa esto a navigator.credentials.get({ publicKey: ... })
    """
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="email requerido")

    # Buscar la credencial de contraseña para obtener el user_id
    result = await db.execute(
        select(UserCredential).where(
            UserCredential.email == email,
            UserCredential.credential_type == "PASSWORD"
        )
    )
    password_cred = result.scalar_one_or_none()
    if not password_cred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # Verificar que el usuario tiene biometría habilitada
    user_result = await db.execute(select(User).where(User.id == password_cred.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_biometric_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este usuario no tiene autenticación biométrica habilitada"
        )

    # Obtener todas las credenciales WebAuthn del usuario
    webauthn_result = await db.execute(
        select(UserCredential).where(
            UserCredential.user_id == password_cred.user_id,
            UserCredential.credential_type == "WEBAUTHN",
            UserCredential.is_active == True
        )
    )
    webauthn_creds = webauthn_result.scalars().all()
    if not webauthn_creds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay dispositivos biométricos registrados para este usuario"
        )

    # Extraer las llaves públicas almacenadas
    allowed_credentials = [c.public_key for c in webauthn_creds if c.public_key]
    
    auth_options, state = biometric_service.authenticate_begin(
        allowed_credentials=allowed_credentials
    )

    return ApiResponse.success(
        data={
            "options": auth_options,
            "state": state,
            "user_id": str(password_cred.user_id)
        },
        message="Challenge de autenticación generado. Procede con navigator.credentials.get()"
    )


# ---------------------------------------------------------------------------
# POST /biometric/auth/complete
# Valida la firma del dispositivo y emite el token de selección de empresa (T1).
# ---------------------------------------------------------------------------
@router.post("/auth/complete", summary="Completar autenticación biométrica")
async def auth_complete(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Recibe: { user_id: UUID, state: dict, client_response: dict }
    Si la firma es válida, retorna el selection_token (T1) + lista de empresas.
    El frontend luego llama a /auth/select-company para obtener el JWT final (T2).
    """
    user_id_str = payload.get("user_id")
    state = payload.get("state")
    client_response = payload.get("client_response")

    if not all([user_id_str, state, client_response]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Se requieren: user_id, state y client_response"
        )

    try:
        user_id = uuid.UUID(str(user_id_str))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="user_id inválido")

    # Obtener llaves públicas del usuario para validación
    webauthn_result = await db.execute(
        select(UserCredential).where(
            UserCredential.user_id == user_id,
            UserCredential.credential_type == "WEBAUTHN",
            UserCredential.is_active == True
        )
    )
    webauthn_creds = webauthn_result.scalars().all()
    allowed_credentials = [c.public_key for c in webauthn_creds if c.public_key]

    if not allowed_credentials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay credenciales biométricas registradas"
        )

    # Validar la firma criptográfica del dispositivo
    is_valid = biometric_service.authenticate_complete(
        state=state,
        credentials=allowed_credentials,
        client_response=client_response
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación biométrica fallida. Firma inválida."
        )

    # Obtener las empresas a las que pertenece el usuario (UserCompanyRole)
    from auth_app.models.user_company_role import UserCompanyRole
    from auth_app.models.user import User
    from common.models import Company

    ucr_result = await db.execute(
        select(UserCompanyRole, Company).join(
            Company, UserCompanyRole.company_id == Company.id
        ).where(
            UserCompanyRole.user_id == user_id,
            UserCompanyRole.is_active == True
        )
    )
    company_rows = ucr_result.all()

    companies = [
        {
            "company_id": str(row.UserCompanyRole.company_id),
            "company_name": row.Company.name,
            "roles": [row.UserCompanyRole.role_id]
        }
        for row in company_rows
    ]

    # Emitir el selection_token (T1) — mismo flujo que el login clásico
    from auth_app.core.security import create_access_token
    selection_token = create_access_token(
        data={"sub": str(user_id), "type": "selection", "method": "biometric"},
        expires_delta_minutes=5
    )

    return ApiResponse.success(
        data={
            "selection_token": selection_token,
            "companies": companies,
            "auth_method": "biometric"
        },
        message="Autenticación biométrica exitosa. Selecciona tu empresa."
    )
