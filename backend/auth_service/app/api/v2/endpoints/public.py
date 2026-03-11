from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.invitation import UserRegistration
from app.commands.complete_registration_command import CompleteRegistrationCommand, CompleteRegistrationCommandHandler
from common.responses import ApiResponse

router = APIRouter()

@router.post("/complete-registration", response_model=ApiResponse)
async def complete_registration(
    registration: UserRegistration,
    db: AsyncSession = Depends(get_db)
):
    command = CompleteRegistrationCommand(
        code=registration.code,
        password=registration.password,
        full_name=registration.full_name
    )
    handler = CompleteRegistrationCommandHandler(db)
    result = await handler.handle(command)
    return ApiResponse(data=result, message="Registration completed successfully")

from app.schemas.auth import RegisterCompanyRequest
from app.commands.register_company_command import RegisterCompanyCommand, RegisterCompanyCommandHandler

@router.post("/register-company", response_model=ApiResponse)
async def register_company(
    request: RegisterCompanyRequest,
    db: AsyncSession = Depends(get_db)
):
    command = RegisterCompanyCommand(
        company_name=request.company_name,
        admin_email=request.admin_email,
        admin_password=request.admin_password,
        admin_full_name=request.admin_full_name,
        group_id=request.group_id,
        group_name=request.group_name
    )
    handler = RegisterCompanyCommandHandler(db)
    result = await handler.handle(command)
    
    return ApiResponse(
        status="success",
        data=result,
        message="Company registered successfully. Check email for confirmation."
    )
