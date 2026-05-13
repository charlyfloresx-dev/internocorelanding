from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from auth_app.dependencies import get_db, get_current_user
from auth_app.schemas.invitation import InvitationCreate, InvitationResponse, UserRoleAssignment
from auth_app.schemas.role import RoleResponse
from auth_app.commands.invite_user_command import InviteUserCommand, InviteUserCommandHandler
from auth_app.commands.assign_role_command import AssignRoleCommand, AssignRoleCommandHandler
from auth_app.queries.get_roles_query import GetRolesQuery, GetRolesQueryHandler
from common.responses import ApiResponse
from common.security.dependencies import require_scope

router = APIRouter()

@router.get("/roles", response_model=ApiResponse[List[RoleResponse]], dependencies=[Depends(require_scope(["admin:read"]))])
async def get_roles(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Security: require_scope handled in decorator
    query = GetRolesQuery()
    handler = GetRolesQueryHandler(db)
    roles = await handler.handle(query)
    return ApiResponse(data=roles, message="Roles retrieved successfully")

@router.post("/users/invite", response_model=ApiResponse[InvitationResponse], dependencies=[Depends(require_scope(["admin:write"]))])
async def invite_user(
    invitation: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Security: require_scope handled in decorator
    # Enforzar multi-tenancy del admin logueado
    command = InviteUserCommand(
        email=invitation.email,
        role_id=invitation.role_id,
        company_id=current_user.company_id
    )
    handler = InviteUserCommandHandler(db)
    result = await handler.handle(command)
    return ApiResponse(data=result, message="User invited successfully")

@router.post("/users/assign-role", response_model=ApiResponse, dependencies=[Depends(require_scope(["admin:write"]))])
async def assign_role(
    assignment: UserRoleAssignment,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Security: require_scope handled in decorator
    # Enforzar multi-tenancy del admin logueado
    command = AssignRoleCommand(
        email=assignment.email,
        role_id=assignment.role_id,
        company_id=current_user.company_id
    )
    handler = AssignRoleCommandHandler(db)
    result = await handler.handle(command)
    return ApiResponse(data=result, message="Role assigned successfully")
