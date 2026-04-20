from dataclasses import dataclass
from typing import Optional

from common.cqrs import IQuery, IQueryHandler
from common.gis.domain.interfaces.gis_service import IGisService
from common.gis.domain.dtos import PropertyValidationResponse

@dataclass
class GetPropertyDataByCoordinatesQuery(IQuery[PropertyValidationResponse]):
    lat: float
    lng: float
    company_id: str

class GetPropertyDataByCoordinatesQueryHandler(IQueryHandler[PropertyValidationResponse]):
    def __init__(self, gis_service: IGisService):
        self._gis_service = gis_service

    async def handle(self, query: GetPropertyDataByCoordinatesQuery) -> PropertyValidationResponse:
        return await self._gis_service.get_data_by_coordinates(
            lat=query.lat,
            lng=query.lng,
            company_id=query.company_id
        )

@dataclass
class GetPropertyDataByAddressQuery(IQuery[PropertyValidationResponse]):
    address_string: str
    company_id: str

class GetPropertyDataByAddressQueryHandler(IQueryHandler[PropertyValidationResponse]):
    def __init__(self, gis_service: IGisService):
        self._gis_service = gis_service

    async def handle(self, query: GetPropertyDataByAddressQuery) -> PropertyValidationResponse:
        # Pasa el address al servicio
        return await self._gis_service.get_location_by_address(address_string=query.address_string)
