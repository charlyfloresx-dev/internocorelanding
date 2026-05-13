from fastapi import Security, APIRouter, Depends, HTTPException, Header, status
from typing import List, Optional, Any
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from master_app.dependencies import get_db, get_currency_service, get_current_user
from master_app.services.currency_service import CurrencyService
from master_app.schemas.exchange_rate import RateRead, RateManualUpdate, RateSummaryResponse
from common.security.dependencies import require_scope
from common.responses import ApiResponse
from common.domain.entities.user_context import UserContext

router = APIRouter()

@router.get("/latest", response_model=ApiResponse[RateSummaryResponse])
async def get_summary(
    base: str = "USD",
    targets: str = "MXN,EUR",
    current_user: UserContext = Security(require_scope(["master_data:read"])),
    service: CurrencyService = Depends(get_currency_service)
):
    target_list = targets.split(",")
    data = await service.get_exchange_rates_summary(current_user.company_id, base, target_list)
    return ApiResponse(status="success", data=data)

@router.post("/update-all")
async def trigger_update(
    base: str = "USD",
    targets: str = "MXN,EUR",
    current_user: UserContext = Security(require_scope(["master_data:write"])),
    service: CurrencyService = Depends(get_currency_service)
):
    target_list = targets.split(",")
    await service.update_rates_automatically(current_user.company_id, base, target_list)
    return ApiResponse(status="success", message="Update triggered")

@router.post("/manual", response_model=ApiResponse[RateRead])
async def manual_update(
    update_in: RateManualUpdate,
    current_user: UserContext = Security(require_scope(["master_data:write"])),
    service: CurrencyService = Depends(get_currency_service)
):
    rate = await service.manual_update_rate(
        company_id=current_user.company_id,
        base=update_in.base_currency,
        target=update_in.target_currency,
        rate=update_in.rate,
        user_id=current_user.user_id
    )
    return ApiResponse(status="success", data=rate, message="Manual rate updated")

@router.patch("/verify/{rate_id}")
async def verify_rate(
    rate_id: uuid.UUID,
    current_user: UserContext = Security(require_scope(["master_data:write"])),
    service: CurrencyService = Depends(get_currency_service)
):
    success = await service.verify_rate(rate_id, current_user.company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rate not found")
    return ApiResponse(status="success", message="Rate verified")

@router.get("/active-rate")
async def get_active_rates(
    base: str = "USD",
    targets: str = "MXN,EUR",
    x_company_id: Optional[uuid.UUID] = Header(None),
    service: CurrencyService = Depends(get_currency_service)
):
    """
    Endpoint ultra-rápido para el frontend y apps externas.
    Si x_company_id NO se manda, devuelve las tasas de los mercados.
    """
    target_list = targets.split(",")
    markets = await service.get_all_market_rates()
    flat_rates = {}
    last_updated = None

    if x_company_id:
        summary = await service.get_exchange_rates_summary(x_company_id, base, target_list)
        flat_rates = {
            rate["currency"]: rate["current_stored_rate"] 
            for rate in summary["rates"] 
            if rate["current_stored_rate"] is not None
        }
        last_updated = summary["timestamp"]
    else:
        import datetime
        from zoneinfo import ZoneInfo
        last_updated = datetime.datetime.now(ZoneInfo("UTC")).isoformat()
        if "MXN" in target_list:
            if "Banxico (FIX)" in markets:
                flat_rates["MXN"] = float(markets["Banxico (FIX)"])
            elif "Frankfurter (BCE)" in markets:
                flat_rates["MXN"] = float(markets["Frankfurter (BCE)"])
            else:
                flat_rates["MXN"] = 17.50
        
        if "EUR" in target_list:
            flat_rates["EUR"] = 0.92
            
    data = {
        "base": base,
        "rates": flat_rates,
        "markets": markets,
        "last_updated": last_updated
    }
    return ApiResponse(status="success", data=data)
