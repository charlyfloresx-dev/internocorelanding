import uuid
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.domain.ports.collaborator_repository import ICollaboratorRepository
from app.domain.entities.collaborator_entities import Collaborator as DomainCollaborator
from app.models.collaborator import Collaborator as ORMCollaborator
from app.models.tenant_settings import HrTenantConfig

logger = logging.getLogger(__name__)

class SQLAlchemyCollaboratorRepository(ICollaboratorRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tenant_config(self, tenant_id: uuid.UUID) -> Optional[HrTenantConfig]:
        """Fetch custom validation rules for a specific tenant."""
        result = await self.db.execute(
            select(HrTenantConfig).where(HrTenantConfig.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    def _to_domain(self, orm: ORMCollaborator) -> Optional[DomainCollaborator]:
        if not orm: return None
        return DomainCollaborator(
            id=orm.id,
            company_id=orm.company_id,
            internal_id=orm.internal_id,
            full_name=orm.full_name,
            rfid_tag=orm.rfid_tag,
            pin_code=orm.pin_code,
            home_warehouse_id=orm.home_warehouse_id,
            is_supervisor=orm.is_supervisor,
            tenant_id=orm.tenant_id,
            photo_path=orm.photo_path
        )

    def _to_orm(self, domain: DomainCollaborator) -> ORMCollaborator:
        return ORMCollaborator(
            id=domain.id,
            company_id=domain.company_id,
            internal_id=domain.internal_id,
            full_name=domain.full_name,
            rfid_tag=domain.rfid_tag,
            pin_code=domain.pin_code,
            home_warehouse_id=domain.home_warehouse_id,
            is_supervisor=domain.is_supervisor,
            tenant_id=domain.tenant_id,
            photo_path=domain.photo_path
        )

    async def get_by_internal_id(self, internal_id: str, company_id: uuid.UUID) -> Optional[DomainCollaborator]:
        result = await self.db.execute(
            select(ORMCollaborator).where(
                and_(
                    ORMCollaborator.internal_id == internal_id,
                    ORMCollaborator.company_id == company_id
                )
            )
        )
        return self._to_domain(result.scalar_one_or_none())

    async def create(self, collaborator: DomainCollaborator) -> DomainCollaborator:
        orm = self._to_orm(collaborator)
        self.db.add(orm)
        await self.db.flush()
        return self._to_domain(orm)

    async def update(self, collaborator: DomainCollaborator) -> DomainCollaborator:
        # Simplified update (should merge in production)
        orm = await self.db.get(ORMCollaborator, collaborator.id)
        if orm:
            orm.full_name = collaborator.full_name
            orm.rfid_tag = collaborator.rfid_tag
            orm.pin_code = collaborator.pin_code
            orm.home_warehouse_id = collaborator.home_warehouse_id
            orm.is_supervisor = collaborator.is_supervisor
            orm.photo_path = collaborator.photo_path
            await self.db.flush()
        return self._to_domain(orm)

    async def list_all(self, company_id: uuid.UUID) -> List[DomainCollaborator]:
        result = await self.db.execute(
            select(ORMCollaborator).where(ORMCollaborator.company_id == company_id)
        )
        return [self._to_domain(o) for o in result.scalars().all()]
