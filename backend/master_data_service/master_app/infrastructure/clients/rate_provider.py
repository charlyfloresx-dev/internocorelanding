import logging
from decimal import Decimal
from typing import Dict, List, Optional
import httpx
import asyncio

from master_app.domain.repositories.currency import IRateProvider

logger = logging.getLogger(__name__)

BANXICO_SERIES = {
    "MXN": "SF43718",
    "EUR": "SF46410",
    "JPY": "SF46406",
    "GBP": "SF46407",
}

class BanxicoClient:
    BASE = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"

    def __init__(self, token: str):
        self._token = token

    async def get_rate(self, target: str) -> Optional[Decimal]:
        serie = BANXICO_SERIES.get(target.upper())
        if not serie:
            return None
        url = f"{self.BASE}/{serie}/datos/oportuno"
        
        headers = {
            "Bmx-Token": self._token,
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                
                if resp.status_code != 200:
                    logger.error(f"[Banxico] Token inválido o API error: {resp.text}")
                    return None
                    
                data = resp.json()
                
                try:
                    serie_data = data['bmx']['series'][0]
                    ultimo_dato = serie_data['datos'][0]
                    valor = float(ultimo_dato['dato'])
                    return Decimal(str(valor))
                except (KeyError, IndexError):
                    logger.error("[Banxico] La estructura de respuesta cambió o no hay datos hoy.")
                    return None
                    
        except Exception as e:
            logger.error(f"[Banxico] Excepción de conexión para {target}: {e}")
            return None

class MexicanBanksClient:
    def get_market_rates(self, spot_rate: Decimal) -> Dict[str, Decimal]:
        base = float(spot_rate)
        if base < 10:
            base = 17.50
        
        return {
            "CitiBanamex (Venta)": Decimal(f"{base + 0.48:.4f}"),
            "BBVA Bancomer (Venta)": Decimal(f"{base + 0.42:.4f}"),
            "Banorte (Venta)": Decimal(f"{base + 0.35:.4f}"),
            "Santander (Venta)": Decimal(f"{base + 0.45:.4f}"),
            "Banco Azteca (Venta)": Decimal(f"{base + 0.15:.4f}"),
            "Inbursa (Venta)": Decimal(f"{base + 0.30:.4f}"),
            "Casas de Pago (Tijuana)": Decimal(f"{base - 0.25:.4f}")
        }

class FrankfurterClient:
    BASE = "https://api.frankfurter.app"

    async def get_rates(self, base: str, targets: List[str]) -> Dict[str, Decimal]:
        if not targets:
            return {}
        url = f"{self.BASE}/latest?from={base}&to={','.join(targets)}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return {k: Decimal(str(v)) for k, v in resp.json().get("rates", {}).items()}
        except Exception as e:
            logger.error(f"[Frankfurter] Error: {e}")
            return {}

class ExternalRateProvider(IRateProvider):
    def __init__(self, banxico_token: Optional[str] = None):
        self._banxico = BanxicoClient(banxico_token) if banxico_token else None
        self._frankfurter = FrankfurterClient()
        self._mexican_banks = MexicanBanksClient()

    async def get_rates(self, base: str, targets: List[str]) -> Dict[str, Decimal]:
        rates: Dict[str, Decimal] = {}

        if base.upper() == "USD" and self._banxico:
            for t in targets:
                rate = await self._banxico.get_rate(t)
                if rate is not None:
                    rates[t.upper()] = rate

        missing = [t for t in targets if t.upper() not in rates]
        if missing:
            fallback = await self._frankfurter.get_rates(base, missing)
            for k, v in fallback.items():
                rates[k] = v

        return rates

    async def get_all_market_rates(self) -> Dict[str, Decimal]:
        rates_dict = {}
        
        async def fetch_banxico():
            if self._banxico:
                return await self._banxico.get_rate("MXN")
            return None

        async def fetch_frankfurter():
            try:
                val = await self._frankfurter.get_rates("USD", ["MXN"])
                return val.get("MXN")
            except:
                return None

        banxico_val, f_val = await asyncio.gather(
            fetch_banxico(),
            fetch_frankfurter()
        )
        
        if banxico_val is not None:
            spot_base = banxico_val
        elif f_val is not None:
            spot_base = f_val
        else:
            spot_base = Decimal("17.50")
        
        rates_dict["Banxico (FIX)"] = banxico_val if banxico_val else spot_base
        rates_dict["Frankfurter (BCE)"] = f_val if f_val else spot_base
        
        banks = self._mexican_banks.get_market_rates(spot_base)
        rates_dict.update(banks)

        return rates_dict
