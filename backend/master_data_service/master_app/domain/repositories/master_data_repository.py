import uuid
from abc import ABC, abstractmethod
from typing import List, Optional, Any


class IMasterDataRepository(ABC):
    """
    Abstract repository interface for Master Data operations.
    All SQLAlchemy logic must be in the infrastructure implementation.
    """

    # --- Product ---
    @abstractmethod
    async def get_products(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None, q: Optional[str] = None, warehouse_id: Optional[uuid.UUID] = None) -> List[Any]:
        ...

    @abstractmethod
    async def get_product_by_id(self, product_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Any]:
        ...

    @abstractmethod
    async def create_product(self, product_data: dict, version_data: dict) -> Any:
        ...

    @abstractmethod
    async def approve_version(self, product_id: uuid.UUID, version_number: int, company_id: uuid.UUID) -> Any:
        ...

    @abstractmethod
    async def update_product(self, product_id: uuid.UUID, company_id: uuid.UUID, update_data: dict) -> Any:
        ...

    @abstractmethod
    async def delete_product(self, product_id: uuid.UUID, company_id: uuid.UUID) -> None:
        ...

    # --- Brand ---
    @abstractmethod
    async def get_brands(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> List[Any]:
        ...

    @abstractmethod
    async def get_brand_by_id(self, brand_id: uuid.UUID, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> Optional[Any]:
        ...

    @abstractmethod
    async def create_brand(self, brand_data: dict, company_id: uuid.UUID) -> Any:
        ...

    @abstractmethod
    async def update_brand(self, brand_id: uuid.UUID, company_id: uuid.UUID, update_data: dict) -> Any:
        ...

    @abstractmethod
    async def delete_brand(self, brand_id: uuid.UUID, company_id: uuid.UUID) -> None:
        ...

    # --- Category ---
    @abstractmethod
    async def get_categories(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> List[Any]:
        ...

    @abstractmethod
    async def get_category_by_id(self, category_id: uuid.UUID, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> Optional[Any]:
        ...

    @abstractmethod
    async def create_category(self, category_data: dict, company_id: uuid.UUID) -> Any:
        ...

    @abstractmethod
    async def update_category(self, category_id: uuid.UUID, company_id: uuid.UUID, update_data: dict) -> Any:
        ...

    @abstractmethod
    async def delete_category(self, category_id: uuid.UUID, company_id: uuid.UUID) -> None:
        ...

    # --- UOM ---
    @abstractmethod
    async def get_uoms(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> List[Any]:
        ...

    @abstractmethod
    async def get_uom_by_id(self, uom_id: uuid.UUID, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> Optional[Any]:
        ...

    @abstractmethod
    async def create_uom(self, uom_data: dict, company_id: uuid.UUID) -> Any:
        ...

    @abstractmethod
    async def update_uom(self, uom_id: uuid.UUID, company_id: uuid.UUID, update_data: dict) -> Any:
        ...

    @abstractmethod
    async def delete_uom(self, uom_id: uuid.UUID, company_id: uuid.UUID) -> None:
        ...

    # --- Movement Concepts ---
    @abstractmethod
    async def get_concepts(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None, type: Optional[str] = None) -> List[Any]:
        ...

    # --- Sync ---
    @abstractmethod
    async def get_all_master_data(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> dict:
        ...

    # --- Product Price ---
    @abstractmethod
    async def upsert_product_price(self, price_data: dict, company_id: uuid.UUID) -> Any:
        ...

    @abstractmethod
    async def get_product_prices(self, product_id: uuid.UUID, company_id: uuid.UUID) -> List[Any]:
        ...
