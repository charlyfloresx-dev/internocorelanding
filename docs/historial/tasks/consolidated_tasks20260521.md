# Consolidado de Tareas: 2026-05-21

Este documento registra el progreso y backlog del día, enfocado en el Housekeeping de `inventory_service` e integración del canal de WhatsApp Local Multitenant.

## Fases de Ejecución

### Fase 1: Housekeeping & Remediación de Deuda (inventory_service)
- `[ ]` Tarea 1.1: Limpieza de `inventory_app/main.py` eliminando las importaciones redundantes de la línea 72-88.
- `[ ]` Tarea 1.2: Creación del directorio `scripts/scratch/`, reubicación de los scripts de depuración de la raíz (`create_dummy_ict.py`, `check_inventory_tables.py`, etc.) y actualización del `.gitignore`.
- `[ ]` Tarea 1.3: Corrección del archivo `inventory_app/models/__init__.py` para incluir y exponer correctamente `InventoryLocation` en el `__all__`.
- `[ ]` Tarea 1.4: Fijar versiones (pinning) de dependencias críticas en el `requirements.txt` del servicio.

### Fase 2: Implementación del Gateway de WhatsApp Local Multitenant
- `[ ]` Tarea 2.1: Creación del microservicio `whatsapp_gateway` en Node.js 22 LTS / TypeScript (Session Manager + Cola FIFO + Throttling).
- `[ ]` Tarea 2.2: Configuración del `Dockerfile` (soporte headless Chromium/Puppeteer) y actualización de `docker-compose.yml`.
- `[ ]` Tarea 2.3: Refactor del `notification_service` (FastAPI) con patrón Adapter/Factory para `BaseWhatsAppClient`, `TwilioWhatsAppClient`, `LocalWhatsAppClient` y `WhatsAppClientFactory` dinámico por Tenant.
- `[ ]` Tarea 2.4: Rutas proxy espejo seguras para el escaneo QR en `app/routers/whatsapp_routes.py` (con aislamiento por `current_user.company_id`).

---

## Log de Jornada (Fase 1 iniciada)
- *10:38 AM:* Aprobación formal del plan. Creación del backlog en `task.md` y sincronización con el historial del repositorio.
