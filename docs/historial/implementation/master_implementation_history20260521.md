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
