"""
DuffelHotelAdapter — Implementación primaria de IHotelAvailabilityProvider usando Duffel Stays API.

Duffel Stays: https://duffel.com/docs/api/stays
- Misma API key que vuelos (DUFFEL_API_TOKEN)
- POST /stays/search → busca hoteles disponibles
- Reemplaza Amadeus Hotel Search (que pasa a Enterprise en julio 2026)
"""
import logging
import httpx
from typing import Optional
from datetime import datetime, timedelta

from app.domain.ports.hotel_availability_provider import IHotelAvailabilityProvider, HotelAvailabilityResult
from app.core.config import get_settings

logger = logging.getLogger("DuffelHotelAdapter")

DUFFEL_BASE_URL = "https://api.duffel.com"
DUFFEL_API_VERSION = "v2"


class DuffelHotelAdapter(IHotelAvailabilityProvider):
    """
    Adaptador Duffel Stays para verificación de disponibilidad hotelera.
    Usa el mismo API token que DuffelAirlineAdapter — una sola credencial para todo.
    """

    def __init__(self):
        self._settings = get_settings()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._settings.DUFFEL_API_TOKEN}",
            "Duffel-Version": DUFFEL_API_VERSION,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def check_availability(
        self,
        confirmation_number: str,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None
    ) -> HotelAvailabilityResult:
        """
        Verifica disponibilidad hotelera en Duffel Stays.
        El confirmation_number se usa como referencia del itinerario.
        Para busqueda en tiempo real, se usa la ciudad/coordenadas del ItineraryItem.
        """
        # Fechas por defecto: próxima semana (ventana de monitoreo)
        if not check_in:
            check_in = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        if not check_out:
            check_out = (datetime.utcnow() + timedelta(days=8)).strftime("%Y-%m-%d")

        payload = {
            "data": {
                "check_in_date": check_in,
                "check_out_date": check_out,
                "rooms": 1,
                "guests": [{"type": "adult"}],
                # Búsqueda por referencia del hotel — en producción se usa el property_id de Duffel
                "accommodation_id": confirmation_number,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{DUFFEL_BASE_URL}/stays/search",
                    json=payload,
                    headers=self._headers(),
                )

            if response.status_code == 200:
                data = response.json()
                results = data.get("data", {}).get("results", [])

                if results:
                    best = results[0]
                    cheapest_rate = None
                    rates = best.get("cheapest_rate_total_amount")
                    if rates:
                        cheapest_rate = float(rates)

                    available_rooms = len(results)
                    status = "CONFIRMED" if available_rooms > 0 else "SOLD_OUT"

                    logger.info(
                        f"DuffelHotelAdapter: {confirmation_number} | "
                        f"Status: {status} | Rooms: {available_rooms} | Rate: {cheapest_rate}"
                    )

                    return HotelAvailabilityResult(
                        hotel_id=best.get("accommodation", {}).get("id", confirmation_number),
                        confirmation_number=confirmation_number,
                        status=status,
                        available_rooms=available_rooms,
                        lowest_rate=cheapest_rate,
                        currency=best.get("cheapest_rate_currency", "USD"),
                        source="DUFFEL_STAYS",
                    )

            elif response.status_code == 404:
                logger.warning(f"DuffelHotelAdapter: Hotel {confirmation_number} no encontrado (404).")
                return HotelAvailabilityResult(
                    hotel_id=confirmation_number,
                    confirmation_number=confirmation_number,
                    status="AT_RISK",
                    available_rooms=0,
                    source="DUFFEL_NOT_FOUND",
                )

            logger.warning(
                f"DuffelHotelAdapter: Sin resultados para {confirmation_number}. "
                f"HTTP {response.status_code}"
            )
            return HotelAvailabilityResult(
                hotel_id=confirmation_number,
                confirmation_number=confirmation_number,
                status="SOLD_OUT",
                available_rooms=0,
                source="DUFFEL_NO_RESULTS",
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"DuffelHotelAdapter: HTTP error {e.response.status_code}: {e}")
            return HotelAvailabilityResult(
                hotel_id=confirmation_number,
                confirmation_number=confirmation_number,
                status="AT_RISK",
                available_rooms=0,
                source="FALLBACK_HTTP_ERROR",
            )
        except Exception as e:
            logger.error(f"DuffelHotelAdapter: Error inesperado para {confirmation_number}: {e}")
            return HotelAvailabilityResult(
                hotel_id=confirmation_number,
                confirmation_number=confirmation_number,
                status="AT_RISK",
                available_rooms=0,
                source="FALLBACK_EXCEPTION",
            )
