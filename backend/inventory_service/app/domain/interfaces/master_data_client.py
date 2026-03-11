import uuid
from abc import ABC, abstractmethod

class IMasterDataClient(ABC):
    """
    Interface for interacting with Master Data Service.
    Defines the contract for product validation.
    """
    @abstractmethod
    async def validate_product(self, product_id: uuid.UUID, company_id: uuid.UUID) -> bool:
        """
        Checks if a product exists and is active in Master Data.
        """
        pass
