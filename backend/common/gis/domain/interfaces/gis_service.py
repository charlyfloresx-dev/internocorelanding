from decimal import Decimal
from abc import ABC, abstractmethod
from typing import Optional
from common.gis.domain.dtos import PropertyValidationResponse

class IGisService(ABC):
    @abstractmethod
    async def get_location_by_address(self, address_string: str) -> Optional[PropertyValidationResponse]:
        """Busca información cartográfica y registral usando una dirección en texto libre."""
        pass

    @abstractmethod
    async def get_data_by_coordinates(self, lat: float, lng: float, company_id: Optional[str] = None) -> Optional[PropertyValidationResponse]:
        """Consulta el FeatureServer espacialmente por latitud y longitud."""
        pass

    @abstractmethod
    async def get_legal_owner(self, cadastral_key: str) -> Optional[str]:
        """Realiza el cruce con el Registro Público o Recaudación para obtener el dueño legal."""
        pass
