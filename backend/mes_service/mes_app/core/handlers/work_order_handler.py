import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from common.exceptions import BusinessRuleException
from mes_app.models.work_order import WorkOrder
from mes_app.models.work_order_line import WorkOrderLine
from mes_app.core.enums import WOType, WorkOrderLineType, WorkOrderLineStatus
from mes_app.core.config import settings

logger = logging.getLogger(__name__)

# Internal service URL (within Docker network)
_INVENTORY_BASE = "http://inventory-service:8000"


class CreateWorkOrderCommand:
    def __init__(
        self,
        order_number: str,
        item_code: str,
        order_qty: int,
        due_date: datetime,
        company_id: uuid.UUID,
        alias: Optional[str] = None,
        wo_type: Optional[WOType] = None,
    ):
        self.order_number = order_number
        self.item_code = item_code
        self.order_qty = order_qty
        self.due_date = due_date
        self.company_id = company_id
        self.alias = alias
        self.wo_type = wo_type


class WorkOrderHandler:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_create(self, command: CreateWorkOrderCommand) -> dict:
        """
        Atomic creation of a WorkOrder + WorkOrderLines (Document+Lines pattern).

        Lines are built from two sources:
          1. BOM from inventory_service (MATERIAL_INPUT lines — one per component)
          2. Finished product itself (PLANNED_OUTPUT line)

        If the BOM HTTP call fails, the WO is still created with just the output line.
        BOM explosion is best-effort to avoid blocking production floor creation.
        """
        async with self.db.begin_nested() as tx:
            try:
                # 1. Create WorkOrder header
                wo = WorkOrder(
                    id=uuid.uuid4(),
                    company_id=command.company_id,
                    tenant_id=command.company_id,
                    order_number=command.order_number,
                    item_code=command.item_code,
                    order_quantity=command.order_qty,
                    request_date=command.due_date,
                    alias=command.alias,
                    release_date=datetime.now(timezone.utc),
                    wo_type=command.wo_type,
                    status="DRAFT",
                )
                self.db.add(wo)
                await self.db.flush()  # get wo.id before building lines

                # 2. Fetch BOM components from inventory_service (best-effort)
                bom_lines = await self._fetch_bom(
                    item_code=command.item_code,
                    company_id=command.company_id,
                )

                # 3. Create MATERIAL_INPUT lines from BOM
                line_number = 1
                for bom in bom_lines:
                    line = WorkOrderLine(
                        id=uuid.uuid4(),
                        company_id=command.company_id,
                        tenant_id=command.company_id,
                        work_order_id=wo.id,
                        line_number=line_number,
                        line_type=WorkOrderLineType.MATERIAL_INPUT,
                        item_code=bom["component_item_code"],
                        planned_quantity=Decimal(str(bom["quantity"])) * command.order_qty,
                        uom=bom.get("uom", "EA"),
                        status=WorkOrderLineStatus.PENDING,
                        bom_id=uuid.UUID(bom["id"]) if bom.get("id") else None,
                    )
                    self.db.add(line)
                    line_number += 1

                # 4. Create PLANNED_OUTPUT line (always present)
                output_line = WorkOrderLine(
                    id=uuid.uuid4(),
                    company_id=command.company_id,
                    tenant_id=command.company_id,
                    work_order_id=wo.id,
                    line_number=line_number,
                    line_type=WorkOrderLineType.PLANNED_OUTPUT,
                    item_code=command.item_code,
                    planned_quantity=Decimal(command.order_qty),
                    actual_quantity=Decimal("0"),
                    status=WorkOrderLineStatus.PENDING,
                )
                self.db.add(output_line)

                await self.db.flush()
                logger.info(
                    f"[WO] Created {wo.order_number} — {len(bom_lines)} BOM lines + 1 output line"
                )

            except Exception as e:
                await tx.rollback()
                raise e

        return {
            "id": str(wo.id),
            "status": wo.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _fetch_bom(
        self, item_code: str, company_id: uuid.UUID
    ) -> list[dict]:
        """
        Fetches BOM components from inventory_service.
        Returns empty list if service is unavailable — WO creation continues.
        """
        url = f"{_INVENTORY_BASE}/api/v1/inventory/boms/"
        params = {"parent_item_code": item_code}
        headers = {
            "X-Company-ID": str(company_id),
            "X-Internal-Secret": settings.INTERNAL_API_KEY,
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code == 200:
                    payload = resp.json()
                    # ApiResponse wrapper: {"status": "success", "data": [...]}
                    data = payload.get("data", payload) if isinstance(payload, dict) else payload
                    return data if isinstance(data, list) else []
        except Exception as exc:
            logger.warning(f"[WO] BOM fetch failed for {item_code}: {exc} — creating WO without BOM lines")
        return []
