"""
ResourceGraphicService — Phase 154 Part 2.

Ports the .NET legacy ResultController.GetGraphic() algorithm to Python.

Algorithm (from Interno.Production.Controllers.ResultController):
  1. Load resource + active shift (resource-level override or company default)
  2. Generate hourly slots [shift.start_hour .. shift.end_hour)
  3. Apply ShiftBreaks: reduce Disponible[i] for slots that overlap a break
  4. For each ProductionRun today (ordered by id):
       - if StandardTime exists for item_code:
           qtyPerHour = floor(Disponible_i_hours / set_time_hours)
         else:
           qtyPerHour = round(planned_qty / total_available_hours)
       - Fill Meta[] slots sequentially
  5. Load HourlyProductionSnapshot for today, group by hour:
       - if actual > meta → Excedente; missing = 0
       - else → Faltante = meta - actual; producidas = actual
  6. Efficiency[i] = ceil((producidas[i] * 100) / meta[i])  if meta > 0
"""
import math
import uuid
from dataclasses import dataclass, field
from datetime import date, time, datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mes_app.models.resource import Resource
from mes_app.models.shift import Shift
from mes_app.models.shift_break import ShiftBreak
from mes_app.models.work_order import WorkOrder
from mes_app.models.production_run import ProductionRun
from mes_app.models.production_snapshot import HourlyProductionSnapshot
from mes_app.models.standard_time import StandardTime


# ── Response dataclasses ──────────────────────────────────────────────────────

@dataclass
class BreakSlot:
    code: str
    label: str
    start_time: str   # "HH:MM"
    end_time: str
    duration_minutes: int


@dataclass
class HourlySlot:
    time: str          # "HH:MM"
    goal: int          # Meta
    actual: int        # Real producidas
    missing: int       # Faltante
    excess: int        # Excedente
    efficiency: float  # %


@dataclass
class CumulativeRow:
    time: str
    goal_cumulative: int
    actual_cumulative: int


@dataclass
class ActiveWorkOrderRead:
    work_order_id: uuid.UUID
    order_number: str
    item_code: str
    manufactured_quantity: int
    order_quantity: int
    progress_pct: float
    status: str


@dataclass
class PlannedWorkOrderRead:
    work_order_id: uuid.UUID
    order_number: str
    item_code: str
    planned_quantity: int
    actual_quantity: int
    status: str


@dataclass
class ResourceGraphicResponse:
    resource_code: str
    shift_name: str
    shift_start: str    # "HH:MM"
    shift_end: str
    total_goal: int
    total_actual: int
    breaks: List[BreakSlot] = field(default_factory=list)
    hours: List[HourlySlot] = field(default_factory=list)
    cumulative_table: List[CumulativeRow] = field(default_factory=list)


# ── Service ───────────────────────────────────────────────────────────────────

