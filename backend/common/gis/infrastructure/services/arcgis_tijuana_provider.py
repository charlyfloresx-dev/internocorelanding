import httpx
import logging
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
        # IMPLAN FeatureServer URL for ArcGIS
        self.feature_server_url = "https://services1.arcgis.com/n6Y9Y9vIOnYf9nIn/arcgis/rest/services/Carta_Urbana_Tijuana/FeatureServer/0/query"
        # Predial search URL
        self.predial_url = "https://pagos.tijuana.gob.mx/pago_predial/Busqueda.aspx"
        self.timeout = 15.0

    async def get_location_by_address(self, address_string: str) -> Optional[PropertyValidationResponse]:
        """
        Geocoding -> FeatureServer query -> Extract Key -> Cross reference ownership.
        For simplicity, assuming this acts as a direct query using WHERE clause on FeatureServer.
        """
        # Split string and build WHERE
        query_parts = []
        for word in address_string.split():
            # Very basic string match, can be improved.
            query_parts.append(f"CALLE LIKE '%{word.upper()}%' OR NUMERO_EXT LIKE '%{word.upper()}%'")
        
        where_clause = " AND ".join(query_parts) if query_parts else "1=1"
        
        params = {
            "where": where_clause,
            "outFields": "CLAVE_CAT,USO_SUELO,COLONIA",
            "returnGeometry": "true",
            "f": "json",
            "outSR": "4326"
        }

        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    self.feature_server_url, 
                    params=params, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                features = data.get("features", [])
                if not features:
                    raise GisOutsideBoundaryException(f"No properties found for address: {address_string}")

                feature = features[0]
                clave = feature["attributes"].get("CLAVE_CAT")
                land_use = feature["attributes"].get("USO_SUELO")
                
                geometry = feature.get("geometry", {})
                lat = geometry.get("y", 0.0)
                lng = geometry.get("x", 0.0)
                
                owner_name = await self.get_legal_owner(clave)
                
                return PropertyValidationResponse(
                    address=address_string,
                    cadastral_key=clave,
                    owner_name=owner_name,
                    land_use=land_use,
                    location=Coordinates(lat=lat, lng=lng)
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error querying Catastro: {e}")
            raise GisProviderUnavailableException(f"Service unavailable: {e.response.status_code}")
        except Exception as e:
            if isinstance(e, GisServiceException):
                raise
            logger.error(f"Unexpected error in ArcGisTijuanaProvider: {e}")
            raise GisProviderUnavailableException(f"Internal GIS error: {e}")

    async def get_data_by_coordinates(self, lat: float, lng: float, company_id: Optional[str] = None) -> Optional[PropertyValidationResponse]:
        """
        Queries the FeatureServer using coordinates (point intersection).
        Logs failures or boundaries issues including the company_id for traceability.
        """
        # Point geometry structure
        geometry_json = f'{{"x":{lng},"y":{lat},"spatialReference":{{"wkid":4326}}}}'

        params = {
            "geometry": geometry_json,
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "CLAVE_CAT,USO_SUELO",
            "returnGeometry": "false",
            "f": "json",
            "inSR": "4326"
        }

        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    self.feature_server_url,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                features = data.get("features", [])
                if not features:
                    logger.warning(f"GisOutsideBoundary: Coordinates ({lat}, {lng}) produced no results. [Company: {company_id}]")
                    raise GisOutsideBoundaryException(f"Las coordenadas {lat}, {lng} no intersecan con un predio catastral.")

                feature = features[0]
                clave = feature["attributes"].get("CLAVE_CAT")
                land_use = feature["attributes"].get("USO_SUELO")

                owner_name = await self.get_legal_owner(clave)

                return PropertyValidationResponse(
                    address="Ubicación por Coordenadas", # Placeholder, ideally use Reverse Geocoding
                    cadastral_key=clave,
                    owner_name=owner_name,
                    land_use=land_use,
                    location=Coordinates(lat=lat, lng=lng)
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error querying Catastro: {e}")
            raise GisProviderUnavailableException(f"Service unavailable: {e.response.status_code}")

    async def get_legal_owner(self, cadastral_key: str) -> Optional[str]:
        """
        Scrapes the predial website to retrieve the owner name.
        Uses BeautifulSoup to extract VIEWSTATE before posting the cadastral key.
        """
        if not cadastral_key:
            return None

        try:
            async with httpx.AsyncClient(verify=False) as client:
                # 1. GET request to obtain hidden input tokens like __VIEWSTATE
                get_resp = await client.get(self.predial_url, timeout=self.timeout)
                get_resp.raise_for_status()

                soup = BeautifulSoup(get_resp.text, 'lxml')
                viewstate = soup.find('input', {'id': '__VIEWSTATE'})
                eventvalidation = soup.find('input', {'id': '__EVENTVALIDATION'})
                viewstategenerator = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})

                if not viewstate:
                    logger.warning("Could not find __VIEWSTATE for Predial scraping.")
                    return None

                form_data = {
                    '__VIEWSTATE': viewstate.get('value', '') if viewstate else '',
                    '__EVENTVALIDATION': eventvalidation.get('value', '') if eventvalidation else '',
                    '__VIEWSTATEGENERATOR': viewstategenerator.get('value', '') if viewstategenerator else '',
                    # The name of these specific input fields might depend on the actual form layout.
                    # Using hypothetical IDs based on typical ASP.NET WebForms. 
                    # Assuming a field named 'txtClave' and button 'btnBuscar'
                    'ctl00$ContentPlaceHolder1$txtClaveCatastral': cadastral_key, 
                    'ctl00$ContentPlaceHolder1$btnBuscar': 'Buscar'
                }

                # 2. POST request to submit the form
                post_resp = await client.post(
                    self.predial_url,
                    data=form_data,
                    timeout=self.timeout,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                post_resp.raise_for_status()

                post_soup = BeautifulSoup(post_resp.text, 'lxml')
                
                # Check for "Not Found" messages
                # Find the label or span that holds the owner's name. E.g. 'lblPropietario'.
                # Hypothetical ID for this example
                owner_label = post_soup.find(id='ctl00_ContentPlaceHolder1_lblPropietario')
                
                if owner_label and owner_label.text.strip():
                    return owner_label.text.strip()
                
                # Not found or different HTML structure.
                return "PROPIETARIO NO ENCONTRADO/PARSEO REQUERIDO"

        except Exception as e:
            logger.error(f"Error scraping Predial for owner: {e}")
            return None

