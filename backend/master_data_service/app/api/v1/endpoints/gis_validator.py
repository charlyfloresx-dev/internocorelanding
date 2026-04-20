from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from common.security.dependencies import get_current_user
from common.gis.infrastructure.services.arcgis_tijuana_provider import ArcGisTijuanaProvider
from common.gis.application.queries.get_property_data import (
    GetPropertyDataByCoordinatesQuery,
    GetPropertyDataByCoordinatesQueryHandler,
    GetPropertyDataByAddressQuery,
    GetPropertyDataByAddressQueryHandler
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
