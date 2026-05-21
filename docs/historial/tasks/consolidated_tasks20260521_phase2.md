# Consolidated Tasks — 2026-05-21 (Phase 2: WhatsApp Gateway Implementation)

## Épica 1: Housekeeping & Remediación de Deuda (inventory_service) ✅ COMPLETADA
- [x] Tarea 1.1: Limpieza de importaciones redundantes en `inventory_app/main.py`.
- [x] Tarea 1.2: Creación de `scripts/scratch/`, reubicación de 8 scripts de debug, `.gitignore`.
- [x] Tarea 1.3: Exportación de `InventoryLocation` en `models/__init__.py`.
- [x] Tarea 1.4: Pin de las 18 dependencias en `requirements.txt`.

## Épica 2: Gateway de WhatsApp Local Multitenant — Progreso del Día

### Tarea 2.1: Scaffolding & Core del Microservicio Node.js ✅
- [x] `package.json` con whatsapp-web.js, express, qrcode, dotenv.
- [x] `tsconfig.json` ES2022 target, strict mode.
- [x] `src/config.ts` con carga segura de variables de entorno.
- [x] `src/manager.ts` — `WhatsAppSessionManager` singleton con:
  - Sesiones aisladas por `company_id` (`LocalAuth` con `clientId`).
  - Cola FIFO humanizada (`CompanyQueue`) con delay aleatorio 1.5s-3s.
  - Conversión automática de QR a Base64 Data URL.
  - Eventos: `qr`, `authenticated`, `auth_failure`, `ready`, `disconnected`.
- [x] `src/index.ts` — API Express con 4 endpoints protegidos por Bearer API Key:
  - `POST /api/v1/whatsapp/send`
  - `GET /api/v1/whatsapp/session/:company_id/status`
  - `GET /api/v1/whatsapp/session/:company_id/qr`
  - `POST /api/v1/whatsapp/session/:company_id/initialize`

### Tarea 2.2: Docker & Compose ✅
- [x] `whatsapp_gateway/Dockerfile` — Node 22-slim + Chromium headless del sistema.
  - `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true` + `PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium`.
- [x] `infrastructure/docker/docker-compose.dev.yml` actualizado:
  - Servicio `whatsapp-gateway` (puerto 3011:3000, vol `whatsapp_sessions_dev`).
- [x] `docker-compose.yml` (root/legacy) actualizado igualmente.

### Tarea 2.3: Refactor del Notification Service (FastAPI) — Adapter/Factory ✅
- [x] `app/infrastructure/base_whatsapp.py` — Interfaz abstracta `BaseWhatsAppClient`.
- [x] `app/infrastructure/twilio_whatsapp_client.py` — Adapter Twilio implementando la ABC.
- [x] `app/infrastructure/local_whatsapp_client.py` — Adapter Local Gateway vía httpx.
- [x] `app/infrastructure/whatsapp_factory.py` — Factory multitenant dinámica.
- [x] `app/core/config.py` — 3 nuevas variables: `DEFAULT_WHATSAPP_PROVIDER`, `LOCAL_WHATSAPP_GATEWAY_URL`, `WHATSAPP_GATEWAY_API_KEY`.
- [x] `notification_app/infrastructure/` — Mirrors con imports ajustados (pydantic_settings).

### Tarea 2.4: Rutas Proxy Seguras (Pending)
- [ ] `app/routers/whatsapp_routes.py` — Endpoints espejo con `current_user.company_id`.

## Validación de Compliance
- ✅ `generate_code_graph.py` → **100% Compliance (0 errores)** — 14/14 servicios CLEAN.
- Fix aplicado: `notification_app/local_whatsapp_client.py` ENV_ACCESS_VIOLATION → migrado a `pydantic_settings`.

## Decisiones Arquitectónicas (ADR)
- **ADR-04**: El `docker-compose.dev.yml` es la fuente de verdad para desarrollo local, no `docker-compose.yml` (root/legacy).
- **ADR-05**: Los archivos en `notification_app/` se mantienen sincronizados pero NO son prioridad en fase de estabilización dev.
