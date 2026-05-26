import uuid
from datetime import datetime, time, timedelta
from typing import Optional, Any
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
        # 1. Turno asignado al recurso específico
        shift = await self._resolve_shift(resource_id=resource_id)
        if shift:
            return shift

        # 2. Turno a nivel instalación (Facility)
        resource = await self.resource_repo.get_by_id(resource_id)
        if resource and resource.area:
            shift = await self._resolve_shift(facility_id=resource.area.facility_id)
            if shift:
                return shift

        # 3. Turno a nivel empresa (Global)
        return await self._resolve_shift(company_id=company_id)

    async def _resolve_shift(self, **kwargs) -> Optional[Any]:
        now_time = datetime.now().time()
        shifts = await self.shift_repo.get_active_shifts_by_criteria(**kwargs)
        for s in shifts:
            if self.is_time_in_shift(now_time, s.start_time, s.end_time, s.is_overnight):
                return s
        return None

    async def get_shift_by_id(self, shift_id: uuid.UUID) -> Optional[Any]:
        return await self.shift_repo.get_by_id(shift_id)

    # ── Static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def is_time_in_shift(check_time: time, start: time, end: time, is_overnight: bool) -> bool:
        if not is_overnight:
            return start <= check_time <= end
        # Overnight: valid if after start OR before end (crosses midnight)
        return check_time >= start or check_time <= end

    @staticmethod
    def calculate_available_minutes(shift: Any) -> float:
        """
        Net productive minutes for a shift = gross duration − break_minutes.

        Overnight arithmetic (legacy: if End < Start → 24h − Start + End):
          T1 08:00 → 16:30 = 510 min gross
          T2 16:30 → 01:45 = (24×60 − 990) + 105 = 555 min gross
        Both are then reduced by shift.break_minutes (default 60).
        """
        start_m = shift.start_time.hour * 60 + shift.start_time.minute
        end_m = shift.end_time.hour * 60 + shift.end_time.minute

        if shift.is_overnight or end_m <= start_m:
            gross_minutes = (24 * 60 - start_m) + end_m
        else:
            gross_minutes = end_m - start_m

        break_mins = getattr(shift, 'break_minutes', 60)
        return max(0.0, gross_minutes - break_mins)
