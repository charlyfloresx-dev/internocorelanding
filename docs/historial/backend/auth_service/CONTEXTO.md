markdown
# 🔐 AUTH SERVICE - CONTEXTO DEL MICROSERVICIO

> **Status:** Active
> **Last Updated:** 2026-02-22
> **Type:** Core Service (Identity Provider)

## 1. Responsabilidad
Este servicio actúa como el **Single Source of Truth (SSOT)** para la identidad de usuarios y la estructura organizacional (Tenants). Gestiona la autenticación (OAuth2/OIDC), la emisión de tokens JWT y el control de acceso basado en roles (RBAC) a nivel de compañía.

## 2. Arquitectura & Stack
*   **Lenguaje:** Python 3.11+
*   **Framework:** FastAPI (Async).
*   **Base de Datos:** PostgreSQL (Principal) / MySQL (Soporte Legacy).
*   **ORM:** SQLAlchemy 2.0.
*   **Seguridad:** Passlib (Bcrypt), Python-Jose (JWT).
*   **Middleware:** Inyección de Contexto Global (ContextVar).

## 3. Conceptos Clave
*   **Handshake de 2 Pasos:**
    1.  **Login:** Valida credenciales -> Retorna `selection_token` + Lista de Compañías.
    2.  **Selección:** Elige compañía -> Retorna `access_token` (con `company_id` claim).
*   **Multi-tenancy:** Aislamiento lógico estricto. Cada usuario puede pertenecer a múltiples compañías con diferentes roles.
*   **Auditoría Robusta:**
    *   **Trazabilidad de Identidad:** Todas las entidades heredan de `AuditBase`, registrando `created_by` y `last_modified_by`.
    *   **Bootstrap de Auditoría:** En flujos de auto-registro, el sistema garantiza que `created_by` se asigna al ID del usuario recién creado, manteniendo la cadena de auditoría intacta desde el origen.
*   **Onboarding:** Manejo del flag `is_new` para guiar a usuarios nuevos a través del flujo de configuración inicial.
*   **Blindaje Zero Trust (Infraestructura):** La seguridad no depende de filtros manuales. El `BaseRepository` captura el `company_id` del `access_token` verificado y aplica el filtro SQL de forma automática y transparente.

## 4. Dependencias
*   **Internas:** `backend/common` (Modelos base, Schemas, Middlewares, Repositorio Genérico).
*   **Externas:** AWS Secrets Manager (Gestión de claves), PostgreSQL.

## 5. Contratos de Datos (DTOs)
*   **`CompanyAccess` (Respuesta de Login):** Enriquecido para proporcionar al frontend el contexto completo del usuario en cada empresa. Incluye `id`, `name`, `roles` (lista de strings) y `company_status`.
*   **`UserUpdate` (Actualización de Usuario):** Esquema de Pydantic que excluye deliberadamente el campo `company_id` para forzar su inmutabilidad a nivel de API.

## 6. Lógica de Negocio (Handlers/Services)
*   **`register_tenant_handler`:** Orquesta la creación atómica de una `Company` y su `User` administrador, estableciendo la relación y los campos de auditoría iniciales.
*   **`update_user_handler`:** Garantiza que un usuario solo pueda ser modificado por otro usuario dentro del mismo tenant y previene la modificación del `company_id` de una entidad.