# ✈️ Estrategias de Precios de Vuelos (Viatra Core)

Este documento detalla cómo el ecosistema Viatra Core automatiza el mantenimiento de precios competitivos y la optimización de márgenes para las agencias.

## 1. Comparativa: Agencia Tradicional vs. Viatra Core

| Estrategia | Agencia Tradicional | Viatra Core (Sentinel Engine) |
| :--- | :--- | :--- |
| **Bloqueo de Precio** | Manual en GDS (24-72h). | **Sentinel Lock:** Automático y vigilado cada 6h. |
| **Seguridad de Estancia** | Control manual de bloques. | **StayGuardian:** Monitoreo de estatus `AT_RISK` cada 12h. |
| **Sugerencia de Fechas** | Basada en experiencia humana. | **Discovery Mode:** Análisis ±7 días para encontrar el "Low-Peak". |
| **Riesgo de Cambio** | Alta volatilidad sin aviso. | **AuditBase:** Registro histórico y alertas de "Price Drop". |
| **Vigilancia Financiera** | Revisión manual de bancos. | **Tercer Centinela:** Webhook de Stripe con desbloqueo automático. |

## 2. SkySentinel: Discovery Mode
El Sentinel no solo vigila una ruta fija, sino que actúa como un asesor de planificación:
- **Búsqueda en Abanico:** Al recibir una solicitud para una ruta (ej. México -> Colombia), el bot escanea precios en una ventana de ±7 días.
- **Identificación de IATA:** Traduce automáticamente destinos ("Colombia") a hubs principales (BOG, MDE, CLO) para maximizar opciones.
- **Recomendación Estratégica:** Si mover el viaje 2 días incrementa el margen de la agencia en un 15%, el sistema dispara una sugerencia en el Dashboard de creación de grupos.

## 3. StayGuardian: El Protector de Estancia
Centinela encargado de la seguridad de los activos inmobiliarios y reservas de hotel:
- **Vigilancia de ACCOMMODATION:** Valida el estatus de bloques con proveedores.
- **Aislamiento Multitenant:** Garantiza que los asientos comprados para la "Empresa A" no puedan ser visualizados o utilizados por la "Empresa B".

## 4. El Tercer Centinela (Invisible): Financial Guard
Aunque no es un bot de rastreo externo, el Stripe Webhook Listener actúa como el centinela de la liquidez:
- **Vigilancia de Eventos:** Monitorea en tiempo real fallos (`payment_failed`) o éxitos (`paid`).
- **Periodo de Gracia:** Activa automáticamente las 48h de protección si el pago falla, evitando la cancelación de la logística.
- **Activación "Mágica":** Desbloquea el acceso al itinerario y activos en el Dashboard instantáneamente al detectar el éxito financiero.

## 5. Implementación Técnica
La lógica reside en `viatra_service/app/services/sentinel_engine.py`, donde se inyectan los metadatos del itinerario para definir la "misión" de búsqueda:
1. Extrae `origin` y `destination` del `TravelerGroup`.
2. Consulta tendencias históricas y actuales vía API/GDS.
3. Cachea resultados en Redis/DB para optimizar costos de consulta.

---
*Versión: 0.9.0*
*Referencia: VIATRA-STRAT-2026*