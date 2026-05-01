from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from app.models.escalation_rule import EscalationRule

class IEscalationRepository(ABC):
    @abstractmethod
    async def get_rules_by_area(self, company_id: UUID, area: str) -> List[EscalationRule]:
        """Retorna las reglas de escalación para un área específica."""
        pass

    @abstractmethod
    async def create_rule(self, company_id: UUID, area: str, level: int, role_name: str, sla_minutes: int) -> EscalationRule:
        """Crea una nueva regla de escalación."""
        pass

    @abstractmethod
    async def delete_rules_by_company(self, company_id: UUID):
        """Limpia reglas para una empresa (usado en seeding)."""
        pass
