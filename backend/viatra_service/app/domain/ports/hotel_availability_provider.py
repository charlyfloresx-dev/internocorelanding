from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class HotelAvailabilityResult:
    """DTO de disponibilidad hotelera — agnóstico del proveedor."""
    hotel_id: str
    confirmation_number: str
    status: str               # CONFIRMED | AT_RISK | CANCELLED | SOLD_OUT
    available_rooms: int
    lowest_rate: Optional[float] = None
    currency: str = "USD"
    source: str = "UNKNOWN"


class IHotelAvailabilityProvider(ABC):
    """
    Puerto de dominio para verificación de disponibilidad hotelera en tiempo real.
    Desacopla StayGuardian de cualquier proveedor específico (Amadeus, Expedia, Hotelbeds, etc.).
    """

    @abstractmethod
    async def check_availability(
        self,
        confirmation_number: str,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None
    ) -> HotelAvailabilityResult:
        """
        Verifica la disponibilidad de una reserva hotelera.
        :param confirmation_number: Número de confirmación de la reserva
        :param check_in: Fecha de check-in (YYYY-MM-DD)
        :param check_out: Fecha de check-out (YYYY-MM-DD)
        :return: HotelAvailabilityResult con estatus y detalles del proveedor
        """
        ...
