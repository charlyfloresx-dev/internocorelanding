import uuid
from typing import List, Optional, Any
from master_app.domain.repositories.master_data_repository import IMasterDataRepository
from master_app.schemas.product_brand import BrandCreate, BrandUpdate


class ProductBrandService:
    def __init__(self, repo: IMasterDataRepository):
        self.repo = repo

    async def get_brands(self, company_id: uuid.UUID) -> List[Any]:
        return await self.repo.get_brands(company_id)

    async def get_brand_by_id(self, brand_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Any]:
        return await self.repo.get_brand_by_id(brand_id, company_id)

    async def create_brand(self, brand_in: BrandCreate, company_id: uuid.UUID) -> Any:
        return await self.repo.create_brand(brand_in.model_dump(), company_id)

    async def update_brand(self, brand_id: uuid.UUID, company_id: uuid.UUID, brand_in: BrandUpdate) -> Any:
        return await self.repo.update_brand(brand_id, company_id, brand_in.model_dump(exclude_unset=True))

    async def delete_brand(self, brand_id: uuid.UUID) -> None:
        await self.repo.delete_brand(brand_id)
