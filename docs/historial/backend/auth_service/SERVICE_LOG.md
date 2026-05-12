markdown
# Service Log: InternoCore Auth-Service

## 2026-02-25: Auditoría, Trazabilidad y Seguridad de Handshake
* **Hito**: Sistema de Rastro Forense y Bloqueo de Seguridad.
* **Estado**: ✅ VALIDADO.
* **Cambios**:
    * **Trazabilidad**: Implementación de `correlation_id` (vía `transaction_id`) vinculado entre el JWT y los logs del handshake.
    * **Seguridad (402)**: Bloqueo explícito de tokens para empresas con estatus `EXPIRED` con registro de nivel `SECURITY`.
    * **Modo Lectura**: Registro de 'Sesión en Modo Lectura' para empresas en periodo de gracia (`PAST_DUE`).
    * **Handshake Resiliente**: Handshake con `subscription_service` optimizado con reintento y fallback detallado.
    * **Gobernanza RBAC**: Payload de token enriquecido con `role` y `accessible_warehouses`.
    * **Trazabilidad**: Enriquecimiento de errores 403 con `transaction_id` para debugging frontend.

## 2026-02-25: Integración con Subscription Service (Handshake v1)
* **Hito**: Integración de Licenciamiento y Entitlements dinámicos.
* **Estado**: ✅ VALIDADO / INTEGRADO.
* **Cambios**:
    * **HttpClient**: Implementación de `SubscriptionClient` para comunicación inter-microservicio (Port 8002).
    * **Resiliencia**: Implementación de "Minimum Viable Access" (auth_core, inventory_core + readonly) en caso de fallo del servicio de suscripciones.
    * **Handshake JWT**: El Access Token final ahora incluye claims críticos: `modules`, `status` y `readonly`.
    * **Regla de Negocio**: Soporte para periodo de gracia (`PAST_DUE`) que activa automáticamente el modo `readonly`.
    * **Auditoría**: Registro detallado de obtención de licencias en los logs de la aplicación.

## 2026-02-20: Consolidación de Aislamiento Multitenant Automático
* **Hito**: Consolidación de Aislamiento Multitenant Automático.
* **Estado**: ✅ VALIDADO / PRODUCTIVO.
* **Cambios**:
    * **Contexto Global**: Implementación exitosa de `common.middleware.request_context` para persistencia de identidad durante el ciclo de vida de la petición.
    * **BaseRepository v2**: Migración a `BaseRepository` con extracción automática de `company_id` desde el `ContextVar`, eliminando la necesidad de pasar el ID manualmente.
    * **Validación de Aislamiento**: Ejecución exitosa de `test_cqrs_filter.py`, confirmando la inyección dinámica de filtros SQL y el correcto manejo de contextos vacíos (Admin).
    * **Simplificación**: Eliminación de redundancias en lógica de filtrado manual en controladores de usuario y empresa.
    * **Despliegue AWS**: Confirmación de que la imagen `demo-v1` reside en Amazon ECR (`interno-backend-auth-service`) y está lista para el despliegue final.

## 2026-02-20: Cierre de Blindaje Multi-tenant y CQRS
* **Hito**: Implementación de Repositorio Base con Contexto Automático.
* **Estado**: ✅ PRODUCTIVO / VALIDADO.
* **Cambios**:
    * **Contexto Global**: Integración de `common.middleware.request_context` para persistir la identidad del usuario durante todo el ciclo de vida de la petición.
    * **BaseRepository v2**: Refactorización del repositorio genérico para extraer el `company_id` directamente del `ContextVar`, eliminando la necesidad de pasar el ID manualmente desde los controladores.
    * **Validación de Aislamiento**: Ejecución exitosa de `test_cqrs_filter.py`, confirmando que el sistema genera SQL con filtros de seguridad dinámicos y maneja correctamente los procesos de sistema (admin) sin contexto.
    * **Política Zero Trust**: El `company_id` del token JWT se establece como la única fuente de verdad para el filtrado de datos, mitigando riesgos de manipulación de IDs en las peticiones del frontend.

## 2026-02-18: Estandarización de Seguridad y Respuestas
*   **Hito**: Alineación con el ADN de Seguridad v2.1.
*   **Estado**: ✅ VALIDADO.
*   **Cambios**:
    *   **Pydantic Config**: Implementado `ConfigDict(extra="ignore")` en `deps.py` para compatibilidad con JWT estándar (exp, iat).
    *   **Security Context**: Migración de endpoints de `users.py` para usar `SecurityContext` en lugar de extracción manual de headers.
    *   **ApiResponse Standard**: Envoltorio de respuestas en `auth.py` para cumplir con el contrato del frontend.

---

## 2026-02-18: Resolución de Validación Pydantic y Tipado de Tokens
*   **Hito**: Estabilización del Flujo de Autenticación en 2 Fases.
*   **Estado**: ESTABLE
*   **Cambios**:
    *   **Resolución de Error 401**: Se implementó `ConfigDict(extra="ignore")` en los modelos Pydantic `TokenPayload` y `SelectionTokenPayload`. Esto evita que la validación falle por campos estándar de JWT no definidos en el modelo (como `exp` o `iat`).
    *   **Separación de Payloads**: Se crearon dos esquemas distintos para los tokens, `SelectionTokenPayload` para la fase 1 (login) y `TokenPayload` para la fase 2 (acceso final), cada uno con su propia dependencia de validación (`get_selection_payload` y `get_current_user_payload` respectivamente).
    *   **Refuerzo de Seguridad de Tenant**: Se confirmó que la dependencia `get_current_tenant_context` sigue siendo el punto de control para la validación cruzada entre el header `X-Company-ID` y el `company_id` del JWT.
    *   **Estandarización de Respuestas**: Se ajustó el endpoint `/select-company` para devolver la respuesta envuelta en el objeto `ApiResponse`, cumpliendo con el contrato global.

---

## 2026-02-04: Blindaje de Seguridad Multi-Tenant
*   **Hito**: Blindaje de Seguridad Multi-Tenant
*   **Estado**: ESTABLE / READY FOR CLOUD
*   **Cambios**:
    *   **Implementación de TenantSecurityMiddleware**: Se ha añadido una capa de validación cruzada. Ahora es obligatorio que el header `X-Company-Id` coincida exactamente con el claim `company_id` del token JWT.
    *   **Estandarización de `ApiResponse`**: Se ha unificado la estructura de respuesta para todos los endpoints.
    *   **Selección de Contexto**: Se cambió el nombre de `handshakeToken` a `selection_token` para mayor claridad en el flujo v2.1.