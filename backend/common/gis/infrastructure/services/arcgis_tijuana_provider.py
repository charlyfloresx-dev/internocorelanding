import httpx
import logging
import math
import ssl
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List

from common.gis.domain.interfaces.gis_service import IGisService
from common.gis.domain.dtos import PropertyValidationResponse, Coordinates
from common.gis.domain.exceptions import (
    GisServiceException,
    GisProviderUnavailableException,
    GisOutsideBoundaryException,
    CadastralKeyNotFoundException
)
from common.logger import get_logger

logger = get_logger(__name__)

class ArcGisTijuanaProvider(IGisService):
    def __init__(self):
        # URLs
        self.wms_url = "https://gemelodigital.implantijuana.gob.mx/geoserver-local-proxy/wms"
        self.rppc_url = "https://rppcweb.ebajacalifornia.gob.mx/portalbc/Produccion/WebAPI/Servicios/ConsultaRegistral/obtenerLotes"
        self.wizard_url = "https://rppcweb.ebajacalifornia.gob.mx/portalbc/Produccion/WebAPI/Servicios/ConsultaRegistral/wizards"
        self.predial_url = "https://pagos.tijuana.gob.mx/pagopredial/"
        self.timeout = 30.0
        
        # User's exact headers from latest feedback (for RPPC)
        self.rppc_headers = {
            "Accept": "application/json;",
            "Accept-Language": "es-419,es;q=0.9",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://rppcweb.ebajacalifornia.gob.mx",
            "Referer": "https://rppcweb.ebajacalifornia.gob.mx/portalbc/Produccion/portalapp/index.html",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        }
        
        # Create a legacy-compatible SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def get_wms_bbox(self, lat: float, lng: float, margin: int = 15) -> str:
        r_major = 6378137.0
        x = r_major * math.radians(lng)
        y = r_major * math.log(math.tan(math.radians((90 + lat)) / 2.0))
        bbox = f"{x - margin},{y - margin},{x + margin},{y + margin}"
        return bbox

    async def get_location_by_address(self, address_string: str) -> Optional[PropertyValidationResponse]:
        return None

    async def get_data_by_coordinates(self, lat: float, lng: float, company_id: Optional[str] = None) -> Optional[PropertyValidationResponse]:
        bbox = self.get_wms_bbox(lat, lng)
        layer = "catastro_pub:predios-211126_Predios"
        params = {
            "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetFeatureInfo",
            "QUERY_LAYERS": layer, "LAYERS": layer, "INFO_FORMAT": "application/json",
            "X": "160", "Y": "160", "WIDTH": "320", "HEIGHT": "320",
            "SRS": "EPSG:3857", "BBOX": bbox, "buffer": "15", "feature_count": "5"
        }
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(self.wms_url, params=params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                features = data.get("features", [])
                if features:
                    feature = features[0]
                    props = feature.get("properties", {})
                    clave = props.get("cve_cat")
                    superficie = props.get("supfis", 0.0)
                    num_oficial = props.get("numoficial", "")
                    
                    if clave:
                        # Try RPPC first
                        owner_info = await self.get_ownership_from_rppc(clave, address={"num_oficial": num_oficial})
                        owner_name = owner_info.get("owner_name")
                        
                        # Fallback to Predial if RPPC failed or returned generic
                        if not owner_name or "disponible" in owner_name or "Privada" in owner_name:
                            predial_owner = await self.get_ownership_from_predial(clave)
                            if predial_owner:
                                owner_name = predial_owner
                        
                        owner_name = owner_name or "No disponible (Consulta manual requerida)"
                        
                        return PropertyValidationResponse(
                            address=f"V. CARRANZA {num_oficial}".strip(),
                            cadastral_key=self.format_cadastral_key(clave),
                            owner_name=owner_name,
                            land_use="No especificado",
                            location=Coordinates(lat=lat, lng=lng),
                            meta={
                                "superficie": superficie,
                                "num_oficial": num_oficial,
                                "raw_clave": clave,
                                "rppc_info": owner_info.get("raw_data")
                            }
                        )
        except Exception as e:
            logger.error(f"Error in coordinate query: {e}")

        raise GisOutsideBoundaryException(f"No se encontró información catastral para las coordenadas: {lat}, {lng}")

    def format_cadastral_key(self, clave: str, version: int = 1) -> str:
        if not clave or len(clave) < 8: return clave
        clean = clave.replace("-", "")
        prefix = clean[:2]
        manzana = clean[2:5]
        lote = clean[5:8] if len(clean) >= 8 else clean[5:]
        if version == 1: return f"{prefix}-{manzana}-{lote}"
        elif version == 2: return f"{prefix}-{manzana}-{lote}-000"
        elif version == 3: return clean
        return clave

    async def get_ownership_from_rppc(self, clave: str, address: dict = None) -> dict:
        variations = [
            (self.format_cadastral_key(clave, 1), "frmClaveCatastral"),
            (self.format_cadastral_key(clave, 2), "frmClaveCatastral"),
            (self.format_cadastral_key(clave, 3), "frmClaveCatastral")
        ]
        
        async with httpx.AsyncClient(verify=self.ssl_context, headers=self.rppc_headers, follow_redirects=True) as client:
            try:
                await client.post(self.wizard_url, json={"SERVICIO_ID": 2, "ACTO_PORTAL_ID": 0}, timeout=self.timeout)
            except: pass

            for var, criterion in variations:
                payload = {
                    "porFolio": {}, "porLote": {}, "porLocal": {}, "porPartida": {}, "porAntecedente": {},
                    "porClaveCat": {"municipio": 2, "cve_cat": var},
                    "porCurt": {}, "CRITERIO_BUSQUEDA": criterion
                }
                try:
                    response = await client.post(self.rppc_url, json=payload, timeout=self.timeout)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success") and data.get("Datos"):
                            return self._parse_rppc_data(data["Datos"][0], var)
                except: pass
            
            if address and address.get("num_oficial"):
                street = "VENUSTIANO CARRANZA"
                num = str(address["num_oficial"])
                fallback_payloads = [
                    {"municipio": 2, "colonia": "PRESIDENTES", "calle": street, "numero": num},
                    {"municipio": 2, "colonia": "", "calle": street, "numero": num}
                ]
                for local_data in fallback_payloads:
                    payload_local = {
                        "porFolio": {}, "porLote": {}, "porPartida": {}, "porAntecedente": {}, "porClaveCat": {}, "porCurt": {},
                        "porLocal": local_data, "CRITERIO_BUSQUEDA": "frmLocalidad"
                    }
                    try:
                        response = await client.post(self.rppc_url, json=payload_local, timeout=self.timeout)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("success") and data.get("Datos"):
                                for item in data["Datos"]:
                                    dir_str = str(item.get("Direccion", "")).upper()
                                    if " C" in dir_str or "-C" in dir_str:
                                        return self._parse_rppc_data(item, "frmLocalidad")
                                return self._parse_rppc_data(data["Datos"][0], "frmLocalidad")
                    except: pass

        return {"owner_name": None, "cadastral_key": clave}

    async def get_ownership_from_predial(self, clave: str) -> Optional[str]:
        """
        Scrapes the Tijuana Predial portal for ownership.
        """
        clean_key = self.format_cadastral_key(clave, 1) # PK-XXX-XXX
        try:
            async with httpx.AsyncClient(verify=False) as client:
                # 1. Get initial page to get ViewState
                resp = await client.get(self.predial_url, timeout=self.timeout)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                viewstate = soup.find(id="__VIEWSTATE")['value'] if soup.find(id="__VIEWSTATE") else ""
                generator = soup.find(id="__VIEWSTATEGENERATOR")['value'] if soup.find(id="__VIEWSTATEGENERATOR") else ""
                eventvalidation = soup.find(id="__EVENTVALIDATION")['value'] if soup.find(id="__EVENTVALIDATION") else ""
                
                # 2. Submit search
                payload = {
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": generator,
                    "__EVENTVALIDATION": eventvalidation,
                    "ctl00$ContentPlaceHolder1$txtClave": clean_key,
                    "ctl00$ContentPlaceHolder1$btnConsultar": "Consultar"
                }
                
                resp = await client.post(self.predial_url, data=payload, timeout=self.timeout)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Propietario is usually in a label or span
                # Looking for keywords or specific IDs
                propietario_label = soup.find(id="ctl00_ContentPlaceHolder1_lblPropietario")
                if propietario_label:
                    return propietario_label.get_text().strip()
                
                # Fallback: search for "Propietario:" text
                text_search = soup.find(text=re.compile("Propietario:"))
                if text_search:
                    return text_search.find_next().get_text().strip()
        except Exception as e:
            logger.error(f"Predial scraping failed: {e}")
        return None

    def _parse_rppc_data(self, item: dict, used_key: str) -> dict:
        return {
            "owner_name": item.get("Titular") or item.get("Nombre") or "Propiedad Privada",
            "cadastral_key": item.get("ClaveCatastral") or used_key,
            "folio_real": item.get("FolioReal"),
            "raw_data": item
        }

    async def get_legal_owner(self, cadastral_key: str) -> Optional[str]:
        owner_name = await self.get_ownership_from_predial(cadastral_key)
        if not owner_name:
            info = await self.get_ownership_from_rppc(cadastral_key)
            owner_name = info.get("owner_name")
        return owner_name
