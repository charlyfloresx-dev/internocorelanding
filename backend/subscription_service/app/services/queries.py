import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subscription import Entitlement

class GetEntitlementsQuery:
    @staticmethod
    async def execute(db: AsyncSession, company_id: uuid.UUID):
        # Query optimizada para el SSOT de accesos
        result = await db.execute(
            select(Entitlement.module_code)
            .where(Entitlement.company_id == company_id)
            .where(Entitlement.is_enabled == True)
        )
        return [row[0] for row in result.all()]
