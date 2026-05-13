from fastapi import APIRouter, Depends, status, HTTPException
from typing import Dict, Any
import uuid
from decimal import Decimal

from master_app.dependencies import get_current_user, get_currency_service
from master_app.services.currency_service import CurrencyService
from common.domain.entities.user_context import UserContext
from common.responses import ApiResponse

router = APIRouter()

@router.get("/latest", response_model=ApiResponse[Dict[str, Any]])
async def get_latest_exchange_rates(
    current_user: UserContext = Security(require_scope, scopes=["master_data:read"]),
    service: CurrencyService = Depends(get_currency_service)
):
    """
    Get a summary of latest stored rates vs fresh external rates.
    Supports the manual update UI.
    """
    try:
        data = await service.get_latest_exchange_rates_summary(current_user.company_id)
        return ApiResponse(status="success", data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rates: {str(e)}")

@router.post("/update-all", response_model=ApiResponse[None])
async def trigger_automatic_update(
    current_user: UserContext = Security(require_scope, scopes=["master_data:write"]),
    service: CurrencyService = Depends(get_currency_service)
):
    """
    Triggers an automatic update for all currencies of the current company.
    """
    try:
        await service.update_rates_automatically(current_user.company_id)
        return ApiResponse(status="success", message="Automatic update triggered successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during automatic update: {str(e)}")

@router.post("/manual", response_model=ApiResponse[Any])
async def manual_update_rate(
    target_currency: str,
    rate: Decimal,
    current_user: UserContext = Security(require_scope, scopes=["master_data:write"]),
    service: CurrencyService = Depends(get_currency_service)
):
    """
    Manually register a new exchange rate.
    """
    try:
        record = await service.manual_update_rate(
            company_id=current_user.company_id,
            target_currency=target_currency,
            rate=rate,
            user_id=current_user.user_id
        )
        return ApiResponse(status="success", data=record, message="Rate updated manually")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/verify/{rate_id}", response_model=ApiResponse[bool])
async def verify_suspicious_rate(
    rate_id: uuid.UUID,
    current_user: UserContext = Security(require_scope, scopes=["master_data:write"]),
    service: CurrencyService = Depends(get_currency_service)
):
    """
    Verify/Approve a suspicious rate.
    """
    success = await service.verify_rate(rate_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rate record not found")
    return ApiResponse(status="success", data=True, message="Rate verified successfully")
