"""
DuffelAirlineAdapter — Implementación primaria de IAirlineProvider usando Duffel API.

Duffel: https://duffel.com/docs/api
- Self-Service permanente (no cierra como Amadeus Self-Service en julio 2026)
- REST moderno: vuelos + hospedaje en un solo API
- Auth: Bearer token (DUFFEL_API_TOKEN)

Endpoints usados:
  - POST /air/offer_requests     → Inicia búsqueda de vuelos
  - GET  /air/offers             → Obtiene las ofertas
"""
import logging
import httpx
from decimal import Decimal
from typing import Optional, List

from app.domain.ports.flight_price_provider import IAirlineProvider, FlightOffer, FlightPriceResult
from app.core.config import get_settings

logger = logging.getLogger("DuffelAirlineAdapter")

DUFFEL_BASE_URL = "https://api.duffel.com"
DUFFEL_API_VERSION = "v2"


class DuffelAirlineAdapter(IAirlineProvider):
    """
    Adaptador Duffel para búsqueda de vuelos y monitoreo de precios.
    Usa el API REST de Duffel con autenticación Bearer token.
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

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        company_id: Optional[str] = None
    ) -> List[FlightOffer]:
        """
        Crea un OfferRequest en Duffel y retorna las ofertas mapeadas a FlightOffer.
        Flujo: POST /air/offer_requests -> GET /air/offers?offer_request_id=XXX
        """
        payload = {
            "data": {
                "slices": [
                    {
                        "origin": origin,
                        "destination": destination,
                        "departure_date": departure_date,
                    }
                ],
                "passengers": [{"type": "adult"} for _ in range(adults)],
                "cabin_class": "economy",
            }
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # 1. Crear OfferRequest
                req_resp = await client.post(
                    f"{DUFFEL_BASE_URL}/air/offer_requests",
                    json=payload,
                    headers=self._headers(),
                    params={"return_offers": "true"},  # Retorna ofertas en una sola llamada
                )
                req_resp.raise_for_status()
                data = req_resp.json()

            offers_raw = data.get("data", {}).get("offers", [])
            offers: List[FlightOffer] = []

            for raw in offers_raw[:20]:  # Limitamos a 20 resultados
                try:
                    slices = raw.get("slices", [{}])
                    first_slice = slices[0] if slices else {}
                    segments = first_slice.get("segments", [{}])
                    first_seg = segments[0] if segments else {}

                    total_price = Decimal(str(raw.get("total_amount", "0")))
                    currency = raw.get("total_currency", "USD")
                    airline = first_seg.get("marketing_carrier", {}).get("iata_code", "??")
                    flight_num = first_seg.get("marketing_carrier_flight_number", "")
                    seats = raw.get("available_services", [])

                    offers.append(FlightOffer(
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        airline=airline,
                        flight_number=f"{airline}{flight_num}",
                        price=total_price,
                        currency=currency,
                        available_seats=len(seats) if seats else 9,
                        provider_offer_id=raw.get("id"),
                        source="DUFFEL",
                    ))
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"DuffelAirlineAdapter: Error mapeando oferta: {e}")
                    continue

            logger.info(
                f"DuffelAirlineAdapter: {origin}->{destination} | {departure_date} | "
                f"{len(offers)} ofertas encontradas"
            )
            return sorted(offers, key=lambda o: o.price)

        except httpx.HTTPStatusError as e:
            logger.error(f"DuffelAirlineAdapter: HTTP {e.response.status_code} en search_flights: {e}")
            return []
        except Exception as e:
            logger.error(f"DuffelAirlineAdapter: Error inesperado en search_flights: {e}")
            return []

    async def get_market_price(
        self,
        flight_number: str,
        base_price: Decimal,
        company_id: Optional[str] = None
    ) -> FlightPriceResult:
        """
        Obtiene el precio de mercado actual para un vuelo.
        Usado por SentinelEngine para detectar bajadas de precio y generar alertas.
        Extrae el carrier e infiere ruta MEX→LAX como referencia de mercado.
        """
        # Extrae IATA carrier del número de vuelo (ej. 'AM123' -> 'AM')
        carrier = flight_number[:2].upper() if len(flight_number) >= 2 else "XX"

        # Referencia de mercado: búsqueda para próximos 30 días
        from datetime import datetime, timedelta
        ref_date = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")

        offers = await self.search_flights(
            origin="MEX",
            destination="LAX",
            departure_date=ref_date,
            adults=1,
            company_id=company_id
        )

        # Filtrar por carrier si hay resultados
        carrier_offers = [o for o in offers if o.airline == carrier]
        candidates = carrier_offers if carrier_offers else offers

        if candidates:
            min_price = min(o.price for o in candidates)
            currency = candidates[0].currency
            logger.info(
                f"DuffelAirlineAdapter: Precio mercado {flight_number} = "
                f"{min_price} {currency} (base: {base_price})"
            )
            return FlightPriceResult(
                flight_number=flight_number,
                current_price=min_price,
                currency=currency,
                source="DUFFEL",
            )

        # Fallback sin datos de mercado
        logger.warning(
            f"DuffelAirlineAdapter: Sin precios para {flight_number}. Usando base: {base_price}"
        )
        return FlightPriceResult(
            flight_number=flight_number,
            current_price=base_price,
            currency="USD",
            source="FALLBACK_NO_DATA",
        )
