import uuid
from typing import List, Any, Optional
import typing
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, condecimal

from app.dependencies import get_db, get_current_user
from common.security.auth_payload import TokenPayload
from common.responses import ApiResponse
from common.exceptions import BusinessRuleException, NotFoundException

import logging

logger = logging.getLogger("wms.api")

router = APIRouter()

class GoodsReceiptItem(BaseModel):
    product_id: str
    quantity: condecimal(gt=0, decimal_places=4)
    unit_cost: condecimal(ge=0, decimal_places=4)
    location_id: Optional[str] = None

class GoodsReceiptRequest(BaseModel):
    company_id: str # Added company_id as per the new command
    folio: str
    warehouse_id: str
    concept_id: str
    items: List[GoodsReceiptItem]

@router.post("/goods-receipt", response_model=None, summary="Finalize Goods Receipt")
async def create_goods_receipt(
    request: GoodsReceiptRequest,
    db: AsyncSession = Depends(get_db)
) -> typing.Any:
    """
    Creates, fills, and confirms a goods receipt (GR).
    Automatically triggers the inventory record in the Inventory Service.
    """
    print(f"[*] RECEIVING GOODS RECEIPT REQUEST: {request.folio}", flush=True)
    from app.application.handlers import (
        CreateInventoryDocumentHandler, 
        AddMovementHandler, 
        ConfirmDocumentHandler
    )
    from app.application.commands import (
        CreateInventoryDocumentCommand, 
        AddMovementCommand, 
        ConfirmDocumentCommand
    )
    from datetime import datetime
    
    try:
        # 1. Create Document
        create_cmd = CreateInventoryDocumentCommand(
            concept_id=request.concept_id,
            warehouse_id=request.warehouse_id,
            folio=request.folio
        )
        doc_handler = CreateInventoryDocumentHandler(db)
        doc = await doc_handler.handle(create_cmd, uuid.UUID(request.company_id))

        # 2. Add Movements
        mov_handler = AddMovementHandler(db)
        for item in request.items:
            mov_cmd = AddMovementCommand(
                document_id=str(doc.id),
                product_id=item.product_id,
                warehouse_id=request.warehouse_id,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                location_id=item.location_id
            )
            await mov_handler.handle(mov_cmd, uuid.UUID(request.company_id))

        # 3. Confirm Document (Triggers Inventory Service)
        confirm_cmd = ConfirmDocumentCommand(document_id=str(doc.id))
        confirm_handler = ConfirmDocumentHandler(db)
        confirmed_doc = await confirm_handler.handle(confirm_cmd, uuid.UUID(request.company_id))

        await db.commit()
        
        return {
            "status": "success",
            "message": f"Goods Receipt {request.folio} processed and confirmed successfully.",
            "data": {"document_id": str(confirmed_doc.id), "folio": confirmed_doc.folio}
        }
    except BusinessRuleException as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundException as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        print(f"ERROR PROCESSING GOODS RECEIPT: {str(e)}", flush=True)
        logger.error(f"Error processing goods receipt: {e}")
        raise HTTPException(status_code=500, detail=str(e))
