import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from common.cqrs import ICommand, ICommandHandler
from app.models.company import Company
from app.models.user import User
from app.models.role import Role
from app.models.user_company_role import UserCompanyRole
from common.models.business_group import BusinessGroup
from app.core.security import get_password_hash
from common.services.audit_service import AuditService

class RegisterCompanyCommand(ICommand):
    def __init__(
        self,
        company_name: str,
        admin_email: str,
        admin_password: str,
        admin_full_name: str,
        group_id: Optional[uuid.UUID] = None,
        group_name: Optional[str] = None
    ):
        self.company_name = company_name
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.admin_full_name = admin_full_name
        self.group_id = group_id
        self.group_name = group_name

class RegisterCompanyCommandHandler(ICommandHandler[dict]):
    def __init__(self, db: AsyncSession, audit_service: Optional[AuditService] = None):
        self.db = db
        self.audit_service = audit_service or AuditService()

    async def handle(self, command: RegisterCompanyCommand) -> dict:
        business_group = None
        if command.group_id:
            bg_stmt = select(BusinessGroup).where(BusinessGroup.id == command.group_id)
            bg_res = await self.db.execute(bg_stmt)
            business_group = bg_res.scalar_one_or_none()
            if not business_group:
                raise ValueError("Provided Business Group ID does not exist.")
        else:
            group_name = command.group_name if command.group_name else command.company_name
            business_group = BusinessGroup(name=group_name)
            self.db.add(business_group)
            await self.db.flush()

        company = Company(
            name=command.company_name,
            parent_group_id=business_group.id
        )
        self.db.add(company)
        await self.db.flush()

        user_stmt = select(User).where(User.email == command.admin_email)
        user_res = await self.db.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user:
            user = User(
                email=command.admin_email,
                hashed_password=get_password_hash(command.admin_password),
                full_name=command.admin_full_name,
                is_active=True
            )
            self.db.add(user)
            await self.db.flush()

        role = Role(
            name="OWNER",
            description="Company Owner",
            company_id=company.id
        )
        self.db.add(role)
        await self.db.flush()

        user_company_role = UserCompanyRole(
            user_id=user.id,
            company_id=company.id,
            role_id=role.id,
            is_new=True
        )
        self.db.add(user_company_role)

        await self.db.commit()

        # Auditoria de la operación
        await self.audit_service.log_action(
            db=self.db,
            user_id=user.id,
            action="REGISTER_COMPANY",
            entity_name="Company",
            entity_id=company.id,
            details=f"Company {company.name} registered under group {business_group.name}"
        )

        return {
            "company_id": str(company.id),
            "group_id": str(business_group.id) if business_group else None,
            "user_id": str(user.id),
            "message": "Company and Admin User registered successfully."
        }
