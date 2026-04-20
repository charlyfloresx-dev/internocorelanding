import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.models.collaborator import Collaborator
from app.models.tenant_settings import HrTenantConfig

logger = logging.getLogger(__name__)


class CollaboratorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tenant_config(self, tenant_id: uuid.UUID) -> Optional[HrTenantConfig]:
        """Fetch custom validation rules for a specific tenant."""
        result = await self.db.execute(
            select(HrTenantConfig).where(HrTenantConfig.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_rfid(self, rfid_hash: str, company_id: Optional[uuid.UUID] = None) -> list[Collaborator]:
        """Find collaborators by their hashed RFID tag within a company scope or globally."""
        filters = [
            Collaborator.rfid_tag == rfid_hash,
            Collaborator.is_active == True,
        ]
        if company_id:
            filters.append(Collaborator.company_id == company_id)
            
        result = await self.db.execute(
            select(Collaborator).where(and_(*filters))
        )
        return list(result.scalars().all())

    async def get_by_id(self, collaborator_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Collaborator]:
        result = await self.db.execute(
            select(Collaborator).where(
                and_(
                    Collaborator.id == collaborator_id,
                    Collaborator.company_id == company_id,
                    Collaborator.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_just_by_id(self, collaborator_id: uuid.UUID) -> Optional[Collaborator]:
        """Fetch a collaborator by ID without company scope (internal use only, bypass_tenant)."""
        result = await self.db.execute(
            select(Collaborator).where(Collaborator.id == collaborator_id)
        )
        return result.scalar_one_or_none()

    async def get_by_internal_id(self, internal_id: str, company_id: Optional[uuid.UUID] = None) -> list[Collaborator]:
        """Find collaborators by their alphanumeric internal_id within a company scope or globally."""
        filters = [
            Collaborator.internal_id == internal_id,
            Collaborator.is_active == True,
        ]
        if company_id:
            filters.append(Collaborator.company_id == company_id)
            
        result = await self.db.execute(
            select(Collaborator).where(and_(*filters))
        )
        return list(result.scalars().all())

    async def create(self, collaborator: Collaborator) -> Collaborator:
        self.db.add(collaborator)
        await self.db.flush()
        await self.db.refresh(collaborator)
        return collaborator
