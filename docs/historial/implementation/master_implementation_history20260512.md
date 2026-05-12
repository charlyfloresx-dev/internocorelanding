# InternoCore: Master Implementation History - 2026-05-12

## Arquitectura de Resiliencia: El Muro de Hierro (Rate Limiting)

### 1. Visión General
Se ha implementado una capa de protección perimetral en el Monolito Unificado para prevenir ataques de Denegación de Servicio (DoS), abusos de scanners industriales y asegurar que el consumo de recursos sea justo entre inquilinos (Fair Usage).

### 2. Componentes Técnicos
- **Provider**: `slowapi` (basado en `limits`).
- **Storage**: Redis (v7-alpine) centralizado en el stack de Docker.
- **Identificación de Clave (Multi-layer)**:
    - Nivel 1: `user_id` (del JWT) si está autenticado.
    - Nivel 2: `X-Company-ID` (Header) para aislamiento de tenant.
    - Nivel 3: `remote_addr` (IP) como fallback de seguridad.

### 3. Configuración de Límites
- **Global Burst**: 100 peticiones por minuto.
- **Hourly Quota**: 2,000 peticiones por hora.
- **Exenciones**: Endpoints de `/health`, `/api/docs` y webhooks internos están bajo observación especial o exentos para asegurar la salud del orquestador.

### 4. Decisiones de Ingeniería
- **Fail-Open Strategy (Bypass)**: Si Redis es inalcanzable, el sistema está configurado (vía fix en exception handler) para registrar el error pero permitir el flujo, priorizando la disponibilidad sobre el bloqueo absoluto en casos de fallo de infraestructura crítica.
- **Middleware Order**: `SlowAPIMiddleware` se posiciona antes que el `InternoCoreGlobalMiddleware` para rechazar tráfico no deseado antes de realizar validaciones costosas de base de datos o JWT.

### 5. Validación E2E
Se utilizó `backend/scripts/test_rate_limit_resilience.py` para simular un ataque de ráfaga desde el `Tenant_A`. El sistema respondió con `HTTP 429` a partir de la petición 101, mientras que el `Tenant_B` operó con latencia normal (<50ms).
