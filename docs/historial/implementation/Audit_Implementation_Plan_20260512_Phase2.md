# Plan de Implementación de Auditoría - Fase 2: Identidad y Acceso (Modelo Híbrido)

## 📌 Contexto
Con la Fase 1 (Aislamiento de Datos vía RLS y Muro de Hierro) completada y universalmente aplicada a los microservicios core (`wms_service`, `mes_service`, `inventory_service`, `master_data_service`), la arquitectura backend de InternoCore es impermeable a la fuga cruzada de datos.

La **Fase 2** aborda la **Capa de Identidad**. Nos centramos en prevenir la escalada de privilegios y suplantación de identidades en un ecosistema multitenant complejo donde un usuario físico (`user_id` único) puede pertenecer a múltiples empresas (`company_id`) con roles (`roles`) e información de contacto (`perfil`) totalmente diferentes por contexto.

## 🎯 Objetivos de Auditoría

1.  **Auditoría del "Tenant Selection" (Post-Auth)**
    *   **Objetivo**: Validar que el intercambio de *Login Token* por *Access Token* es criptográficamente seguro y contextualmente restrictivo.
    *   **Validaciones**:
        *   Confirmar que el `subject_id` del token inicial tiene una relación activa (`UserCompany`) con el `company_id` solicitado.
        *   Prueba de estrés de IDOR: Intentar inyectar el `company_id` de la Empresa B utilizando un Login Token legítimo emitido para el usuario en la Empresa A.
2.  **Validación de Scopes (RBAC + ABAC)**
    *   **Objetivo**: Verificar que los decoradores de seguridad de los endpoints imponen restricciones granulares basadas en Scopes.
    *   **Validaciones**:
        *   Mapeo de Scopes: Comprobar la existencia de la tabla de verdad `Role -> Scopes`.
        *   Inmutabilidad vs Dinamismo: Validar si los scopes están codificados en el JWT (preferido para latencia) o si se validan contra DB en tiempo real.
        *   Principio de Mínimo Privilegio: Rechazar peticiones al servicio `inventory` (ej. escritura) si el token posee solo el scope `masterdata:read`.
3.  **Ciclo de Vida y Estados (UserStatus / CompanyStatus)**
    *   **Objetivo**: Garantizar la revocación instantánea del acceso.
    *   **Validaciones**:
        *   Analizar si el Middleware de Seguridad consulta el estado de la entidad (o una Blacklist en Redis) en cada petición crítica.
        *   Mitigar la ventana de vulnerabilidad (time-to-live del JWT) tras desactivar a un usuario en el HCM.
4.  **Flexibilidad de Identidad (Multi-Profile)**
    *   **Objetivo**: Garantizar aislamiento a nivel de perfil de usuario.
    *   **Validaciones**:
        *   Un cambio en `display_name` o `email_contacto` en la Empresa A no debe filtrarse hacia el perfil del usuario en la Empresa B.

## 🚀 Entregables Esperados (Output de Antigravity)

1.  **Reporte de Colisiones de Identidad**: Verificación del pipeline de registro para evitar que correos electrónicos duplicados entre distintas empresas sobreescriban o mezclen `internal_id`s.
2.  **Matriz de Cobertura de Scopes**: Un mapa de calor (o reporte JSON/Markdown) detallando endpoints en `mes_service`, `wms_service`, `inventory_service` y `master_data_service` que actualmente carecen de `SecurityScopes` en FastAPI.
3.  **Validación Criptográfica**: Confirmar que el hashing asíncrono utiliza Bcrypt 4.0.1+ con un `work_factor` (coste) ≥ 12.

## 🛠️ Herramientas y Módulos a Inspeccionar
*   `auth_service/app/core/security.py` (Manejo de JWT, Password Hashing)
*   `auth_service/app/api/v1/auth.py` (Flujo de Login y Handshake de Tenant)
*   `common/security/dependencies.py` (Decoradores `RequireScopes` / `get_current_user`)
*   Modelos de Base de Datos: `User`, `Company`, `Role`, `UserCompanyRole`

---
**Status:** 🏃‍♂️ EN EJECUCIÓN (Aprobado por el usuario el 2026-05-12)
