import uuid
from typing import List, Optional, Any
from app.domain.repositories.master_data_repository import IMasterDataRepository
from app.schemas.uom import UOMCreate


class UOMService:
    def __init__(self, repo: IMasterDataRepository):
        self.repo = repo

    async def get_uoms_by_company(self, company_id: uuid.UUID) -> List[Any]:
        return await self.repo.get_uoms(company_id)

    async def get_uom_by_id(self, uom_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Any]:
        return await self.repo.get_uom_by_id(uom_id, company_id)

    async def create_uom(self, uom_in: UOMCreate, company_id: uuid.UUID) -> Any:
        return await self.repo.create_uom(uom_in.model_dump(), company_id)