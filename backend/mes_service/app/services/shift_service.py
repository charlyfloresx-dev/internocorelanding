import uuid
from datetime import datetime, time, timedelta
from typing import Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.shift import Shift
from app.models.resource import Resource

class ShiftService:
    """
    Servicio de resolución jerárquica de turnos (AL-005).
    Recurso > Planta > Empresa.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_shift(self, resource_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Shift]:
        """
        Resuelve el turno activo para un recurso siguiendo la jerarquía.
        """
        # 1. Buscar en el Recurso
        shift = await self._resolve_shift(resource_id=resource_id)
        if shift: return shift
        
        # 2. Buscar en la Planta (Facility)
        resource = await self.db.get(Resource, resource_id)
        if resource and resource.area:
            shift = await self._resolve_shift(facility_id=resource.area.facility_id)
            if shift: return shift
            
        # 3. Buscar a nivel Empresa (Global)
        shift = await self._resolve_shift(company_id=company_id, resource_id=None, facility_id=None)
        return shift

    async def _resolve_shift(self, **kwargs) -> Optional[Shift]:
        """Busca el turno que coincide con la hora actual según los criterios."""
        now_time = datetime.now().time()
        
        query = select(Shift).where(Shift.is_active == True)
        if "resource_id" in kwargs:
            query = query.where(Shift.resource_id == kwargs["resource_id"])
        if "facility_id" in kwargs:
            query = query.where(Shift.facility_id == kwargs["facility_id"])
        if "company_id" in kwargs:
            query = query.where(Shift.company_id == kwargs["company_id"])
            
        result = await self.db.execute(query)
        shifts = result.scalars().all()
        
        for s in shifts:
            if self.is_time_in_shift(now_time, s.start_time, s.end_time, s.is_overnight):
                return s
        return None

    @staticmethod
    def is_time_in_shift(check_time: time, start: time, end: time, is_overnight: bool) -> bool:
        """Determina si una hora está dentro del rango del turno (Cruce de medianoche)."""
        if not is_overnight:
            return start <= check_time <= end
        else:
            # Caso medianoche: 22:00 a 06:00
            return check_time >= start or check_time <= end

    async def get_shift_by_id(self, shift_id: uuid.UUID) -> Optional[Shift]:
        return await self.db.get(Shift, shift_id)
