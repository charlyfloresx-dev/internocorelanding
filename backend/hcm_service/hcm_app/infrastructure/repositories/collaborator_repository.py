import uuid
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from hcm_app.domain.ports.collaborator_repository import ICollaboratorRepository
from hcm_app.domain.entities.collaborator_entities import Collaborator as DomainCollaborator
from hcm_app.models.collaborator import Collaborator as ORMCollaborator
from hcm_app.models.tenant_settings import HrTenantConfig

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
            is_supervisor=orm.supervisor_id is None,
            tenant_id=orm.tenant_id,
            photo_path=orm.photo_path,
            assigned_plant=orm.assigned_plant,
            shift=orm.shift,
            global_entry_id=orm.global_entry_id
        )

    def _to_orm(self, domain: DomainCollaborator) -> ORMCollaborator:
        parts = domain.full_name.split() if domain.full_name else []
        if len(parts) >= 3:
            first_name = " ".join(parts[:-2])
            last_name_paternal = parts[-2]
            last_name_maternal = parts[-1]
        elif len(parts) == 2:
            first_name = parts[0]
            last_name_paternal = parts[1]
            last_name_maternal = None
        else:
            first_name = parts[0] if parts else "Unknown"
            last_name_paternal = "Unknown"
            last_name_maternal = None

        return ORMCollaborator(
            id=domain.id,
            company_id=domain.company_id,
            internal_id=domain.internal_id,
            first_name=first_name,
            last_name_paternal=last_name_paternal,
            last_name_maternal=last_name_maternal,
            rfid_tag=domain.rfid_tag,
            pin_code=domain.pin_code,
            home_warehouse_id=domain.home_warehouse_id,
            supervisor_id=None if domain.is_supervisor else None,
            tenant_id=domain.tenant_id,
            photo_path=domain.photo_path,
            assigned_plant=domain.assigned_plant,
            shift=domain.shift,
            global_entry_id=domain.global_entry_id
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
        orm = await self.db.get(ORMCollaborator, collaborator.id)
        if orm:
            parts = collaborator.full_name.split() if collaborator.full_name else []
            if len(parts) >= 3:
                orm.first_name = " ".join(parts[:-2])
                orm.last_name_paternal = parts[-2]
                orm.last_name_maternal = parts[-1]
            elif len(parts) == 2:
                orm.first_name = parts[0]
                orm.last_name_paternal = parts[1]
                orm.last_name_maternal = None
            else:
                orm.first_name = parts[0] if parts else "Unknown"
                orm.last_name_paternal = "Unknown"
                orm.last_name_maternal = None

            orm.rfid_tag = collaborator.rfid_tag
            orm.pin_code = collaborator.pin_code
            orm.home_warehouse_id = collaborator.home_warehouse_id
            if collaborator.is_supervisor:
                orm.supervisor_id = None
            orm.photo_path = collaborator.photo_path
            orm.assigned_plant = collaborator.assigned_plant
            orm.shift = collaborator.shift
            orm.global_entry_id = collaborator.global_entry_id
            await self.db.flush()
        return self._to_domain(orm)

    async def list_all(self, company_id: uuid.UUID) -> List[DomainCollaborator]:
        result = await self.db.execute(
            select(ORMCollaborator).where(ORMCollaborator.company_id == company_id)
        )
        return [self._to_domain(o) for o in result.scalars().all()]
