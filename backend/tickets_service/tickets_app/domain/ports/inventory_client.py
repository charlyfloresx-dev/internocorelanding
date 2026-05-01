from abc import ABC, abstractmethod
from uuid import UUID
from decimal import Decimal

class IInventoryClient(ABC):
    @abstractmethod
    async def record_consumption(
        self, 
        company_id: UUID, 
        resource_id: UUID, 
        warehouse_id: UUID, 
        quantity: Decimal, 
        reference: str,
        user_id: UUID
    ) -> bool:
        """
        Registra el consumo de un recurso en el Kardex (movimiento OUT).
        Incluye validación atómica: si falla, debe notificarlo para abortar la transacción.
        """
        pass
