import pytest
from unittest.mock import AsyncMock, patch

from common.gis.domain.dtos import PropertyValidationResponse, Coordinates
from common.gis.infrastructure.services.arcgis_tijuana_provider import ArcGisTijuanaProvider
from common.gis.application.queries.get_property_data import (
    GetPropertyDataByCoordinatesQuery,
    GetPropertyDataByCoordinatesQueryHandler,
    GetPropertyDataByAddressQuery,
    GetPropertyDataByAddressQueryHandler
)

@pytest.fixture
def mock_gis_provider():
    provider = ArcGisTijuanaProvider()
    
    async def mock_get_location_by_address(address_string: str):
        if "6319-C" in address_string:
            return PropertyValidationResponse(
                address=address_string,
                cadastral_key="PK020119",
                owner_name="PROPIETARIO SIMULADO",
                land_use="Habitacional",
                location=Coordinates(lat=32.49081, lng=-116.90954)
            )
        return None

    provider.get_location_by_address = AsyncMock(side_effect=mock_get_location_by_address)
    provider.get_data_by_coordinates = AsyncMock(return_value=PropertyValidationResponse(
        address="Ubicación por Coordenadas",
        cadastral_key="PK020119",
        owner_name="PROPIETARIO SIMULADO",
        land_use="Habitacional",
        location=Coordinates(lat=32.49081, lng=-116.90954)
    ))
    return provider

@pytest.mark.asyncio
async def test_get_property_by_address(mock_gis_provider):
    handler = GetPropertyDataByAddressQueryHandler(gis_service=mock_gis_provider)
    query = GetPropertyDataByAddressQuery(address_string="Venustiano Carranza 6319-C", company_id="TEST_CO")
    
    result = await handler.handle(query)
    
    assert result is not None
    assert result.cadastral_key == "PK020119"
    assert result.owner_name == "PROPIETARIO SIMULADO"

@pytest.mark.asyncio
async def test_get_property_by_coordinates(mock_gis_provider):
    handler = GetPropertyDataByCoordinatesQueryHandler(gis_service=mock_gis_provider)
    query = GetPropertyDataByCoordinatesQuery(lat=32.49081, lng=-116.90954, company_id="TEST_CO")
    
    result = await handler.handle(query)
    
    assert result is not None
    assert result.cadastral_key == "PK020119"
    assert result.location.lat == 32.49081
