import uuid
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Body, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth_app.core.database import get_db
from auth_app.commands.collaborator_login_command import collaborator_login

logger = logging.getLogger(__name__)
router = APIRouter()


from auth_app.schemas.auth import CompanySelection


class CollaboratorLoginRequest(BaseModel):
    identity_identifier: str  # RFID or PIN
    access_method: str       # 'RFID_SCAN' or 'PIN_PAD'
    internal_id: Optional[str] = None # Added for PIN_PAD method
    terminal_id: Optional[str] = None
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
    "/collaborator-login",
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
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    # Unpack identity_identifier based on access_method
    rfid = request.identity_identifier if request.access_method == "RFID_SCAN" else None
    pin = request.identity_identifier if request.access_method == "PIN_PAD" else None
    internal_id = request.internal_id if request.access_method == "PIN_PAD" else None

    result = await collaborator_login(
        db=db,
        rfid_tag=rfid,
        internal_id=internal_id,
        pin_code=pin,
        company_id=request.company_id,
        ip_address=req.client.host if req.client else None,
        transaction_id=getattr(req.state, "transaction_id", None)
    )
    await db.commit()
    # result already contains either access_token or selection_token/companies
    return result
