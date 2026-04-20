# Viatra Service Logic Log

Tracking technical decisions, model shifts, and endpoint integrations for the Travel Mission Control.

---

## [v0.9.0] - 2026-03-29 - Stabilization & Multi-Tenant Login Handshake
- **Estabilización de Arquitectura Microservicios**: Sincronización exitosa del secret key (`CORE_SECRET_KEY`) con `auth-service` para la validación transparente de JWTs multi-tenant.
- **Middleware Global de Errores**: Inyección de `InternoCoreGlobalMiddleware` y un manejador centralizado de `StarletteHTTPException` para estandarizar las respuestas de error hacia el frontend (`{"status": "error"}`).
- **Correcciones Core**: Reemplazo de métodos no implementados (`.get_all()`) por la interfaz estándar `.list_all()` en repositorios clave como `GroupRepository` y `PaymentRepository`. Adición exitosa de `/api/v1/payments/history`.
- **Persistencia de Sesión Multi-Tenant**: Extensión de vida del `selection_token` a 24h para permitir cambio fácil de empresa sin re-autenticación OAuth.


## [v0.8.5] - 2026-03-29 - PWA Hardening & Grace Period Strategy
- **Offline-First:** Sincronización con `CacheStorage` para acceso a itinerarios sin conexión.
- **Sentinel Indicators:** LEDs neón dinámicos en Dashboard (SkySentinel/StayGuardian status).
- **Grace Period Logic:** Implementación de "Periodo de Gracia" de 48h en `invoice.payment_failed` para evitar bloqueos inmediatos.
- **Cluster Hardening:** Reubicación a puerto **8011** (host) y estandarización a **8000** (container).
- **SQLAlchemy 2.0 Compliance:** Corrección de importación de `composite` en modelos (migración a `sqlalchemy.orm`).
- **Smoke Tests:** Creación de `scripts/smoke_test.py` para validación de clúster y handshake.
- **Database Sync:** Script `scripts/init_db.py` para creación automática de esquemas en `viatra_db`.


## [v0.7.0] - 2026-03-29 - SkySentinel & StayGuardian Deployment
- **Sentinel Core:** Integración de `APScheduler` para tareas en segundo plano.
- **SkySentinel Engine:** Activación de bot de rastreo de vuelos (6h cycle). Compara `current_price` vs `target_price`.
- **StayGuardian Engine:** Activación de bot de disponibilidad hotelera (12h cycle). Alerta sobre estatus `AT_RISK` o `CANCELLED`.
- **Monitoring:** Nueva ruta `/api/v1/sentinel/status` para métricas de bots (vuelos y hoteles activos).
- **Persistence:** Creación de tablas `PriceAlert` para trazabilidad de anomalías de mercado.

## [v0.5.0-0.6.0] - 2026-03-29 - Payment Reconciliation & Ledger
- **Stripe Webhook Listener:** Implementación de endpoint ciego para eventos `checkout.session.completed` e `invoice.paid`.
- **Async Reconciliation:** Actualización automática del estatus de `TravelerGroup` (PAID/UNPAID) al recibir señales de Stripe.
- **PaymentHistory:** Nueva entidad para auditoría de transacciones financieras vinculadas a empresas y usuarios.
- **Dashboard Unlock Logic:** Endpoint `/status` en `booking.py` para que el frontend detecte el cambio de estado financiero.

## [v0.4.0] — Fintech & Checkout Integration (2026-03-29)
- **Product Mirroring:** Se integró `StripeService` en el flujo de creación de paquetes. Cada `TravelPackage` genera automáticamente un Producto en Stripe.
- **Checkout Sessions:** Creación del endpoint `POST /api/v1/payments/create-checkout-session` con protección de idempotencia.
- **Invariants:** Validación de `Money.amount > 0` en `BookingService`.

## [v0.2.0-0.3.0] — Persistence & Multi-Tenancy
- **Zero-Trust Filtering:** `BaseRepository` inyecta forzosamente el filtro `company_id`.
- **Modelos Core:** `TravelPackage`, `TravelerGroup`, `ItineraryItem`.
- **Endpoints:** CRUD seguro de paquetes y grupos.

## [v0.1.0] — Microservice Scaffold (2026-03-28)
- Inicialización en puerto `8006`.
- Estructura básica de `main.py` y routers declarados.
- Integración con `/common` para multi-tenancy.
