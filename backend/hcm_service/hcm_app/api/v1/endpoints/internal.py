import logging
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from hcm_app.core.config import settings
from hcm_app.core.database import get_db
from hcm_app.schemas.collaborator import CollaboratorVerifyRequest, CollaboratorMultiVerifyResponse
from hcm_app.services.collaborator_verify_service import verify_collaborator

logger = logging.getLogger(__name__)
router = APIRouter()


def _check_internal_api_key(x_internal_api_key: str = Header(..., alias="X-Internal-Api-Key")):
    """
    Dependency: validates that the request comes from a trusted internal service.
    Only auth_service should call this endpoint.
    """
    if x_internal_api_key != settings.INTERNAL_API_KEY:
        logger.warning("⛔ Llamada interna no autorizada bloqueada.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clave de API interna inválida.",
        )


@router.post(
    "/verify",
    response_model=CollaboratorMultiVerifyResponse,
    summary="Verificar Identidad de Colaborador (Interno)",
    description=(
        "Endpoint interno invocado por auth_service para validar credenciales RFID o PIN. "
        "Protegido por header X-Internal-Api-Key. No exponer públicamente."
    ),
)
async def verify_collaborator_endpoint(
    request: CollaboratorVerifyRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_check_internal_api_key),
):
    result = await verify_collaborator(request, db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Colaborador no encontrado o credenciales inválidas.",
        )
    return result
