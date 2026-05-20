# Notification Service – Log

## 🕒 Última Actividad (2026-05-20)
**Phase 118: WhatsApp Industrial Client + WebSocket + Notification Service Refactor** ✅
- **`app/infrastructure/whatsapp_client.py`**: Cliente Twilio industrial. Envía alertas a grupos virtuales y destinatarios individuales con retry exponencial. Soporte para templates industriales (stock alert, downtime, incident).
- **`app/services/notification_service.py`**: Servicio central refactorizado con dispatch matrix: `HIGH` priority → fuerza `IN_APP + EMAIL + PUSH`. Soporte para `company_notification_model` para personalización por tenant.
- **`app/core/websocket.py`**: Manager de WebSocket con room management por `company_id`. Permite broadcast en tiempo real de alertas industriales al panel Angular.
- **`app/models/company_notification_model.py`**: Modelo de configuración de notificaciones por empresa (plantillas, canales, preferencias).
- **`app/models/whatsapp_mapping.py`**: Mapeo de `user_id` → número WhatsApp por empresa.
- **`app/routers/whatsapp_routes.py`**: Rutas de configuración WhatsApp actualizadas con autenticación y validación.
- **Migración Alembic** (`000_notification_baseline.py`): Baseline de todas las tablas del servicio de notificaciones.
- **Status**: ✅ COMPLETED — WhatsApp + WebSocket operativos. Code Graph 0 errores.

## 🕒 Última Actividad (2026-04-28)
**Pipeline de Notificaciones WhatsApp (Fase 72)**
- **Twilio Integration**: Integración con Twilio para el envío de alertas industriales.
- **Virtual Groups**: Creación de "Grupos Virtuales" para superar las limitaciones del Sandbox de Twilio, permitiendo envíos multi-destinatario atomizados.

## 🕒 Última Actividad (2026-04-27)
**Notification State Persistence (Fase 71)**
- **Read-Status Fix**: Implementado logging de `rowcount` en el endpoint `mark_as_read` para diagnosticar fallos de persistencia.
- **Commit Verification**: Verificada la integridad del commit asíncrono en la tabla `notification_recipients`.

---

## Overview
The Notification Service (port **8008**) is the "Nervous System" of InternoCore.  
It receives integration events, evaluates user/tenant preferences, and dispatches notifications through the appropriate channels.

---

## Phase 10 – Initial Scaffolding & Preference Dispatcher
**Status**: ✅ Completed · **Date**: 2026-03-04

### Models
| Model | Purpose |
|-------|---------|
| `Notification` | Core record per channel dispatch |
| `NotificationRecipient` | Tracks read/unread per user |
| `UserPreferences` | Per-user channel toggles + optional webhook URL |

### Services
| Service | File | Purpose |
|---------|------|---------|
| `PreferenceService` | `app/services/preference_service.py` | `get_user_channels()` — returns enabled channels based on priority and preferences |

### Event Consumer
`POST /api/v1/events` (router: `app/routers/event_routes.py`)

**Dispatch Matrix:**
- **HIGH priority** → forces `[IN_APP, EMAIL, PUSH]` regardless of preferences.
- **Other priorities** → queries `UserPreferences`; defaults to `[IN_APP]` if no record found.
- A `Notification` record + `NotificationRecipient` entry is created per channel.

### WebhookProvider
Migrated from `tickets_service`. Located at `app/services/webhook_provider.py`.  
HMAC-SHA256 signing for all outgoing webhook payloads.

---

### [2026-03-06] - Phase 16.5: Structure Remediation ✅
- **Status**: ✅ COMPLETED
- **Structure**: Relocated polluted test files from service root to `tests/` directory.
- **Compliance**: Verified 0 "Structure Violations" in Code Graph.
- **OpenAPI**: Successfully extracted `notification.json` spec.

### [2026-03-06] - Phase 10.5 & 10.6: Provider Infrastructure & Templating
- **Status**: ✅ COMPLETED
- **Providers**: Integrated `ResendEmailProvider` (Real SDK) and `SMSMockProvider`.
- **Templating**: Implemented `TemplateService` with Jinja2 and `base_layout.html` for professional HTML emails.
- **Multi-tenancy**: Dynamic logo and privacy policy injection. Integrated **SVG Base64 embedding** for local branding reliability.
- **Fail-Safe**: Integrated error handling in `event_routes.py` to ensure robust dispatch loop.

### [2026-03-05] - Phase 16: Industrial Strengthening
- **Status**: ✅ COMPLETED
- **Deduplication**: Implementación del `IdempotencyGuard` persistente para evitar duplicidad de eventos.
- **Providers**: Lógica base para Email y Push Notifications integrada.

### [2026-03-06] - Phase 17: Advanced Alerts & Escalation (Planned)
- **Escalation**: Implementación del motor de escalación dinámica basado en tiempos configurables por empresa.
- **Andon**: Integración con el sistema de paros para alertas a supervisores.

---

## Pending Backlog
- [x] Implement real channel providers (`EmailProvider`, `PushProvider`) behind a `BaseProvider` interface.
- [x] Implement HTML Templating system using Jinja2 (`TemplateService`).
- [x] Add idempotency check: if `event_id` already processed, skip and return 200.
- [ ] Add automated tests for `PreferenceService` (HIGH vs LOW priority branching).
- [ ] End-to-end integration test (Outbox → Worker → Consumer → Notification).
- [ ] Support additional event types (`StockBreakAlert`, `LineStoppedEvent`).
