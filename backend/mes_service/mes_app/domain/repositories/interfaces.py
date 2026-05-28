import uuid
from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal

class IProductionRunRepository(ABC):
    @abstractmethod
    async def get_by_id(self, run_id: uuid.UUID) -> Any:
        pass

class IManufacturingLedgerRepository(ABC):
    @abstractmethod
    async def create(self, **kwargs) -> Any:
        pass

    @abstractmethod
    async def get_total_produced(self, run_id: uuid.UUID) -> float:
        pass
    
    @abstractmethod
    async def get_produced_in_slot(self, run_id: uuid.UUID, start: datetime, end: datetime) -> float:
        pass

class IDowntimeRepository(ABC):
    @abstractmethod
    async def get_by_run_id(self, run_id: uuid.UUID) -> List[Any]:
        pass
    
    @abstractmethod
    async def get_active_downtime(self, run_id: uuid.UUID) -> Optional[Any]:
        pass

class ILaborRepository(ABC):
    @abstractmethod
    async def get_by_run_id(self, run_id: uuid.UUID) -> List[Any]:
        pass
    
    @abstractmethod
    async def get_active_count_at(self, run_id: uuid.UUID, timestamp: datetime) -> int:
        pass

class IGoalRepository(ABC):
    @abstractmethod
    async def get_hour_meta(self, resource_id: uuid.UUID, hour: int) -> int:
        pass

class IShiftRepository(ABC):
    @abstractmethod
    async def get_by_id(self, shift_id: uuid.UUID) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def get_active_shifts_by_criteria(self, **kwargs) -> List[Any]:
        pass

class IResourceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, resource_id: uuid.UUID) -> Optional[Any]:
        pass

class IWMSClient(ABC):
    @abstractmethod
    async def check_stock(self, sku: str, company_id: str) -> Dict[str, Any]:
        pass


class IWorkOrderRepository(ABC):
    """Updates WorkOrder progress counters when a scan is recorded."""

    @abstractmethod
    async def increment_manufactured_quantity(
        self,
        work_order_id: uuid.UUID,
        qty: "Decimal",
        company_id: uuid.UUID,
    ) -> None:
        """
        Atomically increments WorkOrder.manufactured_quantity and the
        PLANNED_OUTPUT line's actual_quantity.  Also drives status transitions:
          DRAFT → IN_PROGRESS (on first scan)
          IN_PROGRESS → COMPLETED (when manufactured_quantity >= order_quantity)
        """
        pass
