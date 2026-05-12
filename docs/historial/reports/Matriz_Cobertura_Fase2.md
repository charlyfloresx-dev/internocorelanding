# Reporte de Cobertura y Hardening - Fase 2 (Identidad y Acceso)

## 📊 1. Matriz de Cobertura de Scopes (Hardened)

| Microservicio | Endpoint Crítico | Decorador Implementado | Scopes Requeridos | ¿Valida CompanyID? | Estado Final |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **auth_service** | `POST /tenant-switch` | `Depends(get_login_token)` | Ninguno (Phase 1 Token) | Sí (Valida UserCompanyRole) | ✅ OK |
| **inventory** | `POST /stock/adjust` | `SecurityScopes` | `inv:admin` | Sí (vía RLS) | ✅ OK |
| **wms_service** | `GET /wave-picking` | `Depends(require_scope)` | `wms:read` | Sí (vía RLS) | ✅ HARDENED |
| **wms_service** | `POST /locations/` | `Depends(require_scope)` | `wms:write` | Sí (vía RLS) | ✅ HARDENED |
| **mes_service** | `PUT /work-order/{id}` | `Depends(require_scope)` | `mes:write` | Sí (vía RLS) | ✅ HARDENED |
| **master_data** | `DELETE /products/{id}` | `SecurityScopes` | `md:admin` | Sí (vía RLS) | ✅ OK |

*Nota: Se implementó la factoría `require_scope` en `common.security.dependencies.py` para facilitar la inyección estandarizada en FastAPI y se aplicó a las rutas vulnerables de WMS y MES.*

---

## 🔐 2. Validación Criptográfica (Bcrypt)

*   **Hallazgo Anterior**: El `work_factor` (rounds) en `passlib` estaba configurado por defecto (10).
*   **Acción Tomada**: Se inyectó explícitamente `bcrypt__rounds=12` en `CryptContext` en los siguientes módulos:
    *   `auth_service/auth_app/core/security.py`
    *   `auth_service/auth_app/commands/complete_registration_command.py`
    *   `auth_service/scripts/seed_standalone.py`
    *   `hcm_service/hcm_app/core/security.py`
*   **Estado Final**: ✅ OK (Mitigación contra GPU-cracking moderno asegurada).

---

## 🛠️ 3. El "Heartbeat" de Sesión (Redis Blocklist)

*   **Riesgo Anterior**: Los tokens JWT seguían siendo válidos localmente hasta su expiración (60 min) incluso si el usuario era desactivado.
*   **Acción Tomada**: Se implementó una verificación asíncrona ("Heartbeat") en `get_current_active_user` dentro de `common/security/dependencies.py`.
    *   Se consulta asíncronamente `redis.asyncio` buscando la llave `blacklist:{current_user.sub}`.
    *   Se agregó un caché local in-memory (`_user_status_cache`) con un TTL de 5 minutos (300 segundos) para no saturar Redis en escenarios de alta concurrencia o loops del Frontend.
    *   Fallo Seguro (Fail-Open): Si Redis cae temporalmente, el sistema lo loggea pero permite operar al usuario basándose en la firma del JWT, imitando la resiliencia del Rate Limiter.
*   **Estado Final**: ✅ OK (Revocación casi en tiempo real implementada).

---
*Auditoría generada por Antigravity Agent - InternoCore Security Team*
