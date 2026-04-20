# KIOSK SERVICE LOG

## Description
Microservice built to support local Edge Computing deployments for Photo Booths and Events. Processes images, generates S3/MinIO upload presigned URLs, and coordinates the local hardware printing queue (CUPS) through background workers. Includes a Hybrid payment processor (Stripe and Cash).

## 2026-04-11 Initial Implementation & Architecture
- **Framework:** FastAPI, SQLAlchemy Async, asyncpg.
- **Storage Strategy:** Uses MinIO to bypass FastAPI byte buffering, handling `multipart/form-data` directly against the S3 API for gigabit-speed LAN transfers.
- **Data Models:**
  - `EventPhoto`: Stores `guest_session_id`, `event_id`, S3 `object_key`, and lifecycle state-machine.
  - `PaymentOrder`: Tracks STRIPE intents and CASH QR code hashes.
- **Print Worker:** Included an `asyncio` task (`print_worker.py`) running in the background to automatically ferry `PURCHASED` photos over to the Linux local CUPS system (`lp` command).
- **Gamification hooks:** Designed logic to intersect with `subscription_service` para el modelo "Paparazzi Rewards" en el checkout pipeline.
- **Match System (Dual Approval):** Implementada aprobación individual de Novio y Novia, omitiendo automáticamente archivos de video.
- **Smart Checkout (Stripe + Wallet):** Refactorización del flujo de Single PaymentIntents. La lógica consolida el carrito, deduce del monedero Paparazzi interconectando `httpx` de forma resiliente, y delega el saldo sobrante exacto a Stripe.
- **Hotfix de Infra:** Resolución de importación circular nativa de `logging.py` que bloqueaba contenedores y resolución de dependencias internas.
- **Background Print Worker & Hardware Integration:** Incorporada librería `pycups` e inyección de socket físico local para Ubuntu/Debian CUPS (`/var/run/cups/cups.sock`) en la orquestación Docker. El `print_worker.py` corre como background daemon vía el event_loop de FastAPI y transforma a PDF (usando recorte proporcional 3:2 DNP y fusión de Watermark asíncrona vía Pillow) para el volcado nativo spool.
- **Manual Test Validation & Staff Manual:** Finalizado el manual técnico operativo `STAFF_OPERATIONS_MANUAL.md`. Validado el flujo E2E (Setup -> Upload -> Match -> Checkout -> Spool) con PDF final procesado exitosamente. Implementado hotfix de `MINIO_PUBLIC_URL` para permitir previsualización de S3 en navegadores externos a la red Docker.

- **Engine Generalization:** System refactored from "Wedding Only" to a general "Event Workflow Engine". Replaced Bride/Groom roles with an $N$-Approver dynamic quórum system.
- **Integrity Filter (Identity Protection):** Incorporated `device_id` fingerprinting in the backend to prevent duplicate votes from the same hardware.
- **Industrial Hardening (Alembic):** Initialized Alembic with **Async Support** (`sqlalchemy.ext.asyncio`). Migrated from `create_all` to versioned migrations. Integrated `alembic upgrade head` into the Docker Compose startup command 

## 2026-04-12 Industrial Hardening, Domain SSL & Offline Mode
- **SSL Industrial SSL/HTTPS:** Migración de IP local a dominio profesional `momentos.com`. Generación de certificados SSL con `mkcert` (SAN para dominio, IP y localhost).
- **Offline Total Strategy:** Creación de `dns_server.py` (servidor DNS UDP ligero) y `modo_offline.ps1` para orquestar la liberación del puerto 53 y la toma de control del tráfico LAN sin internet.
- **Secure Image Proxy:** Implementada ruta `/api/v1/kiosk/photos/serve/{photo_id}` impulsada por `StreamingResponse` para evitar "Mixed Content" y asegurar que todas las fotos carguen vía HTTPS en móviles agresivos con la seguridad.
- **Cash Ledger Engine:** Implementado modelo `CashTransaction` y controlador de finanzas para el Staff. Rastreo de Fondo Inicial (Float), Gastos (Payouts) y Ajustes manuales.
- **Staff Dashboard V2:** Rediseño estético y funcional del panel de control con widgets financieros dorados y alertas de discrepancia en cierres de caja.
- **PWA Standalone Mode:** Configuración de `manifest.webmanifest` para permitir la instalación de la app en iOS/Android sin barra de búsqueda de navegador, ganando un 20% de superficie de pantalla para la UX.

## 2026-04-16 Architectural Alignment & Decoupling ✅
- **Domain Refactoring**: Successfully decoupled Pydantic schemas from SQLAlchemy ORM models.
- **Shared Domain Layer**: Extracted core Enums (`PaymentMethod`, `PaymentStatus`, `PhotoStatus`) to `app/domain/enums.py` to resolve circular dependencies and comply with DDD standards.
- **AWS Readiness**: 
  - Refactored `config.py` to use Pydantic `Field` and `AliasChoices`.
  - Migrated hardcoded `localhost` database references to environment-injected variables for Docker internal networking.
- **Validation**: Achieved 100% compliance in the internal architectural audit.

### 🔜 Próximos Pasos (Roadmap)
- [ ] **App de uso rápido**: Desarrollo de un wrapper nativo ligero para arranque inmediato en tablets.
- [ ] **Branding Dinámico**: Sistema de inyección de logos y colores primarios desde el onboarding.
- [ ] **Validación de Hardware Pro**: Confirmar la persistencia de los DNS en el router profesional de campo.
