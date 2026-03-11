import uuid
from typing import Any
from app.domain.repositories.master_data_repository import IMasterDataRepository
from app.schemas.sync import MasterDataSyncResponse


class SyncService:
    def __init__(self, repo: IMasterDataRepository):
        self.repo = repo

    async def get_all_master_data(self, company_id: uuid.UUID) -> MasterDataSyncResponse:
        data = await self.repo.get_all_master_data(company_id)
        return MasterDataSyncResponse(products=data["products"], uoms=data["uoms"])