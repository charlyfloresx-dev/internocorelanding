# 💳 SERVICE LOG - SUBSCRIPTION SERVICE

## 📌 Estado Actual: Phase 4 (Finalized)
- **Puerto:** 8002
- **Base de Datos:** `subscription_db`
- **SSOT Acceso:** Tabla `entitlements`

## ✅ Cambios Realizados
### 2026-02-25 - Implementación MVP
- **Cleanup:** Purga de `billing_service` y actualización de `MANIFEST.md`.
- **Scaffolding:** Estructura Clean Architecture con FastAPI y SQLAlchemy Asíncrono.
- **Modelado:**
    - `Module`: Catálogo global.
    - `Plan`: Definición de paquetes.
    - `Subscription`: Estados `TRIAL`, `ACTIVE`, `EXPIRED`.
    - `Entitlement`: Tabla puente de acceso por `company_id`.
    - `AuditSubscriptionLog`: Auditoría JSONB.
- **CQRS:**
    - `StartTrialCommand`: Activación automática de Plan Básico.
    - `GetEntitlementsQuery`: Consulta ultra-veloz para `auth_service`.
- **API:**
    - `GET /internal/entitlements/{company_id}`: Handshake interno.
- **Stub:** `LicenseService` para firmas JWS.

### 2026-02-25 - Auditoría y Trazabilidad (Forensic Trace)
- **Log Service:** Implementación de `AuditSubscriptionChange` para registro de estados Old vs New.
- **Contexto:** Captura de IP y Usuario en logs de auditoría JSONB.
- **Integración:** Soporte para `X-Transaction-ID` (correlation_id) en el handshake interno.

### 2026-02-25 - Cierre Técnico y Admin Layer (God Mode)
- **Error Handling:** Enriquecimiento de mensajes 403 con `transaction_id`.
- **God Mode:** Creación de `app/api/v1/endpoints/admin.py` protegido por `ADMIN_MASTER_KEY`.
- **Contrato RBAC:** Preparación del esquema `TokenPayload` con `role` y `accessible_warehouses`.

## 🚀 Próximos Pasos
- Implementar lógica real de Upgrade/Override en el Admin Router.
- Refactorización de `master_data_service` para integración delegada de seguridad.
- Implementación de firma JWS real en `LicenseService`.
