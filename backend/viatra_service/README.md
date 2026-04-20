# Viatra Core — Travel Mission Control Engine (v0.9.0)

Este microservicio gestiona la logística compleja de grupos de viaje, el motor de reservas (`Booking Engine`) y el rastreo de activos mediante Sentinel Bots.

## Responsabilidades
1. **Booking Engine:** Gestión de paquetes, itinerarios y asignación de asientos.
2. **Fintech Logic:** Cálculo de cuotas mensuales y conexión con Stripe para pagos recurrentes. Incluye **Periodo de Gracia (48h)** para pagos fallidos.
3. **SkySentinel:** Monitoreo activo de vuelos y variaciones de precio en tiempo real.
4. **StayGuardian:** Centinela de disponibilidad hotelera y bloques de habitaciones.
5. **Price Intelligence:** Sugerencia de fechas óptimas y "Discovery Mode" para maximizar márgenes de utilidad.
6. **Document Vault:** Generación de itinerarios certificados en PDF con soporte Offline PWA.

## Stack Tecnológico
- **Core:** FastAPI 0.115+
- **Database:** SQLAlchemy 2.0 (Async/Postgres)
- **Shared Domain:** Montaje de `/common` para modelos base e invariantes de multi-tenancy.
- **Port Unit:** `8011` (Cluster Internal: 8000)

## Sentinel Engine (APScheduler)
Los bots operan en ciclos programados:
- **SkySentinel:** Cada 6 horas (Precios de vuelos y Discovery Mode).
- **StayGuardian:** Cada 12 horas (Cupos hoteleros y Allotments).

## Sentinel Reactivo (Financial Guard)
Además de los ciclos programados, el sistema cuenta con un centinela invisible:
- **Stripe Webhook Listener:** Actúa como un vigilante financiero 24/7. Detecta fallos de pago para activar el **Periodo de Gracia (48h)** y desbloquea el acceso a itinerarios tras la confirmación de fondos, garantizando la continuidad operativa.


## Documentación de Estrategia
Para detalles sobre cómo el motor compite con consolidadores globales, consulta:
`docs/strategies/FLIGHT_PRICING_STRATEGIES.md`

## Estructura de Seguridad (Zero-Trust)
Este servicio aplica un filtro automático por `company_id` a nivel de Repositorio. Ninguna consulta de lectura o escritura puede acceder a datos que no pertenezcan al Tenant del usuario autenticado, garantizando el aislamiento total en una arquitectura SaaS.

## Desarrollo Local (Docker)
Este servicio se orquesta mediante el `docker-compose.yml` en la raíz del proyecto.
```bash
docker compose up -d viatra-service
```
Y valida el clúster con el Smoke Test:
```bash
python scripts/smoke_test.py
```
