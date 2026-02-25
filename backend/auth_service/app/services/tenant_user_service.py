import uuid
from sqlalchemy.orm import Session

from app.models.user import User, Company, UserCompanyRole
from app.schemas.audited_schemas import TenantRegistration, UserUpdate
from app.core.security import get_password_hash

# Asumiendo que estas excepciones y el contexto de usuario existen en common
from common.exceptions import DomainException, NotFoundException
from common.models.user_context import UserContext


def register_tenant_handler(db: Session, tenant_data: TenantRegistration) -> User:
    """
    Handler para crear un nuevo Tenant (Company) y su primer usuario Administrador.
    Implementa la lógica de "Bootstrap de Auditoría".
    """
    # 1. Validar que la compañía no exista
    existing_company = db.query(Company).filter(Company.name == tenant_data.company_name).first()
    if existing_company:
        raise DomainException(f"La compañía '{tenant_data.company_name}' ya existe.")

    # 2. Validar que el email no esté ya en uso para otra compañía (si la regla de negocio lo exige)
    # La UniqueConstraint("email", "company_id") permite el registro, así que procedemos.

    # 3. Crear la nueva compañía
    new_company = Company(
        name=tenant_data.company_name,
        status="ACTIVE"  # Estado inicial
    )
    db.add(new_company)
    db.flush() # Obtenemos el ID de la compañía sin hacer commit

    # 4. Crear el nuevo usuario
    new_user = User(
        email=tenant_data.admin_email,
        hashed_password=get_password_hash(tenant_data.admin_password),
        first_name=tenant_data.admin_first_name,
        last_name=tenant_data.admin_last_name,
        is_active=True
    )
    db.add(new_user)
    db.flush() # Obtenemos el ID del usuario sin hacer commit

    # 5. **Bootstrap de Auditoría**: El usuario se crea a sí mismo.
    # Se asigna su propio ID como creador para mantener la trazabilidad.
    new_user.created_by = new_user.id
    new_user.last_modified_by = new_user.id
    
    # Asignamos el creador a la compañía también
    new_company.created_by = new_user.id
    new_company.last_modified_by = new_user.id

    # 6. Vincular usuario y compañía con el rol de Administrador
    user_company_access = UserCompanyRole(
        user_id=new_user.id,
        company_id=new_company.id,
        role_name="Admin",  # Asumiendo un rol base
        created_by=new_user.id,
        last_modified_by=new_user.id
    )
    db.add(user_company_access)

    # 7. Finalizar la transacción
    db.commit()
    db.refresh(new_user)

    return new_user


def update_user_handler(db: Session, user_id_to_update: uuid.UUID, update_data: UserUpdate, current_user: UserContext) -> User:
    """
    Handler para actualizar la información de un usuario.
    Asegura la inmutabilidad del company_id y el aislamiento de datos.
    """
    # 1. Obtener el usuario a actualizar, asegurando que no esté eliminado
    user_to_update = db.query(User).filter(
        User.id == user_id_to_update,
        User.is_deleted == False
    ).first()

    if not user_to_update:
        raise NotFoundException("Usuario no encontrado o inaccesible.")

    # 2. **Aislamiento Multitenant**: Validar que el usuario a editar pertenece a la misma
    #    empresa que el usuario que realiza la acción.
    link_check = db.query(UserCompanyRole).filter(
        UserCompanyRole.user_id == user_id_to_update,
        UserCompanyRole.company_id == current_user.company_id
    ).first()

    if not link_check:
        # Lanza excepción si se intenta editar un usuario de otro tenant
        raise DomainException("No tiene permisos para modificar a este usuario.")

    # 3. Aplicar los cambios desde el DTO.
    # El `company_id` no puede venir en el DTO, garantizando inmutabilidad a nivel de API.
    update_data_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_data_dict.items():
        setattr(user_to_update, key, value)

    # 4. El BaseRepository (si se usara para guardar) o el contexto global
    #    se encargarían de actualizar `last_modified_by` con el `current_user.user_id`.
    #    Si lo hacemos manualmente:
    user_to_update.last_modified_by = current_user.user_id

    db.add(user_to_update)
    db.commit()
    db.refresh(user_to_update)

    return user_to_update