from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

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


@router.post("/full-report", response_model=Any)
async def get_full_report(
    request: CoordsRequest,
    current_user: dict = Depends(get_current_user),
    handler: GetFullPropertyReportQueryHandler = Depends(get_full_report_query_handler)
) -> Any:
    """Busca clave, propietario, superficie y dirección unificada por coordenadas."""
    try:
        company_id = current_user.get("company_id")
        query = GetFullPropertyReportQuery(lat=request.lat, lng=request.lng, company_id=company_id)
        result = await handler.handle(query)
        
        # Format for final response as per spec
        return {
            "clave": result.cadastral_key,
            "propietario": result.owner_name,
            "superficie": result.meta.get("superficie") if result.meta else 0.0,
            "direccion_catastral": result.address
        }
    except GisServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error in full-report: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
