from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Optional
import uuid
from decimal import Decimal

from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.currency_service import CurrencyService
from app.schemas.exchange_rate import RateRead, RateManualUpdate, RateSummaryResponse
from app.infrastructure.clients.rate_provider import ExternalRateProvider
from app.infrastructure.repositories.currency_repository import SQLAlchemyCurrencyRepository

# Mock for UserContext (in a real app, this comes from common auth)
# For now, we'll use a header for company_id to keep it simple and testable
router = APIRouter()

async def get_currency_service(db: AsyncSession = Depends(get_db)) -> CurrencyService:
    # In production, get token from env/settings
    from common.config import settings
    provider = ExternalRateProvider(banxico_token=settings.int_banxico_token)
    repo = SQLAlchemyCurrencyRepository(db)
    return CurrencyService(repo, rate_provider=provider)

@router.get("/latest", response_model=RateSummaryResponse)
async def get_summary(
    x_company_id: uuid.UUID = Header(...),
    base: str = "USD",
    targets: str = "MXN,EUR", # Comma separated
    service: CurrencyService = Depends(get_currency_service)
):
    target_list = targets.split(",")
    return await service.get_exchange_rates_summary(x_company_id, base, target_list)

@router.post("/update-all")
async def trigger_update(
    x_company_id: uuid.UUID = Header(...),
    base: str = "USD",
    targets: str = "MXN,EUR",
    service: CurrencyService = Depends(get_currency_service)
):
    target_list = targets.split(",")
    await service.update_rates_automatically(x_company_id, base, target_list)
    return {"message": "Update triggered"}

@router.post("/manual", response_model=RateRead)
async def manual_update(
    update_in: RateManualUpdate,
    x_company_id: uuid.UUID = Header(...),
    x_user_id: uuid.UUID = Header(...),
    service: CurrencyService = Depends(get_currency_service)
):
    return await service.manual_update_rate(
        company_id=x_company_id,
        base=update_in.base_currency,
        target=update_in.target_currency,
        rate=update_in.rate,
        user_id=x_user_id
    )

@router.patch("/verify/{rate_id}")
async def verify_rate(
    rate_id: uuid.UUID,
    x_user_id: uuid.UUID = Header(...),
    service: CurrencyService = Depends(get_currency_service)
):
    success = await service.verify_rate(rate_id, x_user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rate not found")
    return {"message": "Rate verified"}

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
    markets = await service.rate_provider.get_all_market_rates()
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
        # Mapea tasas disponibles directo del proveedor
        if "MXN" in target_list:
            if "Banxico (FIX)" in markets:
                flat_rates["MXN"] = float(markets["Banxico (FIX)"])
            elif "Frankfurter (BCE)" in markets:
                flat_rates["MXN"] = float(markets["Frankfurter (BCE)"])
            else:
                flat_rates["MXN"] = 17.50
        
        if "EUR" in target_list:
            flat_rates["EUR"] = 0.92 # Default stub
            
    return {
        "base": base,
        "rates": flat_rates,
        "markets": markets,
        "last_updated": last_updated
    }
