import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from common.exceptions import BusinessRuleException, NotFoundException
from mes_app.models.work_order import WorkOrder
from mes_app.models.work_order_line import WorkOrderLine
from mes_app.core.enums import WOType, WorkOrderLineType, WorkOrderLineStatus
from mes_app.core.config import settings

logger = logging.getLogger(__name__)

_INVENTORY_BASE = settings.int_inventory_service_url

MATERIAL_STATUS_PENDING = "PENDING_ISSUE"
MATERIAL_STATUS_ISSUED  = "ISSUED"


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
        Creates a WorkOrder header + single PLANNED_OUTPUT line.

        MATERIAL_INPUT lines are NOT created automatically — they must be
        issued explicitly via handle_issue_material() once the warehouse
        physically supplies the components to the production cell.

        material_status="PENDING_ISSUE" signals the alert in the UI without
        blocking the workflow.
        """
        async with self.db.begin_nested() as tx:
            try:
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
                    material_status=MATERIAL_STATUS_PENDING,
                )
                self.db.add(wo)
                await self.db.flush()

                # Only PLANNED_OUTPUT at creation — material is issued separately
                output_line = WorkOrderLine(
                    id=uuid.uuid4(),
                    company_id=command.company_id,
                    tenant_id=command.company_id,
                    work_order_id=wo.id,
                    line_number=1,
                    line_type=WorkOrderLineType.PLANNED_OUTPUT,
                    item_code=command.item_code,
                    planned_quantity=Decimal(command.order_qty),
                    actual_quantity=Decimal("0"),
                    status=WorkOrderLineStatus.PENDING,
                )
                self.db.add(output_line)
                await self.db.flush()

                logger.info(
                    f"[WO] Created {wo.order_number} — PLANNED_OUTPUT only, "
                    f"material_status={MATERIAL_STATUS_PENDING}"
                )

            except Exception as e:
                await tx.rollback()
                raise e

        return {
            "id": str(wo.id),
            "status": wo.status,
            "material_status": MATERIAL_STATUS_PENDING,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def handle_issue_material(
        self, order_number: str, company_id: uuid.UUID
    ) -> dict:
        """
        Issues material to a WorkOrder by fetching the BOM and creating
        MATERIAL_INPUT lines. Idempotent — skips if already issued.

        Raises NotFoundException if WO does not belong to this company.
        """
        result = await self.db.execute(
            select(WorkOrder).where(
                WorkOrder.order_number == order_number,
                WorkOrder.company_id == company_id,
            )
        )
        wo = result.scalar_one_or_none()
        if not wo:
            raise NotFoundException("WorkOrder not found")

        if wo.material_status == MATERIAL_STATUS_ISSUED:
            return {
                "id": str(wo.id),
                "status": wo.status,
                "material_status": MATERIAL_STATUS_ISSUED,
                "message": "Material already issued — no changes made",
            }

        async with self.db.begin_nested() as tx:
            try:
                bom_lines = await self._fetch_bom(
                    item_code=wo.item_code,
                    company_id=company_id,
                )

                # Remove any existing MATERIAL_INPUT lines (idempotency)
                existing = await self.db.execute(
                    select(WorkOrderLine).where(
                        WorkOrderLine.work_order_id == wo.id,
                        WorkOrderLine.line_type == WorkOrderLineType.MATERIAL_INPUT,
                    )
                )
                for old_line in existing.scalars().all():
                    await self.db.delete(old_line)

                # Create fresh MATERIAL_INPUT lines from BOM
                for i, bom in enumerate(bom_lines, start=1):
                    self.db.add(WorkOrderLine(
                        id=uuid.uuid4(),
                        company_id=company_id,
                        tenant_id=company_id,
                        work_order_id=wo.id,
                        line_number=i,
                        line_type=WorkOrderLineType.MATERIAL_INPUT,
                        item_code=bom["component_item_code"],
                        planned_quantity=Decimal(str(bom["quantity"])) * wo.order_quantity,
                        uom=bom.get("uom", "EA"),
                        status=WorkOrderLineStatus.PENDING,
                        bom_id=uuid.UUID(bom["id"]) if bom.get("id") else None,
                    ))

                wo.material_status = MATERIAL_STATUS_ISSUED
                await self.db.flush()

                logger.info(
                    f"[WO] Material issued for {wo.order_number} — "
                    f"{len(bom_lines)} MATERIAL_INPUT lines created"
                )

            except Exception as e:
                await tx.rollback()
                raise e

        await self.db.commit()
        return {
            "id": str(wo.id),
            "status": wo.status,
            "material_status": MATERIAL_STATUS_ISSUED,
            "bom_lines_created": len(bom_lines),
        }

    async def _fetch_bom(self, item_code: str, company_id: uuid.UUID) -> list[dict]:
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
                    data = payload.get("data", payload) if isinstance(payload, dict) else payload
                    return data if isinstance(data, list) else []
        except Exception as exc:
            logger.warning(
                f"[WO] BOM fetch failed for {item_code}: {exc} — no MATERIAL_INPUT lines"
            )
        return []
