import httpx
import logging
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from common.logger import get_logger

logger = get_logger(__name__)

class TijuanaPredialProvider:
    """
    Conector 'Ghost' para el Portal de Pagos de Predial de Tijuana.
    Fuente de la verdad para: Nombre del Propietario y Monto del Adeudo.
    """
    def __init__(self):
        self.base_url = "https://pagos.tijuana.gob.mx/pagopredial/"
        self.timeout = 20.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://pagos.tijuana.gob.mx",
            "Referer": "https://pagos.tijuana.gob.mx/pagopredial/"
        }

    async def get_property_data(self, cadastral_key: str) -> Optional[Dict[str, Any]]:
        """
        Consulta el adeudo y el propietario en el portal de pagos.
        Formato esperado de clave: PK-020-027
        """
        # Limpiar clave al formato que espera el portal (con guiones)
        clean_key = self._format_key_for_portal(cadastral_key)
        
        try:
            async with httpx.AsyncClient(verify=False, headers=self.headers, follow_redirects=True) as client:
                # 1. Obtener ViewState inicial
                logger.debug(f"Predial: Iniciando sesión en {self.base_url}")
                resp = await client.get(self.base_url, timeout=self.timeout)
                if resp.status_code != 200:
                    logger.warning(f"Predial: Portal fuera de servicio o en mantenimiento ({resp.status_code})")
                    return None
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                form_data = self._extract_asp_params(soup)
                
                # 2. Inyectar clave catastral y disparar consulta
                form_data["ctl00$ContentPlaceHolder1$txtClave"] = clean_key
                form_data["ctl00$ContentPlaceHolder1$btnConsultar"] = "Consultar"
                
                logger.debug(f"Predial: Consultando clave {clean_key}")
                resp = await client.post(self.base_url, data=form_data, timeout=self.timeout)
                
                if "No se encontró la clave" in resp.text:
                    logger.warning(f"Predial: Clave {clean_key} no encontrada en el padrón.")
                    return None
                
                # 3. Extraer datos del resultado
                soup = BeautifulSoup(resp.text, 'html.parser')
                return self._parse_results(soup, clean_key)

        except Exception as e:
            logger.error(f"Predial: Error crítico en el scraper: {str(e)}")
            return None

    def _format_key_for_portal(self, key: str) -> str:
        # Asegurar formato PK-020-027
        clean = key.replace("-", "").strip().upper()
        if len(clean) >= 8:
            return f"{clean[:2]}-{clean[2:5]}-{clean[5:8]}"
        return key

    def _extract_asp_params(self, soup: BeautifulSoup) -> Dict[str, str]:
        params = {}
        for field in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]:
            tag = soup.find(id=field)
            if tag:
                params[field] = tag.get("value", "")
        return params

    def _parse_results(self, soup: BeautifulSoup, key: str) -> Dict[str, Any]:
        """Extrae el Propietario y el Monto del Adeudo del DOM."""
        data = {
            "cadastral_key": key,
            "owner_name": None,
            "total_debt": 0.0,
            "status": "active"
        }
        
        # El nombre del propietario suele estar en un span específico
        owner_tag = soup.find(id="ctl00_ContentPlaceHolder1_lblPropietario")
        if owner_tag:
            data["owner_name"] = owner_tag.get_text().strip()
        
        # El adeudo total
        debt_tag = soup.find(id="ctl00_ContentPlaceHolder1_lblTotal")
        if debt_tag:
            try:
                # Limpiar "$ 1,234.56" -> 1234.56
                debt_str = debt_tag.get_text().replace("$", "").replace(",", "").strip()
                data["total_debt"] = float(debt_str)
            except:
                logger.warning(f"Predial: No se pudo parsear el adeudo: {debt_tag.get_text()}")

        return data if data["owner_name"] else None
