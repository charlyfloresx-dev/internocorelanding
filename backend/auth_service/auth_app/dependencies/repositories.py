from auth_app.domain.repositories.user_repository import IUserRepository
from auth_app.domain.repositories.user_company_role_repository import IUserCompanyRoleRepository
from auth_app.domain.repositories.permission_repository import IPermissionRepository
from auth_app.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from auth_app.infrastructure.repositories.sqlalchemy_user_company_role_repository import SQLAlchemyUserCompanyRoleRepository
from auth_app.infrastructure.repositories.sqlalchemy_permission_repository import SQLAlchemyPermissionRepository
from auth_app.dependencies.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from auth_app.services.auth_service import AuthService
from auth_app.commands.select_company_command import SelectCompanyCommandHandler

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> IUserRepository:
    return SQLAlchemyUserRepository(db)

async def get_ucr_repository(db: AsyncSession = Depends(get_db)) -> IUserCompanyRoleRepository:
    return SQLAlchemyUserCompanyRoleRepository(db)

async def get_permission_repository(db: AsyncSession = Depends(get_db)) -> IPermissionRepository:
    return SQLAlchemyPermissionRepository(db)

def get_auth_service(
    user_repo: IUserRepository = Depends(get_user_repository)
) -> AuthService:
    return AuthService(user_repo)

def get_select_company_handler(
    ucr_repo: IUserCompanyRoleRepository = Depends(get_ucr_repository),
    permission_repo: IPermissionRepository = Depends(get_permission_repository),
    db: AsyncSession = Depends(get_db)
) -> SelectCompanyCommandHandler:
    return SelectCompanyCommandHandler(ucr_repo, permission_repo, db)
