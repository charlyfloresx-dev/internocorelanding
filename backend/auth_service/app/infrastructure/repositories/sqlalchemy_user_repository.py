from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.domain.entities.user_aggregate import UserEntity, UserCompanyRoleEntity
from app.domain.repositories.user_repository import IUserRepository

from app.models import User, UserCompanyRole, Company, BusinessGroup

class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, user_model: User) -> UserEntity:
        return UserEntity(
            id=user_model.id,
            email=user_model.email,
            hashed_password=user_model.hashed_password,
            identity_token=getattr(user_model, 'identity_token', None),
            is_active=user_model.is_active,
            company_id=user_model.company_id
        )

    async def get_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return self._to_entity(user)
        return None

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            return self._to_entity(user)
        return None

    async def get_by_identity_token(self, token: str) -> Optional[UserEntity]:
        result = await self.db.execute(select(User).where(User.identity_token == token))
        user = result.scalar_one_or_none()
        if user:
            return self._to_entity(user)
        return None

    async def get_user_companies(self, user_id: UUID) -> List[UserCompanyRoleEntity]:
        stmt = (
            select(UserCompanyRole)
            .where(UserCompanyRole.user_id == user_id)
            .options(
                selectinload(UserCompanyRole.company).selectinload(Company.business_group),
                selectinload(UserCompanyRole.role)
            )
        )
        result = await self.db.execute(stmt)
        ucr_list = result.scalars().all()
        
        companies_entities = []
        for ucr in ucr_list:
            if ucr.company:
                entity = UserCompanyRoleEntity(
                    company_id=ucr.company.id,
                    company_name=ucr.company.name,
                    group_id=ucr.company.parent_group_id,
                    logo=ucr.company.logo,
                    is_new=ucr.is_new,
                    role_names=[ucr.role.name] if ucr.role else [],
                    scopes=ucr.scopes or []
                )
                companies_entities.append(entity)
        return companies_entities

    async def get_user_context_for_company(
        self, user_id: UUID, company_id: UUID
    ) -> Tuple[List[str], List[str], Optional[UUID]]:
        stmt = (
            select(UserCompanyRole)
            .where(UserCompanyRole.user_id == user_id, UserCompanyRole.company_id == company_id)
            .options(
                selectinload(UserCompanyRole.role),
                selectinload(UserCompanyRole.company)
            )
        )
        result = await self.db.execute(stmt)
        relation = result.scalar_one_or_none()

        if not relation or not relation.role:
            return [], [], None

        roles = [relation.role.name]
        scopes = relation.scopes or []
        group_id = relation.company.parent_group_id if relation.company else None
        
        return (roles, scopes, group_id)

    async def update_user_password(self, user_id: UUID, hashed_password: str) -> bool:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
            
        user.hashed_password = hashed_password
        self.db.add(user)
        await self.db.commit()
        return True

    async def register_tenant(self, company_name: str, admin_email: str, admin_password_hash: str, admin_first_name: str, admin_last_name: str) -> UserEntity:
        from common.exceptions import DomainException
        
        # 1. Validar que la compañía no exista
        result = await self.db.execute(select(Company).where(Company.name == company_name))
        existing_company = result.scalar_one_or_none()
        if existing_company:
            raise DomainException(f"La compañía '{company_name}' ya existe.")

        # 3. Crear la nueva compañía
        new_company = Company(
            name=company_name,
            status="ACTIVE"
        )
        self.db.add(new_company)
        await self.db.flush()

        # 4. Crear el nuevo usuario
        new_user = User(
            email=admin_email,
            hashed_password=admin_password_hash,
            first_name=admin_first_name,
            last_name=admin_last_name,
            is_active=True,
            company_id=new_company.id
        )
        self.db.add(new_user)
        await self.db.flush()

        # 5. Bootstrap de Auditoría
        new_user.created_by = new_user.id
        new_user.last_modified_by = new_user.id
        new_company.created_by = new_user.id
        new_company.last_modified_by = new_user.id

        # 6. Vincular usuario y compañía
        user_company_access = UserCompanyRole(
            user_id=new_user.id,
            company_id=new_company.id,
            role_name="Admin",
            created_by=new_user.id,
            last_modified_by=new_user.id
        )
        self.db.add(user_company_access)

        # 7. Finalizar la transacción
        await self.db.commit()
        await self.db.refresh(new_user)

        return self._to_entity(new_user)

    async def update_user(self, user_id: UUID, update_data: dict, current_user_id: UUID, current_company_id: UUID) -> UserEntity:
        from common.exceptions import DomainException, NotFoundException
        
        result = await self.db.execute(select(User).where(User.id == user_id, getattr(User, 'is_deleted', False) == False))
        user_to_update = result.scalar_one_or_none()

        if not user_to_update:
            raise NotFoundException("Usuario no encontrado o inaccesible.")

        link_result = await self.db.execute(
            select(UserCompanyRole).where(
                UserCompanyRole.user_id == user_id,
                UserCompanyRole.company_id == current_company_id
            )
        )
        link_check = link_result.scalar_one_or_none()

        if not link_check:
            raise DomainException("No tiene permisos para modificar a este usuario.")

        for key, value in update_data.items():
            setattr(user_to_update, key, value)

        user_to_update.last_modified_by = current_user_id

        self.db.add(user_to_update)
        await self.db.commit()
        await self.db.refresh(user_to_update)

        return self._to_entity(user_to_update)
