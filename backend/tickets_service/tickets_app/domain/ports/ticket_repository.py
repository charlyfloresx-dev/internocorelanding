from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from uuid import UUID
import uuid


class ITicketRepository(ABC):
    """
    Puerto de dominio para persistencia de Tickets.
    Los servicios SOLO deben depender de esta interfaz, nunca de SQLAlchemy directamente.
    """

    @abstractmethod
    async def get_tickets_for_escalation(self) -> List["Ticket"]:  # noqa: F821
        """
        Retorna tickets activos (no resueltos/cerrados) para revisión de SLA.
        Este método es de orquestación global (bypass_tenant).
        """
        ...

    @abstractmethod
    async def get_active_by_station(self, station_id: UUID, company_id: UUID) -> List["Ticket"]:  # noqa: F821
        """Obtiene tickets activos asociados a una estación MES."""
        ...

    @abstractmethod
    async def create(self, data: dict) -> "Ticket":  # noqa: F821
        """Crea un ticket y lo persiste. Maneja commit/flush internamente."""
        ...

    @abstractmethod
    async def get_by_id(self, ticket_id: UUID, company_id: UUID) -> Optional["Ticket"]:  # noqa: F821
        """Obtiene un ticket por ID con filtro multi-tenant."""
        ...

    @abstractmethod
    async def list_by_company(self, company_id: UUID) -> List["Ticket"]:  # noqa: F821
        """Lista todos los tickets activos de una empresa."""
        ...

    @abstractmethod
    async def list_by_visibility(
        self, company_id: UUID, user_id: UUID, is_admin: bool, is_supervisor: bool, department_area: Optional[str] = None
    ) -> List["Ticket"]:  # noqa: F821
        """Lista tickets aplicando reglas jerárquicas de visibilidad."""
        ...

    @abstractmethod
    async def update(self, ticket_id: UUID, company_id: UUID, data: dict) -> Optional["Ticket"]:  # noqa: F821
        """Actualiza campos de un ticket. Maneja commit internamente."""
        ...

    @abstractmethod
    async def soft_delete(self, ticket_id: UUID, company_id: UUID) -> Optional["Ticket"]:  # noqa: F821
        """Marca un ticket como inactivo (soft delete)."""
        ...

    @abstractmethod
    async def count_by_company_year(self, company_id: UUID, year: int) -> int:
        """Cuenta tickets de un año para generar folio TKT-YYYY-NNNN."""
        ...

    @abstractmethod
    async def add_history_entry(self, ticket_id: UUID, company_id: UUID, change_type: str, old_value: Optional[str], new_value: str, changed_by_id: UUID) -> None:
        """Agrega una entrada al historial del ticket."""
        ...

    @abstractmethod
    async def add_comment(self, ticket_id: UUID, company_id: UUID, content: str, author_id: UUID) -> "TicketComment":  # noqa: F821
        """Agrega un comentario a un ticket."""
        ...

    @abstractmethod
    async def get_by_dedup_hash(self, dedup_hash: str, company_id: UUID) -> Optional["Ticket"]:  # noqa: F821
        """Busca un ticket OPEN/IN_PROGRESS por su hash de deduplicación."""
        ...

    @abstractmethod
    async def add_outbox_event(self, company_id: UUID, event_type: str, payload: str) -> None:
        """Persiste un evento en el Outbox para entrega garantizada."""
        ...

    @abstractmethod
    async def get_technician_workload(self, company_id: UUID) -> dict:
        """Retorna un mapa de {user_id: count} con la carga de tickets activos."""
        ...
