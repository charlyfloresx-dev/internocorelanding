import uuid

from auth_app.domain.repositories.user_repository import IUserRepository
from auth_app.domain.entities.user_aggregate import UserEntity
from auth_app.schemas.audited_schemas import TenantRegistration, UserUpdate
from auth_app.core.security import get_password_hash

# Asumiendo que estas excepciones y el contexto de usuario existen en common
from common.exceptions import DomainException, NotFoundException
from common.domain.entities.user_context import UserContext


async def register_tenant_handler(user_repo: IUserRepository, tenant_data: TenantRegistration) -> UserEntity:
    """
    Handler para crear un nuevo Tenant (Company) y su primer usuario Administrador.
    Implementa la lógica de "Bootstrap de Auditoría".
    """
    admin_password_hash = get_password_hash(tenant_data.admin_password)
    
    return await user_repo.register_tenant(
        company_name=tenant_data.company_name,
        admin_email=tenant_data.admin_email,
        admin_password_hash=admin_password_hash,
        admin_first_name=tenant_data.admin_first_name,
        admin_last_name=tenant_data.admin_last_name
    )


async def update_user_handler(user_repo: IUserRepository, user_id_to_update: uuid.UUID, update_data: UserUpdate, current_user: UserContext) -> UserEntity:
    """
    Handler para actualizar la información de un usuario.
    Asegura la inmutabilidad del company_id y el aislamiento de datos.
    """
    update_data_dict = update_data.model_dump(exclude_unset=True)
    
    return await user_repo.update_user(
        user_id=user_id_to_update,
        update_data=update_data_dict,
        current_user_id=uuid.UUID(current_user.user_id),
        current_company_id=current_user.company_id
    )
