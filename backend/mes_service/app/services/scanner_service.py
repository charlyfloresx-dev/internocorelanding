import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.labor import Labor
from app.models.ledger import ManufacturingLedger
from app.models.resource import ResourceResult
from app.services.parser_service import ParserService
from app.infrastructure.wms_client import WMSClient
from common.exceptions import BusinessRuleException

class ScannerService:
    """
    Orquestador principal del proceso de escaneo. 
    Aplica validaciones de Labor, parsing e integración con otros servicios.
    """
    
    GRACE_PERIOD_MINUTES = 10

    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser = ParserService()
        self.wms = WMSClient()

    async def process_scan(
        self, 
        resource_result_id: uuid.UUID, 
        scan_input: str, 
        company_id: uuid.UUID,
        local_txn_id: Optional[uuid.UUID] = None,
        operator_id: Optional[uuid.UUID] = None
    ) -> tuple[ManufacturingLedger, Optional[str]]:
        """
        Procesa el escaneo, valida labor y persiste en el Ledger.
        Retorna (ledger_entry, warning_message).
        """
        # 1. Parsing del input
        sku, qty = self.parser.parse_scan(scan_input)

        # 2. Idempotencia (Edge Buffer)
        if local_txn_id:
            existing = await self._get_existing_txn(local_txn_id)
            if existing:
                return existing, None

        # 3. Labor Guard (Regla de Oro con Periodo de Gracia)
        is_labor_active = await self._check_active_labor(resource_result_id)
        if not is_labor_active:
            in_grace = await self._check_grace_period(resource_result_id)
            if not in_grace:
                raise BusinessRuleException("REJECT_SCAN: No hay personal registrado en línea (Fuera del periodo de gracia)")

        # 6. WMS Check (AL-007: No-Stop Policy)
        # Consultamos stock de forma informativa
        wms_status = await self.wms.check_stock(sku, str(company_id))
        warning = wms_status.get("warning")

        # 4. Calcular Siguiente Secuencia (AL-002)
        next_seq = await self._get_next_sequence(resource_result_id)

        # 5. Crear entrada en el Ledger
        ledger_entry = ManufacturingLedger(
            resource_result_id=resource_result_id,
            company_id=company_id,
            sku=sku,
            qty=qty,
            transaction_type="SCAN",
            sequence_number=next_seq,
            local_txn_id=local_txn_id,
            is_synced=True,
            external_folio=None # Se asignaría según lógica de WorkOrder
        )

        self.db.add(ledger_entry)
        await self.db.flush() # Para obtener el ID si es necesario

        # 5. TODO: Disparar eventos asíncronos (Backflush, KPIs)
        # self.event_publisher.publish("production.declared", ...)

        return ledger_entry, warning

    async def process_sync_batch(
        self, 
        entries: list, 
        company_id: uuid.UUID
    ) -> tuple[int, int]:
        """
        Procesa un lote de sincronización con de-duplicación.
        """
        synced = 0
        skipped = 0
        
        for entry in entries:
            # 1. Verificar si ya existe por local_txn_id Y company_id (Tenant Isolation)
            existing = await self._get_existing_txn(entry.local_txn_id)
            if existing:
                skipped += 1
                continue
                
            # 2. Insertar registro histórico (Backfilling)
            new_entry = ManufacturingLedger(
                resource_result_id=entry.resource_result_id,
                company_id=company_id,
                sku=entry.sku,
                qty=Decimal(str(entry.qty)),
                transaction_type="SCAN",
                sequence_number=entry.sequence_number,
                local_txn_id=entry.local_txn_id,
                is_synced=True,
                external_folio=entry.external_folio,
                created_at=entry.created_at # Respetamos la hora real del Edge
            )
            self.db.add(new_entry)
            synced += 1
            
        await self.db.commit()
        return synced, skipped

    async def _check_active_labor(self, resource_result_id: uuid.UUID) -> bool:
        """Verifica si hay personal activo en la línea."""
        query = select( Labor ).where(
            Labor.resource_result_id == resource_result_id,
            Labor.is_active_labor == True
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def _check_grace_period(self, resource_result_id: uuid.UUID) -> bool:
        """
        Verifica si estamos dentro de los 10 minutos de gracia desde el último clock-out
        o desde que se abrió el turno.
        """
        # Simplificación: 10 min desde la apertura si no hay nadie, 
        # o 10 min desde que el último se fue.
        query = select(func.max(Labor.clock_out)).where(Labor.resource_result_id == resource_result_id)
        result = await self.db.execute(query)
        last_clock_out = result.scalar()

        if not last_clock_out:
            # Si nadie ha entrado, verificamos desde el inicio del turno
            res_result = await self.db.get(ResourceResult, resource_result_id)
            if res_result:
                return datetime.now() <= res_result.start_time + timedelta(minutes=self.GRACE_PERIOD_MINUTES)
            return False

        return datetime.now() <= last_clock_out + timedelta(minutes=self.GRACE_PERIOD_MINUTES)

    async def _get_next_sequence(self, resource_result_id: uuid.UUID) -> int:
        """Obtiene el siguiente número de secuencia para este resultado de turno."""
        query = select(func.max(ManufacturingLedger.sequence_number)).where(
            ManufacturingLedger.resource_result_id == resource_result_id
        )
        result = await self.db.execute(query)
        current_max = result.scalar() or 0
        return current_max + 1

    async def _get_existing_txn(self, local_txn_id: uuid.UUID) -> Optional[ManufacturingLedger]:
        """Busca una transacción por su ID local para evitar duplicados."""
        query = select(ManufacturingLedger).where(ManufacturingLedger.local_txn_id == local_txn_id)
        result = await self.db.execute(query)
        return result.scalars().first()
