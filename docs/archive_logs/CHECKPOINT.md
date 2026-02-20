# CHECKPOINT: Sincronización Pre-Despliegue AWS

## Resumen

Este documento actúa como un checklist de los requisitos técnicos obligatorios que deben cumplirse en el `auth-service` antes de proceder con el despliegue en la infraestructura de AWS. El objetivo es alinear el comportamiento del backend con las necesidades del frontend y saldar deuda técnica crítica.

---

## Requisitos Técnicos Obligatorios

### 1. Contrato de API v1.1 - `ApiResponse`
- [x] **Estado:** Completado
- **Descripción:** Todas las respuestas de la API han sido estandarizadas bajo el objeto `ApiResponse`. El modelo se ha centralizado en `backend/common/responses.py` y todos los endpoints de la v1 han sido refactorizados para implementarlo.
- **Campos:**
    - `status`: `string` (valores: "success", "error")
    - `data`: `object` | `array` | `null` (el payload de la respuesta)
    - `message`: `string` (mensaje descriptivo para toasts o notificaciones en el frontend)
    - `meta`: `object` (metadatos como `trace_id`, `latency`, etc.)

### 2. Flujo de Autenticación en Dos Tiempos
- [x] **Estado:** Completado
- **Descripción:** Se ha implementado y verificado el flujo de autenticación en dos pasos.
- **2.1. Endpoint `POST /auth/login`**
    - [x] **Acción:** Valida credenciales y devuelve un `handshakeToken` junto con la lista de `tenants` del usuario.
- **2.2. Endpoint `POST /auth/select-company`**
    - [x] **Acción:** Valida el `handshakeToken` y `tenant_id` para generar el `accessToken` final con los claims correspondientes (`company_id`, `roles`, `permissions`).

### 3. Lógica de Onboarding (`isNew` Flag)
- [x] **Estado:** Completado
- **Descripción:** La lógica para el flag `isNew` ha sido implementada en el endpoint `/auth/login`.
- **Lógica:** El flag se calcula correctamente basándose en el campo `is_new` del modelo `UserCompanyRole`, que por defecto es `true`.

### 4. Limpieza de Deuda Técnica
- [x] **Estado:** Completado
- **Descripción:** Unificar la lógica de conexión y gestión de la sesión de base de datos.
- **Acción:** Se ha neutralizado el archivo conflictivo `backend/auth_service/app/database.py` (vaciando su contenido). Toda la lógica de conexión a base de datos ahora reside en `backend/auth_service/app/core/database.py`, que es la única fuente de verdad.

### 5. Refactorización Clean Architecture & CQRS (En Progreso)
- [ ] **Estado:** Iniciado
- **Descripción:** Migración del código base a una arquitectura hexagonal estricta (Clean Architecture) con separación de responsabilidades mediante CQRS.
- **Componentes Base:**
    - `backend/common/abstractions.py`: Define `Entity`, `IAggregateRoot`, `IDomainEvent`.
    - `backend/common/cqrs.py`: Define interfaces `ICommand`, `IQuery`, `IHandler`.
- **Reglas de Oro:**
    1. **Dominio Puro:** Las entidades de dominio NO deben tener dependencias de frameworks (FastAPI, SQLAlchemy).
    2. **Casos de Uso:** Toda lógica de negocio debe residir en un `CommandHandler` o `QueryHandler`, nunca en el controlador (Endpoint).
    3. **DTOs:** Los controladores reciben Pydantic Models y los convierten a `Commands`/`Queries` antes de pasar al dominio.
    4. **Multitenancy:** Todo `Command` que mute estado debe validar el `tenant_id` del contexto actual.

---
## Sincronización de Agentes
Este documento representa el estado acordado de tareas. Cualquier cambio o progreso debe ser reflejado aquí.
