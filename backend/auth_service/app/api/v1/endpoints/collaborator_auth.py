import uuid
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Body, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.commands.collaborator_login_command import collaborator_login

logger = logging.getLogger(__name__)
router = APIRouter()


from app.schemas.auth import CompanySelection


class CollaboratorLoginRequest(BaseModel):
    rfid_tag: Optional[str] = None
    internal_id: Optional[str] = None
    pin_code: Optional[str] = None
    company_id: Optional[uuid.UUID] = None


class CollaboratorLoginResponse(BaseModel):
    # Phase 2: Direct access
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    user_id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None
    company_name: Optional[str] = None
    scopes: list[str] = []
    permissions: list[str] = []
    user_full_name: Optional[str] = None
    
    # Phase 1: Selection (if multiple matches)
    selection_token: Optional[str] = None
    companies: Optional[list[CompanySelection]] = None


@router.post(
    "/collaborator/login",
    response_model=CollaboratorLoginResponse,
    summary="Collaborator Login (Kiosk / RFID / PIN)",
    description=(
        "Physical identity login for floor operators. Accepts either an RFID tag "
        "(intercepted by the hardware buffer) or a numeric PIN. "
        "Emits a JWT with role=collaborator or a selection list if multiple companies match."
    ),
)
async def collaborator_login_endpoint(
    request: CollaboratorLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await collaborator_login(
        db=db,
        rfid_tag=request.rfid_tag,
        internal_id=request.internal_id,
        pin_code=request.pin_code,
        company_id=request.company_id,
    )
    # result already contains either access_token or selection_token/companies
    return result
