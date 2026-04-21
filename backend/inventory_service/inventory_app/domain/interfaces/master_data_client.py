import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, List

class IMasterDataClient(ABC):
    """
    Interface for interacting with Master Data Service.
    Defines the contract for product validation.
    """
    @abstractmethod
    async def get_uom_factor(self, uom_id: uuid.UUID, company_id: uuid.UUID) -> Decimal:
        """
        Retrieves the conversion factor for a specific UOM.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_location_capacity(self, warehouse_id: uuid.UUID, location_code: str, company_id: uuid.UUID) -> Decimal:
        """
        [Phase 63] Retrieves structural capacity for a location.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_product_internal_metadata(self, product_id: uuid.UUID, company_id: uuid.UUID, trace_id: Optional[str] = None) -> dict:
        """
        Retrieves product name and metadata from internal master data endpoint.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_warehouse(self, warehouse_id: uuid.UUID, company_id: uuid.UUID) -> dict:
        """
        Retrieves warehouse details from Master Data.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_partner(self, partner_id: uuid.UUID, company_id: uuid.UUID) -> dict:
        """
        Retrieves business partner (Supplier/Customer) details from Master Data.
        """
        raise NotImplementedError()

    @abstractmethod
    async def list_warehouses(self, company_id: uuid.UUID) -> List[dict]:
        """
        Lists all warehouses for a company from Master Data.
        """
        raise NotImplementedError()

    @abstractmethod
    async def check_uom_readiness(self, company_id: uuid.UUID) -> bool:
        """
        Checks if the company has basic UOMs configured.
        """
        raise NotImplementedError()

    @abstractmethod
    async def check_product_readiness(self, company_id: uuid.UUID) -> bool:
        """
        Checks if the company has products registered.
        """
        raise NotImplementedError()

    @abstractmethod
    async def check_pricing_readiness(self, company_id: uuid.UUID) -> bool:
        """
        Checks if the company has at least some prices configured.
        """
        raise NotImplementedError()

