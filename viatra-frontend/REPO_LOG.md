# Viatra Core — REPO LOG

Registro cronológico de los hitos de implementación de la plataforma Viatra Core.

---

## v0.1.0 — Foundation (2026-03-29)

### 🏁 Hito: Arquitectura Base e Inicialización del Proyecto

**Decisiones de Arquitectura tomadas:**
- **Nombre del sistema:** `Viatra Core` (Viaje + Trajectory).
- **Stack Confirmado:** Angular + TypeScript (Frontend PWA) / FastAPI + Python (Backend Microservicios).
- **Herencia:** Se reutiliza la capa `common/` de InternoCore (`BaseEntity`, `AuditBase`, `MultiTenantBase`) para mantener la paridad de la arquitectura limpia.
- **Multitenancy:** El aislamiento de datos por `company_id` es obligatorio en todas las entidades del sistema.
- **Despliegue:** On-Premise y AWS, con `PYTHONPATH=/app:/app/viatra_service` en el Dockerfile.

**Microservicios de InternoCore a reutilizar:**

| Servicio | Modo | Acción |
|---|---|---|
| `auth_service` | Reutilizar + Extender | Agregar endpoint `POST /api/v1/auth/social-login` |
| `notification_service` | Reutilizar + Extender | Agregar endpoints `flight-alert` e `travel-itinerary` |
| `subscription_service` | Reutilizar + Extender | Agregar endpoint `travel-package` (Stripe Billing) |
| `tickets_service` | Reutilizar | Decorador `@idempotent` para transacciones financieras |
| `common/` | Reutilizar Completo | Modelos base y excepciones de dominio |

**Nuevo Microservicio creado:**
- `backend/viatra_service/` — Booking Engine, Document Vault y Sentinel Bots.

**Frontend inicializado en:**
- `viatra-frontend/` — Proyecto Angular PWA con estética Mission Control (Slate-950, acentos Cian/Ámbar).

**Estructura de Documentación creada:**
- `viatra-frontend/README.md` — Contexto de plataforma y especificaciones técnicas.
- `viatra-frontend/REPO_LOG.md` — Este archivo.

## v0.2.0 — Mission Control & Social Auth UI (2026-03-29)

### 🏁 Hito: UI Mission Control e Integración de Autenticación Social (Handshake)

**Decisiones de UI/UX tomadas:**
- **Estética:** "Slate-950" con acentos Neón (Cian `#06b6d4` para navegación y Ámbar `#f59e0b` para alertas).
- **Layout:** Pantalla dividida (Split-Screen) en el Login para reforzar la identidad visual de Viatra Core.
- **Micro-interacciones:** Hover effects con box-shadows neón y transiciones suaves en las tarjetas de selección de empresa.

**Componentes y Lógica implementados:**
- **`styles.scss`:** Configuración de tokens de diseño globales (CSS Variables) para Mission Control.
- **`AuthService` (Angular):**
  - Implementación del broker de `/social-login` (Google/FB/MS).
  - Manejo del `selection_token` en `SessionStorage`.
  - Método `selectCompany` para el handshake final del JWT multi-empresa.
- **`LoginComponent`:**
  - Integración nativa del script de *Google Sign-In (GSI)*.
  - Flujo de selección de agencia/empresa dinámico tras el login social.
  - Navegación automática para usuarios monocliente (viajeros B2C).
- **Enrutamiento:** Configuración de `app.routes.ts` con carga perezosa (Lazy Loading) para Login y Dashboard.

**Status Actual:**
- La base SPA Multitenant está configurada y operativa.
- El frontend puede iniciar sesión vía Google y obtener el JWT contextualizado a una empresa de Viatra Core.

## v0.3.0 — Core Booking & Persistence (2026-03-29)

### 🏁 Hito: Motor de Booking Funcional y Persistencia Heterogénea

**Implementación del Backend (`viatra_service`):**
- **Modelo de Datos:** Implementación de `TravelPackage`, `TravelerGroup` e `ItineraryItem` bajo el estándar `MultiTenantBase`.
- **Invariantes Financieras:** Validación estricta para asegurar que el `total_price` (Money Composite) sea mayor a cero antes de persistir.
- **Zero-Trust Filtering:** Creación de `BaseRepository` que inyecta automáticamente el filtro `company_id` en todas las consultas de lectura y escritura.
- **Auditoría de Dominio:** Integración de campos `created_by` y `last_modified_by` mediante la captura del contexto de usuario social.
- **Sentinel Readiness:** Inclusión de `flight_number` en el modelo de grupos para el futuro monitoreo de SkySentinel.
- **Endpoints:** Activación de rutas `POST /api/v1/booking/packages` y `GET /api/v1/booking/packages` plenamente funcionales.

**Status Actual:**
- El backend de Viatra Core es ahora capaz de gestionar el ciclo de vida de los paquetes de viaje de forma segura y aislada por Tenant.

---

## Próximos Hitos

- `v0.4.0` — Integración Stripe Billing (generación de suscripciones por viajero).
- `v0.5.0` — SkySentinel Bot (Rastreo de cambios en vuelos vía flight_number).
- `v1.0.0` — Ready for Production.
