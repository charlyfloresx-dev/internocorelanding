# 🛠️ Engineering Log - Interno Core

## [2026-02-23] Arquitectura de Resiliencia y Telemetría UI

### 1. Cambio Arquitectónico: Offline-First (Read-Only)
Se ha implementado un patrón de **Cache-Then-Fallback** en los servicios críticos del frontend (`MasterDataService`, `WmsService`).
- **Comportamiento:**
  - Las peticiones exitosas guardan la respuesta en `localStorage` con prefijo `interno_cache_`.
  - Si la API falla (Status 0, 500, 404), el servicio intercepta el error y retorna los datos cacheados usando `of()`.
  - Esto permite que la aplicación siga siendo funcional en modo lectura incluso si los microservicios de backend están caídos.

### 2. Nuevo Componente: SystemHealthService
Se creó un servicio centralizado (`src/app/core/services/system-health.service.ts`) para monitorear el estado de los microservicios.
- **Estados:**
  - 🟢 **Online:** Todos los servicios responden (`auth`, `masterData`, `wms`).
  - 🟡 **Degraded:** Fallo en servicios de datos (WMS/MasterData). Se sirve contenido de caché.
  - 🔴 **Offline:** Fallo en `AuthService`. Bloqueo crítico.
- **Signal `isReadOnly`:** Computado global que se activa cuando el estado no es `online`. Deshabilita botones de escritura (Guardar/Crear) en toda la UI.

### 3. Correcciones de API (OpenAPI Sync)
- **Master Data:** Se corrigió la ruta de Unidades de Medida de `/uoms/` a `/api/v1/ums/` para coincidir con la especificación del backend.

### 4. Variables de Entorno y Testing
- **Puerto WMS:**
  - Producción/Dev: `8002`
  - Testing de Resiliencia: `8099` (Simula caída para verificar estado Ámbar).

### 5. Deuda Técnica / Pendientes (Próxima Sesión)
- **UI Debug:** El indicador "Foquito" en `HeaderComponent` no es visible. Revisar estilos Tailwind/Z-Index.
- **Validación de Hidratación:** Confirmar que las tablas se llenan correctamente desde `localStorage` tras un reinicio simulado.

---

## [2026-02-24] UI Telemetry & Write-Lock Implementation

### 1. UI Telemetry (Health Badge)
- **Componente:** `SystemHealthService` ahora actúa como el sistema nervioso central para la reactividad de la UI a la salud del backend.
- **Integración:** `MasterDataService` y `WmsService` ahora reportan activamente su estado (activo/caído) al `SystemHealthService` en cada llamada a la API (éxito o `catchError`).
- **Feedback Visual:** El "foquito" del avatar (Health Badge) en el `HeaderComponent` es ahora completamente reactivo:
  - 🟢 **Online:** Todos los servicios responden.
  - 🟡 **Degraded:** Un servicio de datos (WMS/MasterData) ha fallado; el sistema opera desde el caché.
  - 🔴 **Offline:** El `AuthService` es inalcanzable.

### 2. Bloqueo de Escritura en Modo Degradado
- **Mecanismo:** Se ha implementado un nuevo signal computado `isReadOnly` dentro de `SystemHealthService`. Devuelve `true` si `overallStatus` no es `'online'`.
- **Impacto:** Este signal es consumido por los componentes de formularios (ej. "Crear Producto") para deshabilitar los botones de "Guardar" y mostrar un mensaje de advertencia.
- **Propósito:** Prevenir la inconsistencia de datos al bloquear operaciones de escritura cuando uno o más microservicios no están disponibles, forzando un modo de "solo lectura" durante las interrupciones.

---

## [2026-03-06] Notification Infrastructure & Templating (Phase 10.5 & 10.6)

### 1. Delivery Infrastructure (Real Providers)
- **Email (Resend):** Integrated the official Resend SDK for transactional emails.
- **SMS (Mock):** Implemented a mock provider for SMS to prepare for future Twilio/AWS integration.
- **Fail-Safe Dispatch:** Refactored `event_routes.py` to handle provider errors gracefully, marking notifications as `FAILED` without breaking the event loop.

### 2. Professional HTML Templating
- **Template Service:** Created a Jinja2-based `TemplateService` to render professional HTML emails.
- **Base Layout:** Implemented `base_layout.html` with inline CSS for cross-client compatibility.
- **Logo Integration:** The `InternoCoreSVGBlack.svg` logo is now embedded as a **Base64 Data URI** in all emails, ensuring visibility and branding consistency.

### 3. Multi-tenancy & Traceability
- **Metadata Injection:** Automatically injects `company_id` into delivery metadata and headers (`X-Company-ID`).
- **Branding:** Dynamic logo and footer generation based on tenant context.

---

## [2026-03-06] Billing Service & Stripe Core (Phase 18)

### 1. Security & Configuration
- **Blinded Keys:** Implemented `StripeSettings` in `common/config.py` to handle API keys securely via Pydantic.
- **Connectivity:** Added a startup fail-fast check using `stripe.Account.retrieve()` to validate Stripe API connection.

### 2. Implementation Core
- **StripeManager:** Created a dedicated wrapper for the Stripe SDK, handling embedded checkout sessions.
- **BillingService:** Implemented business logic for subscription initiation, including multi-tenancy validation and session orchestration.
- **Audit SSOT:** Every checkout session attempt is now logged in `AuditSubscriptionLog` with a `PENDING` status.

### 3. Database & API
- **Migrations**: Synchronized the database schema with new Stripe fields (`stripe_customer_id`, `stripe_subscription_id`, `current_period_end`) and the `CANCELED` status.
- **Endpoints**: Exposed `POST /api/v1/billing/sessions/create-embedded` and `POST /api/v1/billing/webhook`.

### 4. Webhook Automation (Phase 18.1)
- **Automatic State Machine**: Subscriptions now transition to `ACTIVE` automatically upon receiving `checkout.session.completed`.
- **Security**: Raw body signature verification implemented for webhook protection.
- **Traceability**: `PAYMENT_SUCCESS` events are recorded in the forensic timeline with full metadata.
