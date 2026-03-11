import uuid
from abc import ABC, abstractmethod
from typing import List, Optional, Any


class ISubscriptionRepository(ABC):
    """
    Abstract repository interface for Subscription operations.
    """

    @abstractmethod
    async def get_subscription_by_company(self, company_id: uuid.UUID) -> Optional[Any]:
        ...

    @abstractmethod
    async def get_plan_by_stripe_product(self, stripe_product_id: str) -> Optional[Any]:
        ...

    @abstractmethod
    async def create_subscription(self, subscription_data: dict) -> Any:
        ...

    @abstractmethod
    async def update_subscription(self, stripe_subscription_id: str, update_data: dict) -> Any:
        ...

    @abstractmethod
    async def get_active_plans(self) -> List[Any]:
        ...

    @abstractmethod
    async def get_entitlements_by_company(self, company_id: uuid.UUID) -> List[Any]:
        ...

    @abstractmethod
    async def get_subscription_by_company_and_version(self, company_id: uuid.UUID, version_id: int) -> Optional[Any]:
        ...

    @abstractmethod
    async def check_active_users_for_module(self, company_id: uuid.UUID, module_code: str) -> bool:
        ...

    @abstractmethod
    async def upsert_entitlement(self, company_id: uuid.UUID, module_code: str, is_enabled: bool, subscription_id: uuid.UUID) -> None:
        ...

    @abstractmethod
    async def update_subscription_status(self, company_id: uuid.UUID, new_status: str) -> None:
        ...

    @abstractmethod
    async def extend_grace_period(self, company_id: uuid.UUID, days: int) -> Any:
        ...

    @abstractmethod
    async def save_audit_log(self, audit_data: dict) -> None:
        ...
