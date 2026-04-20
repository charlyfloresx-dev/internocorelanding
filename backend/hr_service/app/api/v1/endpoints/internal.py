import logging
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.collaborator import CollaboratorVerifyRequest, CollaboratorMultiVerifyResponse
from app.services.collaborator_verify_service import verify_collaborator

logger = logging.getLogger(__name__)
router = APIRouter()


def _check_internal_api_key(x_internal_api_key: str = Header(..., alias="X-Internal-Api-Key")):
    """
    Dependency: validates that the request comes from a trusted internal service.
    Only auth_service should call this endpoint.
    """
    if x_internal_api_key != settings.INTERNAL_API_KEY:
        logger.warning("⛔ Unauthorized internal API call blocked.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal API key.",
        )


@router.post(
    "/verify",
    response_model=CollaboratorMultiVerifyResponse,
    summary="Verify Collaborator Identity (Internal)",
    description=(
        "Internal endpoint called by auth_service to validate an RFID or PIN credential. "
        "Protected by X-Internal-Api-Key header. Never expose this route publicly."
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
            detail="Collaborator not found or credentials invalid.",
        )
    return result
