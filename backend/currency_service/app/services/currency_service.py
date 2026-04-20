import uuid
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.domain.entities.currency_entities import CurrencyRate
from app.domain.ports.currency_repository import ICurrencyRepository
from app.domain.ports.rate_provider import IRateProvider

logger = logging.getLogger(__name__)

class CurrencyService:
    def __init__(self, repo: ICurrencyRepository, rate_provider: IRateProvider):
        self.repo = repo
        self.rate_provider = rate_provider

    async def get_latest_verified_rate(self, company_id: uuid.UUID, base: str, target: str) -> Optional[CurrencyRate]:
        """Gets the most recent verified rate for a company/currency pair."""
        # Filtramos rates de hoy
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        record = await self.repo.get_latest_verified_rate(
            company_id=company_id,
            base=base.upper(),
            target=target.upper(),
            since=today_start
        )
        
        # Si no hay rate de hoy (ni global ni de empresa), intentamos el último histórico sin filtro de fecha
        if not record:
            record = await self.repo.get_latest_verified_rate(
                company_id=company_id,
                base=base.upper(),
                target=target.upper()
            )
            
        return record

    async def get_exchange_rates_summary(self, company_id: uuid.UUID, base: str, targets: List[str]) -> Dict[str, Any]:
        """
        Generates a summary for the UI: stored vs external fresh rates.
        """
        fresh_rates = await self.rate_provider.get_rates(base, targets)
        
        summary_items = []
        for target in targets:
            stored = await self.get_latest_verified_rate(company_id, base, target)
            current_val = float(stored.rate) if stored else None
            new_val = float(fresh_rates.get(target.upper(), 0))
            
            variation = 0
            if current_val and current_val > 0:
                variation = (new_val - current_val) / current_val
            
            summary_items.append({
                "currency": target.upper(),
                "current_stored_rate": current_val,
                "new_external_rate": new_val if new_val > 0 else None,
                "variation_percentage": round(variation * 100, 2),
                "is_drastic": abs(variation) > 0.10, # 10% threshold
                "last_update": stored.captured_at.isoformat() if stored and stored.captured_at else None
            })
            
        return {
            "company_id": str(company_id),
            "base_currency": base.upper(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rates": summary_items
        }

    async def update_rates_automatically(self, company_id: uuid.UUID, base: str, targets: List[str]):
        """
        Worker logic: fetch external rates and save them via repository.
        """
        fresh_rates = await self.rate_provider.get_rates(base, targets)
        
        for target, new_rate in fresh_rates.items():
            stored = await self.get_latest_verified_rate(company_id, base, target)
            
            is_suspicious = False
            is_verified = True
            
            if stored:
                variation = abs((float(new_rate) - float(stored.rate)) / float(stored.rate))
                if variation > 0.10: # Threshold
                    is_suspicious = True
                    is_verified = False # Requires manual approval
            
            await self.repo.save_rate(
                company_id=company_id,
                base=base.upper(),
                target=target.upper(),
                rate=Decimal(str(new_rate)),
                source="banxico" if target.upper() == "MXN" else "frankfurter",
                is_suspicious=is_suspicious,
                is_verified=is_verified
            )

    async def manual_update_rate(
        self, company_id: uuid.UUID, base: str, target: str, rate: Decimal, user_id: uuid.UUID
    ) -> CurrencyRate:
        """User manually enters a rate via repository."""
        return await self.repo.save_rate(
            company_id=company_id,
            base=base.upper(),
            target=target.upper(),
            rate=rate,
            source="manual",
            is_suspicious=False,
            is_verified=True,
            captured_by=user_id
        )

    async def verify_rate(self, rate_id: uuid.UUID, verifier_id: uuid.UUID) -> bool:
        """Approve a suspicious rate via repository."""
        return await self.repo.verify_rate(rate_id)
