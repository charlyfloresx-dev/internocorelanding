# Historial Maestro de Implementación: 2026-05-21

Este documento registra los planes de diseño aprobados y decisiones arquitectónicas tomadas durante esta jornada para el mantenimiento de `inventory_service` y la integración del canal de WhatsApp Local Multitenant en **InternoCore**.

---

## 1. Decisiones Arquitectónicas (ADRs)

### ADR-01: Adapter/Factory Pattern para Notificaciones Multitenant
- **Contexto:** Se requiere ofrecer un canal de notificaciones por WhatsApp flexible. Algunos clientes optan por Twilio corporativo (SaaS pago) y otros por una pasarela gratuita conectando su propio dispositivo móvil (Gateway Local).
- **Decisión:** Implementar la interfaz abstracta `BaseWhatsAppClient` en el `notification_service` FastAPI. Crear dos adaptadores concretos: `TwilioWhatsAppClient` y `LocalWhatsAppClient`. Utilizar una factoría `WhatsAppClientFactory` para instanciar el cliente correcto en tiempo de ejecución de acuerdo a la columna `provider` de la tabla `company_notification_configs` en base de datos.
- **Consecuencias:** Desacoplamiento total de los proveedores. Si en el futuro se añade otro proveedor (e.g. MessageBird), solo se requiere crear un nuevo adaptador concreto sin modificar el servicio de notificaciones.

### ADR-02: Proxies Espejo Seguros para QR en API Gateway
- **Contexto:** El portal frontend de Angular requiere mostrar el estado de la conexión de WhatsApp y dibujar el código QR de vinculación de Puppeteer. La pasarela local se encuentra en la red aislada de Docker (`interno-network`).
- **Decisión:** Exponer rutas espejo `/session/status`, `/session/qr` y `/session/initialize` en `app/routers/whatsapp_routes.py` de FastAPI que actúen como proxies HTTP reverse hacia el servicio Node.js. 
- **Seguridad:** Proteger estrictamente estas rutas forzando la inyección de dependencias `current_user: TokenPayload` de JWT y usando `current_user.company_id` para realizar las llamadas a la pasarela Node.js, garantizando aislamiento estricto (Multitenancy Isolation). Un administrador de la Empresa A jamás podrá consultar o alterar las sesiones de la Empresa B.

### ADR-03: Desacoplamiento de Eventos (Outbox Pattern)
- **Contexto:** Workers asíncronos como `Tickets Worker` no deben acoplarse con la lógica o errores de entrega de notificaciones de WhatsApp.
- **Decisión:** Los emisores publican eventos de integración JSON hacia el endpoint `/api/v1/events` del `notification_service`. Es el servicio de notificaciones el encargado de interceptar el evento, evaluar la prioridad en su **Dispatch Matrix** y disparar los adaptadores de WhatsApp de manera descentralizada y asíncrona.

---

## 2. Plan de Remediación de Deuda (Housekeeping)
Se aprueba una limpieza exhaustiva sobre `inventory_service` para subsanar los hallazgos de la auditoría arquitectónica:
- Remoción de importaciones redundantes y repetidas en `main.py` de FastAPI.
- Ordenación estructural: reubicación de scripts huérfanos/temporales de depuración a `scripts/scratch/` y actualización del `.gitignore`.
- Corrección de alias y exposición de `InventoryLocation` en el archivo de inicialización de modelos.
- Fijar versiones estables en el archivo de requerimientos (`requirements.txt`) para repetibilidad garantizada.

---

## 3. Implementación Ejecutada (Phase 121 + 122) — Estado Final

### Phase 121 Fase 1 — inventory_service Housekeeping

**`inventory_app/main.py`**: Se identificó que el bloque líneas 72-88 re-importaba los mismos 4 routers (`transactions`, `reconciliation`, `boms`, `inter_company_transfers`) ya declarados en la línea 14. El bloque era redundante y fue eliminado. Adicionalmente se eliminaron imports de `CORSMiddleware`, `Base`, `engine` que no se usaban.

