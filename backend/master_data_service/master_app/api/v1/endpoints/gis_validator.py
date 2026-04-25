from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
import httpx

from common.security.dependencies import get_current_user
from common.logger import get_logger
from common.gis.infrastructure.services.arcgis_tijuana_provider import ArcGisTijuanaProvider

logger = get_logger(__name__)
from common.gis.application.queries.get_property_data import (
    GetPropertyDataByCoordinatesQuery,
    GetPropertyDataByCoordinatesQueryHandler,
    GetPropertyDataByAddressQuery,
    GetPropertyDataByAddressQueryHandler,
    GetFullPropertyReportQuery,
    GetFullPropertyReportQueryHandler
)
from common.gis.domain.exceptions import GisServiceException

router = APIRouter()

# URL del Asset Manager Service — se configura via env en Docker
ASSET_MANAGER_URL = "http://asset-manager-service:8006"

# En un sistema maduro, inyectaríamos via contenedor DI
# Para este MS, instanciamos el handler directamente.
def get_coor_query_handler():
    # Instanciar el provider
    provider = ArcGisTijuanaProvider()
    return GetPropertyDataByCoordinatesQueryHandler(gis_service=provider)

def get_address_query_handler():
    provider = ArcGisTijuanaProvider()
    return GetPropertyDataByAddressQueryHandler(gis_service=provider)

def get_full_report_query_handler():
    provider = ArcGisTijuanaProvider()
    return GetFullPropertyReportQueryHandler(gis_service=provider)


class CoordsRequest(BaseModel):
    lat: float
    lng: float

class AddressRequest(BaseModel):
    address_string: str


@router.post("/validate-coordinates", response_model=Any)
async def validate_by_coordinates(
    request: CoordsRequest,
    current_user: dict = Depends(get_current_user),
    handler: GetPropertyDataByCoordinatesQueryHandler = Depends(get_coor_query_handler)
) -> Any:
    """Busca clave catastral y dueño a partir de latitud y longitud."""
    try:
        company_id = current_user.get("company_id")
        query = GetPropertyDataByCoordinatesQuery(lat=request.lat, lng=request.lng, company_id=company_id)
        result = await handler.handle(query)
        if not result:
            raise HTTPException(status_code=404, detail="No se encontraron datos.")
        return result
    except GisServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/validate-address", response_model=Any)
async def validate_by_address(
    request: AddressRequest,
    current_user: dict = Depends(get_current_user),
    handler: GetPropertyDataByAddressQueryHandler = Depends(get_address_query_handler)
) -> Any:
    """Busca clave catastral y dueño a partir de una dirección en texto libre."""
    try:
        company_id = current_user.get("company_id")
        query = GetPropertyDataByAddressQuery(address_string=request.address_string, company_id=company_id)
        result = await handler.handle(query)
        if not result:
            raise HTTPException(status_code=404, detail="No se encontraron datos.")
        return result
    except GisServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def _propagate_to_asset_manager(report_payload: dict, user_id: str | None) -> None:
    """
    BackgroundTask: Envía el reporte GIS al Asset Manager Service para evaluación
    financiera automática. Se ejecuta en background — NO bloquea la respuesta a Indiana.
    Si el servicio CRM no está disponible, solo lo registra en log (no lanza excepción).
    """
    try:
        payload = {**report_payload, "created_by": user_id}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{ASSET_MANAGER_URL}/api/v1/opportunities/evaluate",
                json=payload,
            )
            if response.status_code in (200, 201):
                logger.info(f"[GIS→CRM] Predio {report_payload.get('cve_cat')} propagado al Asset Manager. ROI calculado.")
            else:
                logger.warning(f"[GIS→CRM] Asset Manager respondió {response.status_code} para {report_payload.get('cve_cat')}")
    except Exception as e:
        # No propagamos el error — el mapa de Indiana ya respondió correctamente
        logger.warning(f"[GIS→CRM] BackgroundTask falló (CRM puede estar offline): {e}")


@router.post("/full-report", response_model=Any)
async def get_full_report(
    request: CoordsRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    handler: GetFullPropertyReportQueryHandler = Depends(get_full_report_query_handler)
) -> Any:
    """Busca clave, propietario, superficie y dirección unificada por coordenadas.
    
    Además de responder al frontend, lanza una BackgroundTask que propaga
    los datos al Asset Manager Service para evaluación financiera automática.
    """
    try:
        company_id = current_user.get("company_id")
        user_id = current_user.get("user_id")
        query = GetFullPropertyReportQuery(lat=request.lat, lng=request.lng, company_id=company_id)
        result = await handler.handle(query)
        
        # Format for final response as per spec
        report_data = {
            "cve_cat": result.cadastral_key,
            "propietario": result.owner_name,
            "superficie": result.meta.get("superficie") if result.meta else 0.0,
            "direccion_catastral": result.address,
            "lat": request.lat,
            "lng": request.lng,
            "folio_real": result.meta.get("rppc_info", {}).get("FolioReal") if result.meta else None,
            "colonia": result.meta.get("colonia") if result.meta else None,
        }

        # ── BackgroundTask: Propaga al CRM sin bloquear el mapa ───────────
        background_tasks.add_task(_propagate_to_asset_manager, report_data, user_id)
        
        return report_data

    except GisServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error in full-report: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
