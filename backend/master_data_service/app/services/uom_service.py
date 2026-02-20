import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select

# 1. Asegúrate de que el nombre coincida con el archivo y la clase
from app.models.uom import UOM 
from app.schemas.uom import UOMCreate, UOMUpdate

class UOMService:
    @staticmethod
    async def get_uoms_by_company(db: AsyncSession, *, company_id: uuid.UUID) -> List[UOM]:
        # El uso de or_ es vital para los catálogos base de Interno Core
        stmt = select(UOM).where(
            or_(UOM.company_id == None, UOM.company_id == company_id)
        ).order_by(UOM.name)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_uom_by_id(db: AsyncSession, *, uom_id: uuid.UUID, company_id: uuid.UUID) -> Optional[UOM]:
        # Protegemos que no pueda ver/editar UOMs de otras empresas
        stmt = select(UOM).where(
            UOM.id == uom_id,
            or_(UOM.company_id == None, UOM.company_id == company_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def create_uom(db: AsyncSession, *, uom_in: UOMCreate, company_id: uuid.UUID) -> UOM:
        # Inyectamos el ID de la empresa del contexto actual
        db_obj = UOM(
            company_id=company_id,
            **uom_in.model_dump()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # Los métodos update y delete están impecables.