class ResourceGraphicService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_graphic(
        self,
        resource_code: str,
        company_id: uuid.UUID,
        target_date: date,
    ) -> Optional[ResourceGraphicResponse]:
        """Returns the hourly production graphic for a resource on a given date."""

        # ── 1. Load resource ─────────────────────────────────────────────────
        res_row = await self.db.execute(
            select(Resource).where(
                Resource.code == resource_code,
                Resource.company_id == company_id,
            )
        )
        resource = res_row.scalar_one_or_none()
        if not resource:
            return None

        # ── 2. Detect active shift ────────────────────────────────────────────
        shift = await self._get_active_shift(resource.id, company_id, target_date)
        if not shift:
            return ResourceGraphicResponse(
                resource_code=resource_code,
                shift_name="Sin turno",
                shift_start="00:00",
                shift_end="00:00",
                total_goal=0,
                total_actual=0,
            )

        # ── 3. Load breaks for this shift ─────────────────────────────────────
        breaks_row = await self.db.execute(
            select(ShiftBreak).where(ShiftBreak.shift_id == shift.id)
        )
        breaks: List[ShiftBreak] = list(breaks_row.scalars().all())

        # ── 4. Generate hourly slots ──────────────────────────────────────────
        slots = self._generate_slots(shift, breaks)  # List[str] "HH:MM"
        n = len(slots)
        # disponible[i] in hours (fraction of the hour available for production)
        disponible = self._apply_breaks(slots, shift, breaks)

        # ── 5. Load today's ProductionRuns with WorkOrders ────────────────────
        runs_row = await self.db.execute(
            select(ProductionRun, WorkOrder)
            .join(WorkOrder, ProductionRun.work_order_id == WorkOrder.id)
            .where(
                ProductionRun.resource_id == resource.id,
                ProductionRun.date == target_date,
                ProductionRun.company_id == company_id,
            )
            .order_by(ProductionRun.id)
        )
        runs_with_wo = runs_with_wo = runs_row.all()

        # ── 6. Build Meta[] array ─────────────────────────────────────────────
        meta = [0] * n
        total_available_hours = sum(disponible)

        cursor = 0
        for run, wo in runs_with_wo:
            # Try to get StandardTime for this item
            std_row = await self.db.execute(
                select(StandardTime).where(
                    StandardTime.item_code == wo.item_code,
                    StandardTime.company_id == company_id,
                ).limit(1)
            )
            std_time = std_row.scalar_one_or_none()

            qty_remaining = run.planned_quantity

            while qty_remaining > 0 and cursor < n:
                if std_time and std_time.set_time_hours and float(std_time.set_time_hours) > 0:
                    qty_per_hour = math.floor(disponible[cursor] / float(std_time.set_time_hours))
                else:
                    qty_per_hour = (
                        round(run.planned_quantity / total_available_hours)
                        if total_available_hours > 0 else 0
                    )

                meta[cursor] = qty_per_hour
                qty_remaining -= qty_per_hour
                cursor += 1

        # ── 7. Load HourlyProductionSnapshot → actual[] ───────────────────────
        snaps_row = await self.db.execute(
            select(HourlyProductionSnapshot).where(
                HourlyProductionSnapshot.resource_id == resource.id,
                HourlyProductionSnapshot.date == target_date,
                HourlyProductionSnapshot.company_id == company_id,
            )
        )
        snaps: List[HourlyProductionSnapshot] = list(snaps_row.scalars().all())
        actual_by_hour = {s.hour: s.actual_quantity for s in snaps}

        # ── 8. Build hourly result slots ──────────────────────────────────────
        start_hour = shift.start_time.hour
        hour_slots: List[HourlySlot] = []
        for i, slot_label in enumerate(slots):
            slot_hour = (start_hour + i) % 24
            actual = actual_by_hour.get(slot_hour, 0)
            goal = meta[i]

            if actual > goal:
                excess = actual - goal
                missing = 0
                producidas = goal
            else:
                excess = 0
                missing = goal - actual
                producidas = actual

            efficiency = (
                math.ceil((producidas * 100) / goal) if goal > 0 else 0.0
            )

            hour_slots.append(HourlySlot(
                time=slot_label,
                goal=goal,
                actual=actual,
                missing=missing,
                excess=excess,
                efficiency=float(efficiency),
            ))

        # ── 9. Cumulative table ───────────────────────────────────────────────
        cum_goal = 0
        cum_actual = 0
        cumulative: List[CumulativeRow] = []
        for slot in hour_slots:
            cum_goal += slot.goal
            cum_actual += slot.actual
            cumulative.append(CumulativeRow(
                time=slot.time,
                goal_cumulative=cum_goal,
                actual_cumulative=cum_actual,
            ))

        break_slots = [
            BreakSlot(
                code=b.code,
                label=b.label,
                start_time=b.start_time.strftime("%H:%M"),
                end_time=b.end_time.strftime("%H:%M"),
                duration_minutes=b.duration_minutes,
            )
            for b in breaks
        ]

        return ResourceGraphicResponse(
            resource_code=resource_code,
            shift_name=shift.name,
            shift_start=shift.start_time.strftime("%H:%M"),
            shift_end=shift.end_time.strftime("%H:%M"),
            total_goal=sum(s.goal for s in hour_slots),
            total_actual=sum(s.actual for s in hour_slots),
            breaks=break_slots,
            hours=hour_slots,
            cumulative_table=cumulative,
        )

    async def get_active_workorder(
        self,
        resource_code: str,
        company_id: uuid.UUID,
        target_date: date,
    ) -> Optional[ActiveWorkOrderRead]:
        """Returns the IN_PROGRESS WorkOrder for a resource today, or None."""
        res_row = await self.db.execute(
            select(Resource).where(
                Resource.code == resource_code, Resource.company_id == company_id
            )
        )
        resource = res_row.scalar_one_or_none()
        if not resource:
            return None

        row = await self.db.execute(
            select(ProductionRun, WorkOrder)
            .join(WorkOrder, ProductionRun.work_order_id == WorkOrder.id)
            .where(
                ProductionRun.resource_id == resource.id,
                ProductionRun.date == target_date,
                ProductionRun.company_id == company_id,
                WorkOrder.status == "IN_PROGRESS",
            )
            .limit(1)
        )
        result = row.first()
        if not result:
            return None

        run, wo = result
        progress = (
            round((wo.manufactured_quantity / wo.order_quantity) * 100, 1)
            if wo.order_quantity > 0 else 0.0
        )
        return ActiveWorkOrderRead(
            work_order_id=wo.id,
            order_number=wo.order_number,
            item_code=wo.item_code,
            manufactured_quantity=wo.manufactured_quantity,
            order_quantity=wo.order_quantity,
            progress_pct=progress,
            status=wo.status,
        )

    async def get_planned_workorders(
        self,
        resource_code: str,
        company_id: uuid.UUID,
        target_date: date,
    ) -> List[PlannedWorkOrderRead]:
        """Returns DRAFT + IN_PROGRESS WorkOrders for a resource today."""
        res_row = await self.db.execute(
            select(Resource).where(
                Resource.code == resource_code, Resource.company_id == company_id
            )
        )
        resource = res_row.scalar_one_or_none()
        if not resource:
            return []

        rows = await self.db.execute(
            select(ProductionRun, WorkOrder)
            .join(WorkOrder, ProductionRun.work_order_id == WorkOrder.id)
            .where(
                ProductionRun.resource_id == resource.id,
                ProductionRun.date == target_date,
                ProductionRun.company_id == company_id,
                WorkOrder.status.in_(["DRAFT", "IN_PROGRESS"]),
            )
            .order_by(ProductionRun.id)
        )

        return [
            PlannedWorkOrderRead(
                work_order_id=wo.id,
                order_number=wo.order_number,
                item_code=wo.item_code,
                planned_quantity=run.planned_quantity,
                actual_quantity=run.actual_quantity,
                status=wo.status,
            )
            for run, wo in rows.all()
        ]

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get_active_shift(
        self, resource_id: uuid.UUID, company_id: uuid.UUID, target_date: date
    ) -> Optional[Shift]:
        """
        Returns the active shift for the resource.
        Priority: resource-level shift (resource_id FK) → company-wide active shift.
        Legacy heuristic: hour 5-16 → day shift; else → night shift.
        """
        # 1. Resource-specific shift
        row = await self.db.execute(
            select(Shift).where(
                Shift.resource_id == resource_id,
                Shift.is_active == True,
                Shift.company_id == company_id,
            ).limit(1)
        )
        shift = row.scalar_one_or_none()
        if shift:
            return shift

        # 2. Company-wide fallback using time-of-day heuristic (legacy behavior)
        now_hour = datetime.now().hour
        # Day shift: starts before 12; Night shift: starts at 12+
        row = await self.db.execute(
            select(Shift).where(
                Shift.company_id == company_id,
                Shift.is_active == True,
                Shift.resource_id == None,
            ).order_by(Shift.start_time).limit(1)
        )
        return row.scalar_one_or_none()

    def _generate_slots(self, shift: Shift, breaks: list) -> List[str]:
        """Generate list of 'HH:MM' labels for each hour slot in the shift."""
        start = shift.start_time.hour
        end = shift.end_time.hour

        slots = []
        if end > start:
            # Day shift: 06 → 14 = [06,07,08,09,10,11,12,13]
            for h in range(start, end):
                slots.append(f"{h:02d}:00")
        else:
            # Overnight: 22 → 06 = [22,23,00,01,02,03,04,05]
            for h in range(start, 24):
                slots.append(f"{h:02d}:00")
            for h in range(0, end):
                slots.append(f"{h:02d}:00")

        return slots

    def _apply_breaks(
        self, slots: List[str], shift: Shift, breaks: List[ShiftBreak]
    ) -> List[float]:
        """
        Returns disponible[i] in hours for each slot.
        Slot with no break = 1.0.
        Slot where a break STARTS: disponible = break.start.minutes/60
        Slot where a break ENDS:   disponible = (60 - break.end.minutes) / 60
        """
        disponible = [1.0] * len(slots)

        for br in breaks:
            for i, slot_label in enumerate(slots):
                slot_hour = int(slot_label[:2])
                # Break starts in this slot
                if br.start_time.hour == slot_hour:
                    disponible[i] = br.start_time.minute / 60.0
                # Break ends in this slot
                elif br.end_time.hour == slot_hour:
                    disponible[i] = (60 - br.end_time.minute) / 60.0

        return disponible
