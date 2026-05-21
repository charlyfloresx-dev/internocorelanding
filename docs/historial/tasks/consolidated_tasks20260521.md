# Consolidado de Tareas: 2026-05-21

Este documento registra el progreso y backlog del día. Jornada de seguridad y arquitectura: Phase 120 (Security Hardening), Phase 121 (Inventory Housekeeping + WhatsApp Gateway), Phase 122 (HMAC Inter-Service).

---

## Phase 120 — Backend Security Hardening + Frontend Alignment ✅ COMPLETADO

- `[x]` Iron Wall Fix: `inventory_app/inventory.py` (10 endpoints) migrados de `X-Company-ID` header a JWT `TokenPayload`.
- `[x]` Iron Wall Fix: `inventory_app/dashboard.py` (9 endpoints) mismo patrón.
- `[x]` Admin Hardening: `auth_service/companies.py` (5 endpoints) protegidos con `verify_admin_master_key`.
- `[x]` Admin Hardening: `auth_service/seed.py` (`/seed/run`) protegido.
- `[x]` Admin Hardening: `subscription_service/wallet.py` (`/award`, `/deduct`) protegidos.
- `[x]` Audit Trail: `hcm_service/collaborators.py` — `bulk_upload` registra `AuditService.log_action`.
- `[x]` Frontend Bug Fix: `multi-tenant.interceptor.ts` — 403 ya no dispara logout (solo 401 → RTR).
- `[x]` Frontend Route Guard: `/inventory` y `/monitor/tickets` con `canActivate: [permissionGuard]`.
- `[x]` Frontend Scope Aliases: `NavigationService` acepta dot-format y colon-format.
- `[x]` Auditoría de seguridad completa (177 endpoints) guardada en `docs/historial/implementation/security_audit_roles_permisos.md`.

---

## Phase 121 — Inventory Housekeeping + WhatsApp Gateway ✅ COMPLETADO

### Fase 1: Housekeeping (inventory_service)
- `[x]` Tarea 1.1: `inventory_app/main.py` limpiado — bloque de imports duplicados eliminado.
- `[x]` Tarea 1.2: `scripts/scratch/` creado — 20 scripts de debug reubicados desde la raíz; `.gitignore` actualizado.
- `[x]` Tarea 1.3: `models/__init__.py` — `InventoryLocation` ya estaba expuesta. Sin cambios requeridos.
- `[x]` Tarea 1.4: `requirements.txt` — dependencias ya pinneadas. Sin cambios requeridos.

### Fase 2: WhatsApp Gateway Multitenant
- `[x]` Tarea 2.1: `backend/whatsapp_gateway/` — Node.js 22 LTS, `manager.ts` (Singleton + CompanyQueue 1.5–3s anti-ban), `index.ts` (4 rutas Express + Bearer auth + SIGTERM).
- `[x]` Tarea 2.2: `Dockerfile` (Chromium headless) + `docker-compose.dev.yml` (servicio `whatsapp-gateway`, puerto 3011, volumen `whatsapp_sessions_dev`).
- `[x]` Tarea 2.3: `notification_service` — `BaseWhatsAppClient` ABC, `LocalWhatsAppClient`, `TwilioWhatsAppClient`, `WhatsAppClientFactory` dinámico por tenant.
- `[x]` Tarea 2.4: `whatsapp_routes.py` — 3 proxy espejo con ADR-02 (Iron Wall JWT). Scope: `["admin", "notifications:manage"]`.

---

## Phase 122 — HMAC Inter-Service Hardening ✅ COMPLETADO

- `[x]` `subscription_service/internal.py` — `_verify_service_signature()` + header `X-Service-Signature` requerido en `/status` y `/entitlements`.
- `[x]` `auth_service/infrastructure/clients/subscription_client.py` — `_service_signature()` inyectado en `get_company_entitlements()`.
- `[x]` `auth_service/infrastructure/subscription_client.py` — eliminado (dead code, cero importadores activos).
- `[x]` `.agent/workflows/sync-docs.md` — actualizado con paso 1.5 (HMAC verification), paso 3.6 (WhatsApp Gateway), formato de commit estándar.

---

## Pendientes (próximas sesiones)

- `[ ]` Desplegar y conectar `whatsapp-gateway`: `docker compose up --build whatsapp-gateway`, escanear QR via `/api/v1/whatsapp/session/qr` con JWT admin, verificar sesión CONNECTED.
- `[ ]` Rate limiting en endpoints de `subscription_service` y `master_data_service`.
- `[ ]` Fix conocido: `GET /products/{id}/variants` retorna 403 para rol `collaborator` — agregar `inventory:read` al scope mapping en `select_company_command.py`.
- `[ ]` `default_tax_rate` en Planta US debería ser 0.0 (actualmente 0.16).
