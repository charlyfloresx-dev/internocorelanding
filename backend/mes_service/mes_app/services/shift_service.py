import uuid
from datetime import datetime, time, timedelta
from typing import Optional, List, Any
from mes_app.domain.repositories.interfaces import IShiftRepository, IResourceRepository

class ShiftService:
    """
    Servicio de resolución jerárquica de turnos (AL-005).
    Shielded from SQLAlchemy.
    """
    
    def __init__(self, shift_repo: IShiftRepository, resource_repo: IResourceRepository):
        self.shift_repo = shift_repo
        self.resource_repo = resource_repo

    async def get_active_shift(self, resource_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Any]:
        # 1. Buscar en el Recurso
        shift = await self._resolve_shift(resource_id=resource_id)
        if shift: return shift
        
        # 2. Buscar en la Planta (Facility)
        resource = await self.resource_repo.get_by_id(resource_id)
        if resource and resource.area:
            shift = await self._resolve_shift(facility_id=resource.area.facility_id)
            if shift: return shift
            
        # 3. Buscar a nivel Empresa (Global)
        shift = await self._resolve_shift(company_id=company_id)
        return shift

    async def _resolve_shift(self, **kwargs) -> Optional[Any]:
        now_time = datetime.now().time()
        shifts = await self.shift_repo.get_active_shifts_by_criteria(**kwargs)
        
        for s in shifts:
            if self.is_time_in_shift(now_time, s.start_time, s.end_time, s.is_overnight):
                return s
        return None

    @staticmethod
    def is_time_in_shift(check_time: time, start: time, end: time, is_overnight: bool) -> bool:
        if not is_overnight:
            return start <= check_time <= end
        else:
            return check_time >= start or check_time <= end

    async def get_shift_by_id(self, shift_id: uuid.UUID) -> Optional[Any]:
        return await self.shift_repo.get_by_id(shift_id)
