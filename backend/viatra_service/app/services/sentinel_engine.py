"""
SentinelEngine — Worker de monitoreo de precios de vuelos en tiempo real.

Clean Architecture:
  - Recibe IAirlineProvider (interfaz) como dependencia — NO importa modelos ORM
  - Recibe PriceAlertRepository (repositorio) para persistencia — sin commit() en el servicio
  - Usa Duffel como proveedor primario (swappable sin cambiar esta clase)
"""
import uuid
import logging
from decimal import Decimal

from app.domain.ports.flight_price_provider import IAirlineProvider
from app.domain.ports.viatra_repositories import IGroupRepository, IPackageRepository, IPriceAlertRepository

logger = logging.getLogger("SkySentinel")


class SentinelEngine:
    """
    Worker de rastreo de precios de vuelos.
    Detecta bajadas de precio y genera alertas de oportunidad para los viajeros.
    """

    def __init__(
        self, 
        group_repo: IGroupRepository, 
        package_repo: IPackageRepository,
        alert_repo: IPriceAlertRepository,
        airline_provider: IAirlineProvider
    ):
        """
        SkySentinel constructor with Repository Injection.
        """
        self.group_repo = group_repo
        self.package_repo = package_repo
        self.alert_repo = alert_repo
        self.airline_provider = airline_provider

    async def check_flights_prices(self):
        """
        Ciclo principal del SkySentinel:
        1. Obtiene grupos activos con número de vuelo via IGroupRepository
        2. Consulta precio actual via IAirlineProvider
        3. Genera alertas via IPriceAlertRepository
        """
        logger.info("SkySentinel: Iniciando ciclo de rastreo de vuelos...")

        # 1. Cargar grupos activos con vuelo — via repositorio
        groups = await self.group_repo.get_active_groups_with_flights()
        if not groups:
            logger.info("SkySentinel: Sin grupos activos con vuelos. Ciclo completado.")
            return

        for group in groups:
            try:
                # 2. Obtener el paquete para ver precio objetivo via IPackageRepository
                package = await self.package_repo.get_by_id(
                    group.package_id, group.company_id
                )
                if not package or not package.total_price:
                    continue

                base_price = package.total_price.amount if hasattr(package.total_price, 'amount') else Decimal(str(package.total_price))
                target_price = getattr(package, 'target_price', None)
                if not target_price:
                    continue

                # 3. Consulta al proveedor real (Duffel) — NO al mock
                result = await self.airline_provider.get_market_price(
                    flight_number=group.flight_number,
                    base_price=base_price,
                    company_id=str(group.company_id)
                )

                logger.info(
                    f"SkySentinel: Vuelo {group.flight_number} | "
                    f"Mercado: {result.current_price} {result.currency} | "
                    f"Objetivo: {target_price} | Fuente: {result.source}"
                )

                # 4. Generar alerta si hay bajada de precio
                if result.current_price < Decimal(str(target_price)):
                    await self.alert_repo.create_alert({
                        "id": uuid.uuid4(),
                        "company_id": group.company_id,
                        "tenant_id": group.tenant_id if hasattr(group, 'tenant_id') else group.company_id,
                        "package_id": package.id,
                        "group_id": group.id,
                        "flight_number": group.flight_number,
                        "old_price": base_price,
                        "new_price": result.current_price,
                        "currency": result.currency,
                        "alert_type": "FLIGHT_PRICE_DROP",
                        "notes": (
                            f"¡Bajada de precio detectada vía {result.source}! "
                            f"Vuelo {group.flight_number}: "
                            f"{result.current_price} {result.currency} < Target {target_price}"
                        ),
                        "created_by": uuid.UUID(int=0),  # System Bot ID
                    })
                    logger.warning(
                        f"🚨 ALERT: Precio bajo para {group.flight_number}! "
                        f"{result.current_price} < {target_price}"
                    )

            except Exception as e:
                logger.error(f"SkySentinel: Error procesando grupo {group.id}: {e}")
                continue

        logger.info("SkySentinel: Ciclo de rastreo completado.")
