"""
StayGuardian — Worker de monitoreo de disponibilidad hotelera en tiempo real.

Clean Architecture:
  - Recibe IHotelAvailabilityProvider (interfaz) como dependencia — sin modelos ORM
  - Recibe ItineraryRepository para leer datos — sin AsyncSession en el servicio
  - Usa Duffel Stays como proveedor primario (swappable sin cambiar esta clase)
"""
import uuid
import logging
from decimal import Decimal

from app.domain.ports.viatra_repositories import IItineraryRepository, IPriceAlertRepository
from app.domain.ports.hotel_availability_provider import IHotelAvailabilityProvider

logger = logging.getLogger("StayGuardian")


class StayGuardian:
    """
    Worker de monitoreo de disponibilidad hotelera.
    Detecta habitaciones AT_RISK o CANCELLED y genera alertas operacionales.
    """

    def __init__(
        self, 
        itinerary_repo: IItineraryRepository, 
        alert_repo: IPriceAlertRepository,
        hotel_provider: IHotelAvailabilityProvider
    ):
        """
        StayGuardian constructor with Repository Injection.
        """
        self.itinerary_repo = itinerary_repo
        self.alert_repo = alert_repo
        self.hotel_provider = hotel_provider

    async def check_hotel_availability(self):
        """
        Ciclo principal del StayGuardian:
        1. Obtiene ItineraryItems de tipo ACCOMMODATION via IItineraryRepository
        2. Verifica disponibilidad via IHotelAvailabilityProvider (Duffel Stays)
        3. Crea alertas vía repositorio (alert_repo) para AT_RISK o CANCELLED
        """
        logger.info("StayGuardian: Iniciando monitoreo de bloques hoteleros...")

        # 1. Obtener itinerarios de tipo hotel — via repositorio
        items = await self.itinerary_repo.get_active_accommodations()
        if not items:
            logger.info("StayGuardian: Sin itinerarios ACCOMMODATION activos.")
            return

        for item in items:
            try:
                # 2. Consulta a Duffel Stays en tiempo real
                result = await self.hotel_provider.check_availability(
                    confirmation_number=item.confirmation_number or item.name,
                    check_in=item.check_in_date.strftime("%Y-%m-%d") if item.check_in_date else None,
                    check_out=item.check_out_date.strftime("%Y-%m-%d") if item.check_out_date else None
                )

                logger.info(
                    f"StayGuardian: Hotel '{item.name}' | Status: {result.status} | "
                    f"Rooms: {result.available_rooms} | Fuente: {result.source}"
                )

                # 3. Generar alerta si hay riesgo
                if result.status in ("AT_RISK", "CANCELLED", "SOLD_OUT"):
                    await self.alert_repo.create_alert({
                        "id": uuid.uuid4(),
                        "company_id": item.company_id,
                        "tenant_id": item.tenant_id if hasattr(item, 'tenant_id') else item.company_id,
                        "package_id": item.package_id,
                        "group_id": item.group_id,
                        "flight_number": "N/A (HOTEL)",
                        "old_price": Decimal("0"),
                        "new_price": Decimal(str(result.lowest_rate)) if result.lowest_rate else Decimal("0"),
                        "currency": result.currency,
                        "alert_type": f"HOTEL_{result.status}",
                        "notes": (
                            f"[{result.source}] Hotel '{item.name}' para Grupo {item.group_id} "
                            f"reporta estatus: {result.status}. "
                            f"Habitaciones disponibles: {result.available_rooms}."
                        ),
                        "created_by": uuid.UUID(int=0),  # System Bot ID
                    })
                    logger.warning(
                        f"🚨 URGENCIA HOTEL: '{item.name}' Grupo {item.group_id} "
                        f"→ {result.status} (Fuente: {result.source})"
                    )

            except Exception as e:
                logger.error(f"StayGuardian: Error procesando itinerario {item.id}: {e}")
                continue

        logger.info("StayGuardian: Monitoreo hotelero completado.")
