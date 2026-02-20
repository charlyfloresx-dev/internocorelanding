markdown
# Service Log: InternoCore Auth-Service

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