import uuid
from typing import List, Optional, Any
from master_app.domain.repositories.master_data_repository import IMasterDataRepository
from master_app.schemas.product_category import CategoryCreate, CategoryUpdate


class ProductCategoryService:
    def __init__(self, repo: IMasterDataRepository):
        self.repo = repo

    async def get_categories(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> List[Any]:
        return await self.repo.get_categories(company_id, group_id)

    async def get_category_by_id(self, category_id: uuid.UUID, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> Optional[Any]:
        return await self.repo.get_category_by_id(category_id, company_id, group_id)

    async def create_category(self, category_in: CategoryCreate, company_id: uuid.UUID) -> Any:
        return await self.repo.create_category(category_in.model_dump(), company_id)

    async def update_category(self, category_id: uuid.UUID, company_id: uuid.UUID, category_in: CategoryUpdate) -> Any:
        return await self.repo.update_category(category_id, company_id, category_in.model_dump(exclude_unset=True))

    async def delete_category(self, category_id: uuid.UUID) -> None:
        await self.repo.delete_category(category_id)