**`scripts/scratch/`**: Directorio nuevo para archivos temporales de desarrollo. Se movieron: `check_inventory_tables.py`, `create_dummy_ict.py`, `fix_ict_ids.py`, `inspect_row.py`, `test_db_access.py`, `verify_ict.py`, `error.txt`, `test_out.txt`, y ~12 scripts adicionales. `.gitignore` actualizado con entrada `inventory_service/scripts/scratch/`.

**`models/__init__.py` y `requirements.txt`**: Verificados — ya estaban correctos. No requirieron cambios.

### Phase 121 Fase 2 — WhatsApp Gateway Multitenant

**Microservicio Node.js (`backend/whatsapp_gateway/`):**

Patrón `Singleton` para `WhatsAppSessionManager`: un proceso Node.js gestiona todas las sesiones. Cada empresa tiene su `SessionInfo` (state machine: `NOT_INITIALIZED → QR_READY → AUTHENTICATING → CONNECTED / DISCONNECTED / FAILED`). El estado `QR_READY` incluye el Data URL Base64 del QR listo para renderizar en frontend sin procesamiento adicional.

`CompanyQueue`: FIFO por tenant. El método `processNext()` es non-blocking (una sola ejecución en paralelo por tenant). Delay aleatorio `Math.floor(Math.random() * (3000 - 1500 + 1) + 1500)` entre mensajes. El formato del número destino se normaliza: se limpian caracteres no-digit y se añade `@c.us` si no tiene sufijo.

Puppeteer args críticos para Docker: `--no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --single-process --disable-gpu` — necesarios para correr Chromium sin root y sin `/dev/shm` grande.

**Adapter/Factory Pattern (notification_service):**

`BaseWhatsAppClient` — ABC con `send_group_message(group_id, message, metadata)` y `send_template_message(group_id, template_name, template_params)`. El `metadata` dict transporta `company_id` al `LocalWhatsAppClient` sin romper la firma.

`WhatsAppClientFactory.get_client_for_tenant(db, company_id)`: Consulta `company_notification_configs` con `is_active=True`. Si no hay config → fallback a `DEFAULT_WHATSAPP_PROVIDER` (.env). Para Twilio con BYOK: usa `account_sid` y `auth_token` del tenant. Para Twilio fallback: usa credenciales globales. Para `"local"`: devuelve `LocalWhatsAppClient()` — sencillo, sin parámetros.

**ADR-02 — Proxy Espejo (whatsapp_routes.py):**

Los 3 endpoints proxy (`/session/status`, `/session/qr`, `/session/initialize`) no aceptan `company_id` de ningún parámetro del cliente. El `company_id` es extraído exclusivamente de `current_user.company_id` (JWT verificado por `require_scope`). Helpers `_proxy_get(path)` y `_proxy_post(path)` encapsulan el client httpx con timeout y manejo de `HTTP_503_SERVICE_UNAVAILABLE`.

### Phase 122 — HMAC Inter-Service

**Motivación**: Los endpoints `/internal/*` de subscription_service no estaban expuestos vía Nginx, pero cualquier contenedor en `interno-network` podía llamarlos libremente. En producción en AWS, cualquier ECS task en la misma VPC podía consultar el estado de suscripción de cualquier tenant.

**Implementación**: `hmac.new(SECRET_KEY.encode(), company_id.encode(), hashlib.sha256).hexdigest()` — idéntico al patrón de tickets_service. `hmac.compare_digest` en vez de `==` para evitar timing attacks. El helper `_verify_service_signature` es llamado como primera instrucción en cada endpoint, antes de tocar el repositorio.

**Dead code**: `auth_service/infrastructure/subscription_client.py` tenía `BASE_URL = "http://subscription-service:8000/internal"` hardcodeado y `SubscriptionClient` con `get_subscription_status()` que llamaba `/internal/status`. Grep confirmó: cero archivos activos importan este módulo. Eliminado.

---

## 4. Verificación Final

| Check | Resultado |
|---|---|
| Code Graph | ✅ 0 errores — 14 servicios CLEAN |
| Ecosistema (validate_ecosystem.ps1) | ✅ 8/8 OK |
| `GET /internal/status` sin firma | ✅ 403 Firma de servicio requerida |
| `GET /internal/entitlements` sin firma | ✅ 403 Firma de servicio requerida |
| WhatsApp Gateway código | ✅ Completo — pendiente despliegue y QR scan |
