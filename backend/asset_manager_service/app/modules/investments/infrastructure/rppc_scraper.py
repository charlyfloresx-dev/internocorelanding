import httpx
import logging
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

class RppcScraperService:
    BASE_URL = "https://rppcweb.ebajacalifornia.gob.mx/portalbc/Produccion/WebAPI/Servicios/ConsultaRegistral/obtenerLotes"

    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://rppcweb.ebajacalifornia.gob.mx/",
            "Origin": "https://rppcweb.ebajacalifornia.gob.mx"
        }

    async def search_by_address(self, address: str) -> List[Dict]:
        """
        Searches RPPC by address (Localidad).
        """
        payload = {
            "municipio": 2,
            "CRITERIO_BUSQUEDA": "frmLocalidad",
            "VALOR_BUSQUEDA": address
        }
        return await self._fetch_payload(payload)

    async def get_ownership_data(self, cve_cat: str) -> List[Dict]:
        """
        Fetches ownership data from RPPC using the cadastral key.
        Tries both PK-020-027 and PK020027 formats.
        """
        # Try original
        results = await self._fetch(cve_cat)
        if results: return results

        # If it has dashes, try stripping them
        if "-" in cve_cat:
            results = await self._fetch(cve_cat.replace("-", ""))
            if results: return results
        
        # If it doesn't have dashes and is 8 chars, try adding them
        elif len(cve_cat) == 8:
            dashed = f"{cve_cat[:2]}-{cve_cat[2:5]}-{cve_cat[5:]}"
            results = await self._fetch(dashed)
            if results: return results
            
        return []

    async def _fetch(self, cve_cat: str) -> List[Dict]:
        payload = {
            "municipio": 2,
            "CRITERIO_BUSQUEDA": "frmClaveCatastral",
            "VALOR_BUSQUEDA": cve_cat
        }
        return await self._fetch_payload(payload)

    async def _fetch_payload(self, payload: Dict) -> List[Dict]:
        import ssl
        # Create a custom SSL context that is more forgiving
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1') # Lower security level for legacy gov servers
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            async with httpx.AsyncClient(verify=ctx) as client:
                response = await client.post(self.BASE_URL, json=payload, headers=self.headers, timeout=15.0)
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, list) else []
                else:
                    logger.error(f"RPPC API Error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Scraper Exception: {str(e)}")
        return []

    def filter_by_unit(self, results: List[Dict], unit_name: str) -> Optional[Dict]:
        """
        Advanced filtering for multi-unit properties.
        Searches for the unit name (e.g. 'C') in descriptions or unit fields.
        """
        unit_token = unit_name.upper().replace("UNIDAD", "").strip()
        
        for entry in results:
            description = str(entry.get("DESCRIPCION", "")).upper()
            # Look for "UNIDAD C", "UNIT C", or just " C "
            if f"UNIDAD {unit_token}" in description or f"UNIT {unit_token}" in description or f" {unit_token} " in description:
                return entry
                
        # Fallback: check if the 'C' is part of a code or if it's the only one matching
        for entry in results:
            if unit_token in str(entry.get("FOLIO", "")).upper():
                return entry
                
        return None
