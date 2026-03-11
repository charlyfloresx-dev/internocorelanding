# 📜 Auth Service - SERVICE LOG

> **Service:** Auth Service (Port 8001)
> **Status:** Critical / Identity Provider — ✅ 100% Auditor Compliant

---

### [2026-03-07] - Phase 19-20.5: Sanitization & Common Migration ✅
- **Status**: ✅ COMPLETED — **0 CRITICAL errors** in Auditor v4.1
- **PermissionChecker**: Extracted DB logic to `IPermissionRepository`. Pure domain logic now.
- **SelectCompanyCommandHandler**: Refactored with `IUserCompanyRoleRepository`.
- **Common Migration**: Updated imports from `common.domain.entities` to `common.models`.
- **Compliance**: 1 remaining INFO-level warning (AuditService trace). No structural violations.

---

### [2026-03-04] - FASE 4: Trazabilidad y Gobernanza Sanitizada (Actualidad)
- **Bloque de Seguridad:** Refactorización de `UserCompanyRole` para heredar de `MultiTenantBase`, garantizando cumplimiento de auditoría estricta.
- **Trazabilidad:** Integración de `X-Trace-Id`. Registro de cada intento de login y selección vinculado a un ID de seguimiento único.
- **Performance:** Indexación de tablas de relación para asegurar tiempos de respuesta `< 100ms` en el T2 Handshake.

### [2026-03-03] - FASE 3: Estructura de Clusters (Holdings)
- **Modelo de Datos:** Introducción del modelo `BusinessGroup` (Tabla `business_groups`).
- **Contexto Corporativo:** Inyección del claim `group_id` en el JWT.
- **Propósito:** Habilitar la visibilidad compartida para Master Data y transferencias entre almacenes del mismo grupo.

### [2026-02-25] - FASE 2: Integración de Suscripciones y Entitlements
- **Interconectividad:** Implementación de handshake síncrono con `subscription_service` (Port 8002).
- **Claims Dinámicos:** Inclusión del array `modules` según la licencia activa de la empresa.
- **Modo Read-Only:** Implementación del flag `readonly: true` para bloquear escrituras en inquilinos con suscripciones vencidas.

### [2026-02-10] - FASE 1: Cimiento y Handshake T1/T2
- **Protocolo:** Implementación de OAuth2 con Password Flow.
- **Flujo de Acceso:** Creación del proceso de dos pasos (`/login` -> T1, `/select-company` -> T2).
- **Estabilización:** Estandarización de UUIDs para consistencia entre desarrollo (`aiosqlite`) y producción (`PostgreSQL`).
- **Optimización:** Uso de `lazy="selectin"` en SQLAlchemy para prevenir problemas de performance N+1.
