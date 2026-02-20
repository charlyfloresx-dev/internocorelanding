markdown
# 🔐 AUTH SERVICE - CONTEXTO DEL MICROSERVICIO

> **Status:** Active
> **Last Updated:** 2026-02-10
> **Type:** Core Service (Identity Provider)

## 1. Responsabilidad
Este servicio actúa como el **Single Source of Truth (SSOT)** para la identidad de usuarios y la estructura organizacional (Tenants). Gestiona la autenticación (OAuth2/OIDC), la emisión de tokens JWT y el control de acceso basado en roles (RBAC) a nivel de compañía.

## 2. Arquitectura & Stack
*   **Lenguaje:** Python 3.11+
*   **Framework:** FastAPI (Async).
*   **Base de Datos:** PostgreSQL (Principal) / MySQL (Soporte Legacy).
*   **ORM:** SQLAlchemy 2.0.
*   **Seguridad:** Passlib (Bcrypt), Python-Jose (JWT).

## 3. Conceptos Clave
*   **Handshake de 2 Pasos:**
    1.  **Login:** Valida credenciales -> Retorna `selection_token` + Lista de Compañías.
    2.  **Selección:** Elige compañía -> Retorna `access_token` (con `company_id` claim).
*   **Multi-tenancy:** Aislamiento lógico estricto. Cada usuario puede pertenecer a múltiples compañías con diferentes roles.
*   **Onboarding:** Manejo del flag `is_new` para guiar a usuarios nuevos a través del flujo de configuración inicial.

## 4. Dependencias
*   **Internas:** `backend/common` (Modelos base y utilidades).
*   **Externas:** AWS Secrets Manager (Gestión de claves), PostgreSQL.