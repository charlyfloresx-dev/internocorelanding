from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.ports.escalation_repository import IEscalationRepository
from app.models.escalation_rule import EscalationRule

class SQLAlchemyEscalationRepository(IEscalationRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_rules_by_area(self, company_id: UUID, area: str) -> List[EscalationRule]:
        # Intentar obtener reglas específicas del área
        stmt = select(EscalationRule).where(
            EscalationRule.company_id == company_id,
            EscalationRule.area == area
        ).order_by(EscalationRule.level)
        
        result = await self._session.execute(stmt)
        rules = result.scalars().all()
        
        # Si no hay reglas para el área, retornar las de _default
        if not rules and area != "_default":
            stmt_default = select(EscalationRule).where(
                EscalationRule.company_id == company_id,
                EscalationRule.area == "_default"
            ).order_by(EscalationRule.level)
            result_default = await self._session.execute(stmt_default)
            rules = result_default.scalars().all()
            
        return rules

    async def create_rule(self, company_id: UUID, area: str, level: int, role_name: str, sla_minutes: int) -> EscalationRule:
        rule = EscalationRule(
            company_id=company_id,
            tenant_id=company_id,  # Multi-tenant constraint
            area=area,
            level=level,
            role_name=role_name,
            sla_minutes=sla_minutes
        )
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def delete_rules_by_company(self, company_id: UUID):
        stmt = delete(EscalationRule).where(EscalationRule.company_id == company_id)
        await self._session.execute(stmt)
        await self._session.flush()
