"""
LaborDensityService — materializa HourlyLaborSnapshot por rangos de horas.

Roll-over fix (Tip #1): un Labor que abarca 06:15–09:30 dispara recálculo
de las snapshots de las horas 6, 7, 8 y 9, no solo la hora actual.

Regla de multitenancy (Tip #2): el UniqueConstraint incluye company_id.

Gained hours (Tip #4): el campo gained_hrs NO se toca aquí — se actualiza
exclusivamente por eventos de producción (registro de piezas en WorkOrder).
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mes_app.models.labor import Labor, LaborType, LaborCategory
from mes_app.models.hourly_labor_snapshot import HourlyLaborSnapshot
from mes_app.models.production_run import ProductionRun
from mes_app.models.production_snapshot import HourlyProductionSnapshot

logger = logging.getLogger(__name__)


class LaborDensityService:
    """
    Recalcula HourlyLaborSnapshot para todas las horas afectadas por un evento de labor.

    Uso:
        svc = LaborDensityService()
        await svc.materialize_range(
            production_run_id=run.id,
            resource_id=run.resource_id,
            company_id=company_id,
            clock_in=labor.clock_in,
            clock_out=labor.clock_out,   # None = aún activo
            db=db,
        )
    """

    async def materialize_range(
        self,
        production_run_id: uuid.UUID,
        resource_id: uuid.UUID,
        company_id: uuid.UUID,
        clock_in: datetime,
        clock_out: Optional[datetime],
        db: AsyncSession,
    ) -> None:
        """
        Recalcula snapshots para TODAS las horas que toca el intervalo [clock_in, clock_out].
        clock_out=None usa datetime.now(UTC) como límite superior.
        """
        now = datetime.now(timezone.utc)
        eff_end = clock_out or now

        # Normalizar a UTC si viene sin tzinfo
        if clock_in.tzinfo is None:
            clock_in = clock_in.replace(tzinfo=timezone.utc)
        if eff_end.tzinfo is None:
            eff_end = eff_end.replace(tzinfo=timezone.utc)

        run_date = clock_in.date()
        start_hour = clock_in.hour
        end_hour = eff_end.hour

        for hour in range(start_hour, end_hour + 1):
            try:
                await self._materialize_hour(
                    production_run_id=production_run_id,
                    resource_id=resource_id,
                    company_id=company_id,
                    target_date=run_date,
                    hour=hour,
                    db=db,
                )
            except Exception:
                logger.exception(
                    "LaborDensityService: error materializing hour %d for resource %s",
                    hour, resource_id,
                )

    async def _materialize_hour(
        self,
        production_run_id: uuid.UUID,
        resource_id: uuid.UUID,
        company_id: uuid.UUID,
        target_date: date,
        hour: int,
        db: AsyncSession,
    ) -> None:
        """
        Recalcula la snapshot para (resource_id, date, hour).

        Time-slice: un Labor aporta a la hora H si:
            clock_in.hour <= H  AND  (clock_out IS NULL OR clock_out.hour >= H)

        Tiempo efectivo dentro de H:
            eff_start = max(clock_in, H:00:00)
            eff_end   = min(clock_out OR now, H:59:59)
            contribution = eff_end - eff_start  (si > 0)
        """
        now = datetime.now(timezone.utc)
        hour_start = datetime(
            target_date.year, target_date.month, target_date.day,
            hour, 0, 0, tzinfo=timezone.utc,
        )
        hour_end = datetime(
            target_date.year, target_date.month, target_date.day,
            hour, 59, 59, tzinfo=timezone.utc,
        )

        # Todos los Labor del run que se solapan con la hora H
        stmt = (
            select(Labor, LaborType)
            .outerjoin(LaborType, Labor.type_id == LaborType.id)
            .where(
                Labor.production_run_id == production_run_id,
                Labor.company_id == company_id,
                Labor.clock_in <= hour_end,
            )
            .where(
                (Labor.clock_out >= hour_start) | (Labor.clock_out.is_(None))
            )
        )
        rows = (await db.execute(stmt)).all()

        headcount_active = 0
        headcount_on_permit = 0
        headcount_transferred_in = 0
        headcount_transferred_out = 0
        total_minutes = Decimal("0")

        for labor, labor_type in rows:
            # Categoría del registro
            category = LaborCategory.ACTIVE
            if labor_type and labor_type.category:
                try:
                    category = LaborCategory(labor_type.category)
                except ValueError:
                    category = LaborCategory.ACTIVE

            # Clasificar en bucket de estado subdividido
            if category == LaborCategory.PERMIT:
                headcount_on_permit += 1
            elif category == LaborCategory.TRANSFER:
                headcount_transferred_in += 1
            else:
                headcount_active += 1

            # Tiempo efectivo dentro de esta hora
            ci = labor.clock_in
            if ci.tzinfo is None:
                ci = ci.replace(tzinfo=timezone.utc)

            co_raw = labor.clock_out or now
            if co_raw.tzinfo is None:
                co_raw = co_raw.replace(tzinfo=timezone.utc)

            eff_start = max(ci, hour_start)
            eff_end = min(co_raw, hour_end)

            if eff_end > eff_start:
                total_minutes += Decimal(
                    str((eff_end - eff_start).total_seconds() / 60)
                )

        paid_hrs = (total_minutes / Decimal("60")).quantize(Decimal("0.0001"))

        # Upsert: fetch + update, o insert nuevo
        existing = await db.scalar(
            select(HourlyLaborSnapshot).where(
                HourlyLaborSnapshot.resource_id == resource_id,
                HourlyLaborSnapshot.date == target_date,
                HourlyLaborSnapshot.hour == hour,
                HourlyLaborSnapshot.company_id == company_id,
            )
        )

        if existing:
            existing.headcount_active = headcount_active
            existing.headcount_on_permit = headcount_on_permit
            existing.headcount_transferred_in = headcount_transferred_in
            existing.headcount_transferred_out = headcount_transferred_out
            existing.total_labor_minutes = total_minutes
            existing.paid_hrs = paid_hrs
            # gained_hrs: NO se modifica aquí — es responsabilidad de producción
        else:
            snapshot = HourlyLaborSnapshot(
                resource_id=resource_id,
                production_run_id=production_run_id,
                company_id=company_id,
                date=target_date,
                hour=hour,
                headcount_active=headcount_active,
                headcount_on_permit=headcount_on_permit,
                headcount_transferred_in=headcount_transferred_in,
                headcount_transferred_out=headcount_transferred_out,
                total_labor_minutes=total_minutes,
                paid_hrs=paid_hrs,
                gained_hrs=Decimal("0"),
            )
            db.add(snapshot)

        # Sincronizar employees_qty en la snapshot de producción de esa hora
        await self._sync_production_snapshot_headcount(
            resource_id=resource_id,
            company_id=company_id,
            target_date=target_date,
            hour=hour,
            employees_qty=headcount_active,
            paid_hrs_total=paid_hrs,
            db=db,
        )

    async def _sync_production_snapshot_headcount(
        self,
        resource_id: uuid.UUID,
        company_id: uuid.UUID,
        target_date: date,
        hour: int,
        employees_qty: int,
        paid_hrs_total: Decimal,
        db: AsyncSession,
    ) -> None:
        """Mantiene employees_qty y paid_hrs_total en HourlyProductionSnapshot sincronizados."""
        prod_snap = await db.scalar(
            select(HourlyProductionSnapshot).where(
                HourlyProductionSnapshot.resource_id == resource_id,
                HourlyProductionSnapshot.date == target_date,
                HourlyProductionSnapshot.hour == hour,
                HourlyProductionSnapshot.company_id == company_id,
            )
        )
        if prod_snap:
            prod_snap.employees_qty = employees_qty
            prod_snap.paid_hrs_total = paid_hrs_total
