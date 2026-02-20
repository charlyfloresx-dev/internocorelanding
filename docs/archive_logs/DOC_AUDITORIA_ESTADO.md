# DOC_AUDITORIA_ESTADO.md

## Auditoría de Estado del Auth-Service (Contrato de Autenticación y Tenancy)

**Fecha de Auditoría:** 2026-01-18

### 1. ¿Qué endpoints actuales cumplen con el formato StandardResponse?

Todos los endpoints principales implementados o modificados recientemente cumplen con el formato `StandardResponse`. Estos incluyen:

*   **`app/api/v1/endpoints/companies.py`**:
    *   `POST /api/v1/companies/` (Crear empresa)
    *   `GET /api/v1/companies/{company_id}` (Leer empresa por ID)
    *   `GET /api/v1/companies/` (Listar empresas)
    *   `PUT /api/v1/companies/{company_id}` (Actualizar empresa)
    *   `DELETE /api/v1/companies/{company_id}` (Eliminar empresa)

*   **`app/api/v1/endpoints/users.py`**:
    *   `POST /api/v1/users/` (Crear usuario)

*   **`app/api/v1/endpoints/auth.py`**:
    *   `POST /api/v1/auth/login` (Paso 1: Autenticación inicial y token de selección)
    *   `POST /api/v1/auth/select-company` (Paso 2: Selección de empresa y JWT final)
    *   `GET /api/v1/auth/my-companies` (Listar empresas asociadas al usuario)

Todos estos endpoints utilizan el `StandardResponse` y `ResponseMeta` definidos en `app/schemas/responses.py` para estructurar sus salidas con `status`, `data`, `message` y `meta`.

### 2. ¿Existe la tabla intermedia para soportar el array de tenants (N:N)?

**Sí, la tabla intermedia existe.** Se ha implementado el modelo `UserCompanyRole` en `app/models/user_company_role.py`. Esta tabla de asociación soporta una relación N:N entre `User`, `Company` y `Role`, permitiendo que un usuario esté asociado a múltiples empresas, cada una con un rol específico.

Los modelos `User` y `Company` han sido actualizados para incluir la relación `user_company_roles` con esta tabla intermedia.

### 3. ¿El modelo de User actual soporta el flag isNew o necesitamos una tabla de perfil por empresa?

El flag `isNew` **no se almacena directamente en el modelo `User`**, sino que se **calcula dinámicamente** en el endpoint `POST /api/v1/auth/login`. Este flag se incluye en el `SelectionTokenResponse` al inicio del flujo de autenticación.

La lógica actual para `isNew` se basa en la cantidad de asociaciones `UserCompanyRole` que tiene un usuario:
*   Es `True` si el usuario no tiene ninguna asociación con empresas.
*   Es `True` si el usuario tiene una única asociación que presumiblemente fue creada durante su registro inicial (si se le asignó una empresa primaria).
*   Es `False` en cualquier otro caso, implicando que el usuario ya ha interactuado o configurado su perfil en múltiples contextos.

En cuanto a la necesidad de una "tabla de perfil por empresa" (`user_company_context`):
*   **Actualmente, no existe una tabla explícita llamada `user_company_context`.** La tabla `UserCompanyRole` gestiona las asociaciones usuario-empresa-rol.
*   Si la especificación de frontend para "registros de actividad o perfil completo" en `user_company_context` implica almacenar datos adicionales y persistentes *específicos para el perfil de un usuario dentro de una empresa particular* (más allá de su rol), entonces **sí, se necesitaría una nueva tabla** (e.g., `UserProfileCompanyContext` o `UserCompanyProfile`). Esta tabla contendría campos como `user_id`, `company_id`, `last_activity_date`, `profile_completion_status`, etc.
*   **Recomendación:** Para la lógica del flag `isNew` tal como se entiende ahora, la implementación actual es suficiente. Sin embargo, si la 'actividad' o 'perfil completo' son atributos que deben persistir por empresa y ser gestionados, **se recomienda crear una tabla dedicada a ese contexto de usuario-empresa-perfil.** Por el momento, el flag `isNew` es una heurística útil para el flujo de onboarding.

---
