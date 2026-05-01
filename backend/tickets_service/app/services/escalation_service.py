from typing import List
from uuid import UUID
from app.domain.ports.escalation_repository import IEscalationRepository
from app.models.escalation_rule import EscalationRule

class EscalationConfigService:
    """
    Servicio para gestionar la configuración de escalación Multi-tenant (Fase 7).
    """
    def __init__(self, repo: IEscalationRepository):
        self.repo = repo

    async def get_escalation_path(self, company_id: UUID, area: str) -> List[EscalationRule]:
        """
        Retorna la ruta de escalación para un ticket dado su área.
        Si el área no tiene reglas, cae en la configuración _default de la empresa.
        """
        return await self.repo.get_rules_by_area(company_id, area)

    async def seed_default_rules(self, company_id: UUID):
        """
        Puebla las reglas por defecto para una nueva empresa (Multi-tenant bootstrapping).
        """
        DEFAULT_MATRIX = {
            "Producción": [
                {"level": 1, "role": "Jefe de Turno",      "sla": 30},
                {"level": 2, "role": "Gerente de Área",     "sla": 60},
                {"level": 3, "role": "Gerente de Planta",   "sla": 120},
            ],
            "Almacén": [
                {"level": 1, "role": "Supervisor Almacén",  "sla": 45},
                {"level": 2, "role": "Gerente Logística",   "sla": 90},
                {"level": 3, "role": "Director Operaciones", "sla": 180},
            ],
            "Mantenimiento": [
                {"level": 1, "role": "Técnico Senior",      "sla": 20},
                {"level": 2, "role": "Jefe Mantenimiento",  "sla": 45},
                {"level": 3, "role": "Gerente de Planta",   "sla": 90},
            ],
            "Calidad": [
                {"level": 1, "role": "Inspector Calidad",   "sla": 30},
                {"level": 2, "role": "Supervisor Calidad",  "sla": 60},
                {"level": 3, "role": "Gerente de Calidad",  "sla": 120},
            ],
            "Soporte": [
                {"level": 1, "role": "Analista Soporte",    "sla": 60},
                {"level": 2, "role": "Coordinador IT",      "sla": 180},
                {"level": 3, "role": "Gerente IT",          "sla": 480},
            ],
            "Recursos Humanos": [
                {"level": 1, "role": "Generalista RH",      "sla": 120},
                {"level": 2, "role": "Jefe Personal",       "sla": 240},
                {"level": 3, "role": "Gerente RH",          "sla": 480},
            ],
            "_default": [
                {"level": 1, "role": "Supervisor",   "sla": 60},
                {"level": 2, "role": "Gerente",      "sla": 120},
                {"level": 3, "role": "Director",     "sla": 240},
            ],
        }

        await self.repo.delete_rules_by_company(company_id)
        
        for area, levels in DEFAULT_MATRIX.items():
            for rule in levels:
                await self.repo.create_rule(
                    company_id=company_id,
                    area=area,
                    level=rule["level"],
                    role_name=rule["role"],
                    sla_minutes=rule["sla"]
                )
