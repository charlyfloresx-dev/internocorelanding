"""
IAirlineProvider — Puerto de dominio para búsqueda y monitoreo de vuelos.

Agnóstico del proveedor. Soporta:
  - Duffel API (implementación primaria, self-service permanente)
  - Amadeus Enterprise (skeleton para clientes con contrato)
  - Skyscanner / Kiwi Tequila (adaptadores futuros)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List


@dataclass
class FlightOffer:
    """DTO de oferta de vuelo — agnóstico del proveedor."""
    origin: str
    destination: str
    departure_date: str
    airline: str
    flight_number: str
    price: Decimal
    currency: str
    available_seats: int
    duration_minutes: Optional[int] = None
    provider_offer_id: Optional[str] = None
    source: str = "UNKNOWN"


@dataclass
class FlightPriceResult:
    """DTO de precio actual de vuelo para rastreo (SentinelEngine)."""
    flight_number: str
    current_price: Decimal
    currency: str
    source: str = "UNKNOWN"
    origin: Optional[str] = None
    destination: Optional[str] = None


class IAirlineProvider(ABC):
    """
    Puerto de dominio para operaciones aeronáuticas.
    SentinelEngine y BookingService dependen SÓLO de esta interfaz.
    """

    @abstractmethod
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        company_id: Optional[str] = None
    ) -> List[FlightOffer]:
        """
        Busca ofertas de vuelo disponibles.
        :param origin: Código IATA de origen (ej. 'MEX')
        :param destination: Código IATA de destino (ej. 'LAX')
        :param departure_date: Fecha de salida (YYYY-MM-DD)
        :param adults: Número de pasajeros adultos
        :param company_id: Tenant ID para credenciales multi-tenant
        :return: Lista de FlightOffer ordenada por precio
        """
        ...

    @abstractmethod
    async def get_market_price(
        self,
        flight_number: str,
        base_price: Decimal,
        company_id: Optional[str] = None
    ) -> FlightPriceResult:
        """
        Obtiene el precio de mercado actual de un vuelo específico.
        Usado por SentinelEngine para detectar variaciones de precio.
        :param flight_number: Número IATA (ej. 'AM123')
        :param base_price: Precio base del paquete como referencia
        :return: FlightPriceResult con precio actual del mercado
        """
        ...
