import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, Any, TYPE_CHECKING
from mes_app.domain.repositories.interfaces import (
    IProductionRunRepository, IManufacturingLedgerRepository,
    ILaborRepository, IWMSClient, IWorkOrderRepository,
)
from mes_app.services.parser_service import ParserService
from mes_app.services.pattern_validator import PatternValidatorService
from common.exceptions import BusinessRuleException

if TYPE_CHECKING:
    from mes_app.infrastructure.clients.master_data_client import MasterDataClient

_MULTI_COUNT_PATTERN = re.compile(r"^(\d+)\*(.+)$")


class ScannerService:
    """
    Orquestador principal del proceso de escaneo.
    100% Shielded from Infrastructure and app.models.
    """

    GRACE_PERIOD_MINUTES = 10

    def __init__(
        self,
        run_repo: IProductionRunRepository,
        ledger_repo: IManufacturingLedgerRepository,
        labor_repo: ILaborRepository,
        wms_client: IWMSClient,
        wo_repo: IWorkOrderRepository,
        master_data_client: "MasterDataClient",
    ):
        self.run_repo = run_repo
        self.ledger_repo = ledger_repo
        self.labor_repo = labor_repo
        self.wms = wms_client
        self.wo_repo = wo_repo
        self.master_data = master_data_client
        self.parser = ParserService()

    async def process_scan(
        self, 
        resource_result_id: uuid.UUID, 
        scan_input: str, 
        company_id: uuid.UUID,
        local_txn_id: Optional[uuid.UUID] = None
    ) -> tuple[Any, Optional[str]]:
        sku, qty = self.parser.parse_scan(scan_input)

        # Strip multiplier prefix (N*) to get the bare item code for pattern validation
        stripped = _MULTI_COUNT_PATTERN.sub(r"\2", scan_input.strip().upper())

        # Validate scan patterns (best-effort — fetch error never rejects a scan)
        try:
            patterns = await self.master_data.get_scan_patterns(sku, company_id)
            if patterns:
                error = PatternValidatorService().validate(stripped, patterns)
                if error:
                    raise BusinessRuleException(error)
        except BusinessRuleException:
            raise
        except Exception:
            pass  # network/parse failure → skip validation, proceed with scan

        if local_txn_id:
            existing = await self.ledger_repo.get_by_id(local_txn_id) # local_txn_id is the PK in some flows
            if existing:
                return existing, None

        is_labor_active = await self.labor_repo.get_active_count_at(resource_result_id, datetime.now()) > 0
        if not is_labor_active:
            in_grace = await self._check_grace_period(resource_result_id)
            if not in_grace:
                raise BusinessRuleException("REJECT_SCAN: No hay personal registrado en línea (Fuera del periodo de gracia)")

        wms_status = await self.wms.check_stock(sku, str(company_id))
        warning = wms_status.get("warning")

        next_seq = await self.ledger_repo.get_next_sequence(resource_result_id)

        # Usamos el Factory del repositorio para evitar importar app.models
        ledger_entry = await self.ledger_repo.create(
            production_run_id=resource_result_id,
            company_id=company_id,
            sku=sku,
            qty=qty,
            transaction_type="SCAN",
            sequence_number=next_seq,
            local_txn_id=local_txn_id,
            is_synced=True
        )

        # Update WorkOrder progress counters (best-effort — scan is never blocked by WO state)
        run = await self.run_repo.get_by_id(resource_result_id)
        if run and run.work_order_id:
            try:
                await self.wo_repo.increment_manufactured_quantity(
                    work_order_id=run.work_order_id,
                    qty=qty,
                    company_id=company_id,
                )
            except Exception:
                pass  # WO update failure must not reject a valid scan

        return ledger_entry, warning

    async def _check_grace_period(self, resource_result_id: uuid.UUID) -> bool:
        labors = await self.labor_repo.get_by_run_id(resource_result_id)
        last_clock_out = None
        for lb in labors:
            if lb.clock_out:
                if not last_clock_out or lb.clock_out > last_clock_out:
                    last_clock_out = lb.clock_out

        if not last_clock_out:
            res_run = await self.run_repo.get_by_id(resource_result_id)
            if res_run:
                return datetime.now() <= res_run.created_at + timedelta(minutes=self.GRACE_PERIOD_MINUTES)
            return False

        return datetime.now() <= last_clock_out + timedelta(minutes=self.GRACE_PERIOD_MINUTES)
