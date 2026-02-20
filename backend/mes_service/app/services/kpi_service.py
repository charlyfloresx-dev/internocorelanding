import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resource import ResourceResult
from app.models.ledger import ManufacturingLedger
from app.models.downtime import Downtime
from app.models.labor import Labor
from common.exceptions import NotFoundException

class KPIService:
    """
    Servicio encargado de los cálculos de OEE y KPIs en tiempo real.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_oee(self, resource_result_id: uuid.UUID) -> Dict[str, Any]:
        """
        Calcula el OEE completo para un resultado de producción específico (Turno).
        OEE = Disponibilidad * Eficiencia * Calidad (MVP Calidad = 1.0)
        """
        # 1. Obtener el ResourceResult para el tiempo programado
        result = await self.db.get(ResourceResult, resource_result_id)
        if not result:
            raise NotFoundException("ResourceResult not found")

        # Duración del turno hasta ahora (o total si está cerrado)
        end_time = result.end_time or datetime.now()
        shift_duration_minutes = (end_time - result.start_time).total_seconds() / 60

        # 2. Calcular Disponibilidad (A)
        # Disponibilidad = (Tiempo Programado - Downtime) / Tiempo Programado
        downtime_minutes = await self._get_total_downtime(resource_result_id)
        if shift_duration_minutes > 0:
            availability = (shift_duration_minutes - downtime_minutes) / shift_duration_minutes
        else:
            availability = 0.0

        # 3. Calcular Eficiencia (E)
        # Eficiencia = (Piezas Producidas * StdTime) / TotalLaborHours
        # NOTA: Para el MVP, si no tenemos StdTime dinámico, usamos un factor de 1.0 o simplificado.
        # Aquí sumamos la cantidad del Ledger.
        total_produced = await self._get_total_produced(resource_result_id)
        total_labor_minutes = await self._get_total_labor_minutes(resource_result_id)
        
        # Simplificación MVP: Eficiencia basada en piezas vs meta (o tiempo estandar)
        # E = (Produced / TotalLaborHours) / Ideal_Rate
        if total_labor_minutes > 0:
            # Supongamos 1 pieza por minuto por persona como ideal para el ejemplo
            efficiency = float(total_produced) / (total_labor_minutes / 60.0) / 60.0 # Ajustar según StdTime real
            efficiency = min(1.0, efficiency) # Cappeado a 100% para el dashboard básico
        else:
            efficiency = 0.0

        # 4. OEE
        quality = 1.0 # MVP
        oee = availability * efficiency * quality

        return {
            "oee": round(oee * 100, 2),
            "availability": round(availability * 100, 2),
            "efficiency": round(efficiency * 100, 2),
            "quality": 100.0,
            "metrics": {
                "produced": float(total_produced),
                "downtime_minutes": round(downtime_minutes, 2),
                "labor_minutes": round(total_labor_minutes, 2),
                "shift_duration_minutes": round(shift_duration_minutes, 2)
            }
        }

    async def _get_total_downtime(self, resource_result_id: uuid.UUID) -> float:
        """Suma de minutos de paros cerrados."""
        query = select(Downtime).where(Downtime.resource_result_id == resource_result_id)
        result = await self.db.execute(query)
        downtimes = result.scalars().all()
        
        total_minutes = 0.0
        for dt in downtimes:
            end = dt.end_at or datetime.now()
            total_minutes += (end - dt.start_at).total_seconds() / 60
        return total_minutes

    async def _get_total_produced(self, resource_result_id: uuid.UUID) -> Decimal:
        """Suma de piezas en el Ledger."""
        query = select(func.sum(ManufacturingLedger.qty)).where(
            ManufacturingLedger.resource_result_id == resource_result_id,
            ManufacturingLedger.transaction_type == "SCAN"
        )
        result = await self.db.execute(query)
        return result.scalar() or Decimal("0.0")

    async def _get_total_labor_minutes(self, resource_result_id: uuid.UUID) -> float:
        """Suma de minutos de labor de todo el personal en el turno."""
        query = select(Labor).where(Labor.resource_result_id == resource_result_id)
        result = await self.db.execute(query)
        labors = result.scalars().all()
        
        total_minutes = 0.0
        for lb in labors:
            end = lb.clock_out or datetime.now()
            total_minutes += (end - lb.clock_in).total_seconds() / 60
        return total_minutes

    async def get_resource_graphic(self, resource_result_id: uuid.UUID) -> Dict[str, Any]:
        """
        Porta la lógica de 'GetGraphic' del legacy C#.
        Genera tendencias horarias, metas distribuidas y eficiencia.
        """
        result = await self.db.get(ResourceResult, resource_result_id)
        if not result:
            raise NotFoundException("ResourceResult not found")

        # 1. Definir rango de horas del turno
        start_hour = result.start_time.replace(minute=0, second=0, microsecond=0)
        end_time = result.end_time or datetime.now()
        end_hour = end_time.replace(minute=59, second=59, microsecond=0)

        graphic_data = {
            "categories": [],
            "meta": [],
            "real": [],
            "efficiency": [],
            "accumulated_real": [],
            "accumulated_meta": []
        }

        current_hour = start_hour
        acc_meta = 0
        acc_real = 0

        while current_hour <= end_hour:
            hour_label = current_hour.strftime("%H:00")
            graphic_data["categories"].append(hour_label)

            # 2. Meta para esta hora (Ajustada dinámicamente por Labor)
            # Meta Ajustada = Meta Teórica * (Personal Activo / Personal Planeado)
            theoretical_meta = await self._get_hour_meta(result.resource_id, current_hour.hour)
            
            # Obtener Personal Activo en esa hora (o actual si es la hora en curso)
            active_labor_count = await self._get_active_labor_count_at(resource_result_id, current_hour)
            planned_labor = result.planned_labor or 1
            
            labor_factor = active_labor_count / planned_labor
            adjusted_meta = int(theoretical_meta * labor_factor)
            
            acc_meta += adjusted_meta
            graphic_data["meta"].append(adjusted_meta)
            graphic_data["accumulated_meta"].append(acc_meta)

            # 3. Real producido en esta hora
            hour_real = await self._get_produced_in_slot(resource_result_id, current_hour, current_hour + timedelta(hours=1))
            acc_real += float(hour_real)
            graphic_data["real"].append(float(hour_real))
            graphic_data["accumulated_real"].append(acc_real)

            # 4. Eficiencia de la hora
            # E = (Real * StdTime) / (Operators * 60min)
            eff = 0.0
            if hour_meta > 0:
                eff = (float(hour_real) / hour_meta) * 100
            graphic_data["efficiency"].append(min(100.0, round(eff, 2)))

            current_hour += timedelta(hours=1)

        return graphic_data

    async def calculate_maintenance_kpis(self, resource_result_id: uuid.UUID) -> Dict[str, Any]:
        """
        Calcula indicadores de mantenimiento NF E 60-182.
        MTTR: Mean Time To Repair.
        MTBF: Mean Time Between Failures.
        """
        query = select(Downtime).where(
            Downtime.resource_result_id == resource_result_id,
            Downtime.status.in_(["TECH_CLOSED", "ADMIN_CLOSED"])
        ).order_by(Downtime.start_at)
        
        result = await self.db.execute(query)
        downtimes = result.scalars().all()
        
        if not downtimes:
            return {"mttr": 0.0, "mtbf": 0.0, "total_failures": 0}

        # 1. MTTR: Promedio de tiempo de reparación
        total_repair_time = sum(dt.mttr_minutes for dt in downtimes)
        mttr = total_repair_time / len(downtimes)

        # 2. MTBF: Promedio de tiempo entre fallas
        # Calculamos el tiempo total de operación (Turno - Downtime) / Cantidad de fallas
        res_result = await self.db.get(ResourceResult, resource_result_id)
        if not res_result: return {"mttr": mttr, "mtbf": 0.0, "total_failures": len(downtimes)}
        
        end_time = res_result.end_time or datetime.now()
        total_duration_minutes = (end_time - res_result.start_time).total_seconds() / 60
        
        downtime_minutes = await self._get_total_downtime(resource_result_id)
        uptime_minutes = total_duration_minutes - downtime_minutes
        
        # MTBF = Uptime / Number of Failures
        mtbf = uptime_minutes / len(downtimes) if downtimes else 0.0

        return {
            "mttr": round(mttr, 2),
            "mtbf": round(mtbf, 2),
            "total_failures": len(downtimes),
            "uptime_minutes": round(uptime_minutes, 2)
        }

    async def _get_active_labor_count_at(self, resource_result_id: uuid.UUID, timestamp: datetime) -> int:
        """Cuenta el personal activo en un momento dado."""
        # Consideramos labor activa quienes tienen is_active_labor=True 
        # y su clock_in <= timestamp < clock_out (o actual)
        query = select(func.count(Labor.id)).where(
            Labor.resource_result_id == resource_result_id,
            Labor.clock_in <= timestamp,
            (Labor.clock_out == None) | (Labor.clock_out > timestamp)
        )
        res = await self.db.execute(query)
        return res.scalar() or 0

    async def _get_hour_meta(self, resource_id: uuid.UUID, hour: int) -> int:
        """Busca la meta configurada para esa hora en el Resource."""
        from app.models.kpi import Goal
        query = select(Goal.target_qty).where(
            and_(Goal.resource_id == resource_id, Goal.hour_of_day == hour)
        )
        res = await self.db.execute(query)
        val = res.scalar()
        return val or 0

    async def _get_produced_in_slot(self, resource_result_id: uuid.UUID, start: datetime, end: datetime) -> Decimal:
        """Suma de piezas en un rango de tiempo específico."""
        query = select(func.sum(ManufacturingLedger.qty)).where(
            and_(
                ManufacturingLedger.resource_result_id == resource_result_id,
                ManufacturingLedger.created_at >= start,
                ManufacturingLedger.created_at < end
            )
        )
        res = await self.db.execute(query)
        return res.scalar() or Decimal("0.0")
