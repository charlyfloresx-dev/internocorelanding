# 📂 INTERNOCORE_MASTER.MD - The Single Source of Truth

**Version:** 1.0  
**Date:** 2026-01-13  
**Status:** Consolidated from existing project documentation.

---

## 1. Visión General del Proyecto

### Qué es InternoCore
InternoCore is a modular, hybrid SaaS platform designed as a comprehensive Manufacturing Execution System (MES). It aims to bridge the gap between shop-floor operations and executive-level control by providing real-time visibility and robust data architecture. The project is also referred to as `NexoSuite` in some documents; `InternoCore` is the canonical name.

### Para qué existe
The platform was created to solve critical inefficiencies in high-regulation manufacturing environments (Aerospace, Medical, Electronics). It provides a unified ecosystem for managing inventory, production, quality, and other operational domains that traditionally rely on disparate or manual systems.

### Problemas que resuelve
-   **Inventory & WIP Tracking:** Drastically reduces lost or untracked Work-In-Progress. One key achievement cited is the reduction of WIP from **$4.8M USD to $40K**.
-   **Operational Inefficiency:** Increases the efficiency of digital tool usage on the shop floor.
-   **Lack of Real-Time Visibility:** Replaces static reports with live, interactive dashboards, enabling data-driven decisions.

### Público objetivo
The primary audience is manufacturing companies in highly regulated sectors (AS9100, FDA Class III). The platform is designed for two deployment models:
1.  **Cloud SaaS:** A multi-tenant solution hosted on AWS.
2.  **Corporate On-Premise:** A single-tenant version for clients who require data to remain within their own infrastructure.

---

## 2. ADN del Proyecto (Extraído)

### Principios arquitectónicos
-   **Clean Architecture:** A non-negotiable principle involving a strict separation of layers (Domain, Application, Infrastructure). The Domain core must have no external dependencies.
-   **Domain-Driven Design (DDD):** A focus on accurately modeling the business domain using concepts like Entities, Aggregates, and a Ubiquitous Language.
-   **Hybrid Deployment:** The system MUST operate identically on both multi-tenant Cloud and single-tenant On-Premise environments from a single codebase. The environment's configuration dictates behavior, not the code itself.
-   **Provider Agnostic:** Code should not be tied to a specific cloud provider's proprietary services if it compromises the ability to deploy on-premise.
-   **Stateless Services:** All microservices must be stateless to support horizontal scaling and resilience. Data should not be stored on a container's local disk.

### Decisiones técnicas históricas
-   **Technology Shift:** The project is an active migration from a **.NET Core 3.1 monolith** to a microservices architecture using **Python 3.11+ (FastAPI)**.
-   **Frontend:** The strategic direction for the frontend is **Flutter**, enabling a single codebase for Web, Mobile, and Desktop applications.
-   **AI Usage Governance:** A minor billing incident with the Gemini API led to the establishment of strict governance policies for using AI in development, emphasizing cost control, security (IP-restricted keys), and explicit, monitored usage.

### Restricciones conocidas
-   **On-Premise Hardware Target:** The minimum server specification for on-premise deployment is **12 GB RAM** and a 4-core CPU.
-   **Legacy Code Rule:** The primary directive for AI agents working on the migration is to **extract logic, not fix bugs** in the old .NET code.

### Filosofía de diseño
> "The configuration of the environment dictates the behavior of the application, not the code."

---

## 3. Arquitectura General

### Monolito → Microservicios
The architecture is transitioning from a monolithic .NET application to a distributed system of microservices, each representing a distinct Bounded Context.

### Bounded Contexts
Each microservice acts as a bounded context, with a clear domain and responsibilities. The primary modules identified are detailed in Section 4.

### Comunicación entre servicios
Communication is handled via RESTful APIs, facilitated by the FastAPI framework for each service.

### Multi-tenant strategy
-   **Model:** Logical multi-tenancy within a **single database**.
-   **Isolation:** Data is strictly isolated between tenants using a mandatory `company_id` (UUID) column on all relevant tables.
-   **Authentication:** The user's active `company_id` is a required claim in their JSON Web Token (JWT) and is used for data scoping in every request.
-   **Configuration:** A `MULTI_TENANT_MODE=True/False` flag in the environment configuration will switch the system's behavior, although the `company_id` remains mandatory in the database structure to facilitate future data migrations.

---

## 4. Módulos del Sistema

| Módulo | Propósito | Responsabilidades | Dependencias | Estado Actual / Prioridad |
| :--- | :--- | :--- | :--- | :--- |
| **Auth Service** | Gestión de identidad y acceso. | Users, roles, permissions, licenses, JWT generation, multi-tenancy context. | Core (all others depend on it) | **1 (Critical)** - Foundation |
| **Warehouse** | Gestión de inventario y almacenes. | Item tracking, warehouse locations, purchase orders, receipts. | Auth | **2 (High)** - Key monetization module |
| **Tickets** | Sistema de soporte y mantenimiento. | Ticket creation, evidence tracking, issue resolution workflows. | Auth | **3 (Medium)** |
| **Production** | Ejecución de manufactura (MES). | Work orders, resource planning, production tracking, downtime. | Auth, Warehouse | **Medium** |
| **Human Resource**| Gestión de personal. | Employee records, shifts. | Auth | **Low** |
| **HealthCare** | Gestión de servicios de salud. | Medical records, appointments, prescriptions. | Auth, HR | **Low** - Specialized module |
| **Quality** | Control de calidad. | Defect tracking, quality assurance workflows. | Auth, Production | **Low** |
| **Security** | Seguridad física y de acceso. | Guardhouse logs, visitor management, employee access logs. | Auth, HR | **Low** |
| **Gym Service** | Gestión de membresías de gimnasio. | Memberships, facility access, payments. | Auth | **Low** - Specialized module |
| **Admin Service** | Gestión global de la plataforma. | Onboarding new companies, managing global licenses. | Auth | **Low** |

---

## 5. Autenticación y Usuarios

### Flujo de login
1.  A user authenticates with their credentials (username/password).
2.  The system issues an initial, short-lived JWT containing basic user identity.
3.  The user selects which company (tenant) they wish to access from a list of their associated companies.
4.  The system issues a final, contextual JWT that includes the selected `company_id`, roles, and permissions for that specific tenant. This token is used for all subsequent API calls.

### JWT contextual
The JWT is the core of the security model. Its payload MUST contain:
-   `sub`: The user's unique ID.
-   `company_id`: The UUID of the tenant the user is currently acting within.
-   `roles`: A list of roles the user holds within that company.
-   `permissions`: A list of specific actions the user can perform.
-   `exp`: A mandatory expiration timestamp.
-   `license_valid`: A boolean indicating if the company's license is active.

### Roles y permisos
A Role-Based Access Control (RBAC) system is implemented. Roles (e.g., `Admin`, `Supervisor`, `Operator`) are defined, and permissions are granted to these roles. The user's token contains the roles they possess for a given company.

### Licencias
Company licenses are checked at runtime. The validity of a company's license is embedded in the JWT to allow services to enforce access without repeated database lookups.

---

## 6. Modelo de Datos (Conceptual)

### Entidades comunes
-   **Company:** Represents a tenant in the system.
-   **User:** Represents an individual who can have access to one or more companies.
-   **Role / Permission:** Defines the RBAC structure.
-   **License:** Governs a company's access to modules and features.
-   **`company_id`:** This UUID is the central foreign key that links all tenant-specific data (e.g., Items, Work Orders, Tickets) back to a `Company`.

### Relación entre módulos
Modules are logically separate but linked through the common `company_id` and `user_id`. For example, a `WorkOrder` in the Production module is tied to a `company_id` and may be updated by a `User` whose identity is managed by the Auth module.

---

## 7. Infraestructura

### Despliegue Híbrido
| Componente | Despliegue Cloud (AWS) | Despliegue On-Premise |
| :--- | :--- | :--- |
| **Orquestación** | Amazon ECS / Kubernetes | `docker-compose.yml` |
| **Base de Datos**| **PostgreSQL** (via AWS RDS) | **MySQL 8.0+** (in Docker container) |
| **File Storage** | **Amazon S3** | **MinIO** (S3-compatible API) or local disk via mounted volume |
| **Config/Secrets**| AWS Secrets Manager / Parameter Store | `.env` file loaded by Docker Compose |
| **Networking** | VPC, Route 53, CloudFront | Local network |

### Stack Tecnológico
-   **Containerization:** **Docker** is mandatory for all services.
-   **ORM:** **SQLAlchemy** is used in Python to ensure database agnosticism.
-   **Migrations:** **Alembic** is used for version-controlled database schema migrations.
-   **Environment Variables:** Configuration is handled exclusively through environment variables, following the 12-Factor App methodology.

---

## 8. Seguridad

### Zero Trust
A "Zero Trust" model is the guiding security principle. Every API request must be independently authenticated and authorized via the JWT token.

### Middleware
-   **JWT Validation:** A middleware component in each service is responsible for validating the JWT on every incoming request.
-   **Global Exception Handler:** Prevents application tracebacks from leaking to the client, returning a standardized error response instead.

### Auditoría
-   A dedicated `SecurityLog` table records all critical security events (e.g., successful logins, failed login attempts, password changes).
-   In the cloud, structured logs are sent to **AWS Cloud Logging** for centralized analysis and monitoring.

### Contraseñas y Secretos
-   **Password Hashing:** **Bcrypt** is the mandatory algorithm for hashing user passwords.
-   **Secret Management:** In cloud environments, all secrets (API keys, database passwords) must be stored in AWS Secrets Manager. In on-premise deployments, they are managed via environment files secured by the client.

---

## 9. Roadmap y Monetización

### MVP y Prioridades
1.  **Auth Service:** The absolute first priority. It is the foundation for all other services and must be secure and robust.
2.  **Warehouse / Inventory Service:** The primary module for early monetization, as it provides immediate, tangible value in solving inventory tracking issues.
3.  **Tickets Service:** A strong secondary module for adding value.
4.  **Other Modules:** (Production, HR, etc.) to be developed subsequently.

### Qué ya genera valor
The concepts and logic have been validated in previous on-premise versions (the legacy .NET system), which successfully demonstrated significant value by recovering inventory costs and improving operational efficiency. The goal now is to deliver this value through a modern, scalable, and maintainable SaaS platform.

---

## 10. Pendientes Técnicos Detectados

### Inconsistencias y Duplicaciones
-   **Project Naming:** The use of `InternoCore` and `NexoSuite` has been consolidated to `InternoCore`.
-   **Frontend Framework:** Documentation mentioned both `React` and `Flutter`. The official architectural choice is **Flutter**.
-   **Documentation:** Many documents contained overlapping or duplicated information. This master file supersedes them.

### Riesgos y Deuda Técnica
-   **Legacy Monolith:** The entire `.NET Core 3.1` codebase is considered technical debt and is the subject of the migration.
-   **Security Vulnerabilities:** The original `docker-compose.yml` file contained hardcoded secrets and ran services as the `root` user. This is a critical risk to be remediated in the new architecture.
-   **Database Constraints:** A critical design flaw was identified where a user's `email` had a unique constraint at the table level. This has been corrected to a composite unique constraint on `(email, company_id)` to allow a user to exist across multiple tenants.

---

## 11. Protocolo de Trazabilidad y Seguridad

Antes de proceder con las fases de homologación, debes seguir este Protocolo de Trazabilidad:

*   **Registro de Estado Anterior:** Por cada archivo que modifiques, debes imprimir en el log el estado previo (o una referencia clara) de la firma del método o modelo que estás cambiando.
*   **Verbose Logging:** Cada acción de 'Refactor' debe ir acompañada de un mensaje: `[REFACTOR-LOG] Modificando {Clase/Archivo} para cumplir con {Fase X}: {Cambio realizado}`.
*   **Snapshot de Modelos:** Si cambias un modelo de Pydantic o una Interfaz de Angular, imprime la estructura final resultante en el log para que podamos validarla visualmente.
*   **Rollback Plan:** Si una fase rompe la compilación, debes ser capaz de indicarme el comando o el código previo para regresar al estado estable anterior.


# 📂 INTERNOCORE: DOCUMENTO ÚNICO DE CONTEXTO (SSOT)
**Versión:** 2.1 (Consolidada)  
**Estado:** Activo / Desarrollo  
**Última Sincronización:** 2026-01-28  

---

## 🚀 1. Visión y Propósito
InternoCore es un sistema de ejecución de manufactura (**MES**) híbrido diseñado para sectores de alta regulación.
- **Arquitectura:** SaaS Multitenancy con Clean Architecture (Hexagonal) y CQRS.
- **Stack:** Backend Python (FastAPI), Frontend Angular 19.1.0 (Signals/Zoneless), DB PostgreSQL/SQLite.

---

## 🏛️ 2. Arquitectura de Referencia
### Backend (Python/FastAPI)
- **Dominio Puro:** Entidades en `backend/common/abstractions.py` sin dependencias de frameworks.
- **Multitenancy:** Restricción única compuesta en `(email, company_id)`. El `company_id` es obligatorio en todas las transacciones.
- **Estructura de Respuesta (`ApiResponse`):** Todas las respuestas siguen el formato `{ status, data, message, meta }`.

### Frontend (Angular)
- **Estado:** Gestionado mediante **Signals** (`currentUser`, `authStep`, `currentContext`).
- **Persistence:** LocalStorage con los prefijos `interno_auth_`.
- **Interceptors:** Inyección automática de `Authorization` y `X-Company-Id`.

---

## 🔐 3. Flujo Crítico de Autenticación (Handshake)
1. **Login (`/v1/auth/login`):** Valida credenciales y devuelve un `selection_token` y lista de empresas.
2. **Selección (`/v1/auth/select-company`):** El usuario elige empresa. El backend emite el **Access Token definitivo** con el contexto de `company_id` y roles.

---

## ✅ 4. Checklist de Estado Actual

### Finalizado (Ready)
- [x] **Auth Handshake:** Proceso de login y selección estabilizado en el frontend.
- [x] **Data Mapping:** Mapeo de JSON de 4 niveles (`status`, `data`, `message`, `meta`).
- [x] **Common:** Sincronización de modelos `BaseEntity` y `MultiTenantBase`.
- [x] **Seed Data:** Usuario `charly@internocore.app` con 3 empresas demo.

### Próximos Pasos (Pendientes)
- [ ] **Redirección Onboarding:** Forzar navegación a `/onboarding` si `is_new: true`.
- [ ] **Filtrado de Menús:** Dinamizar el sidebar según los roles del token.
- [x] **Validación de Headers:** Confirmar envío de `X-Company-Id` en peticiones de negocio.
- [ ] **Acceso Operativo (Fase 2):** Implementar endpoint `/auth/fast-login` para escaneo de Badge/RFID.
- [ ] **Modelado de Usuario:** Agregar campo `badge_id` a la entidad `User` en `common`.
- [ ] **Configuración AWS (Mañana):** Despliegue de prueba para visibilidad externa del API.

---

## 🔍 5. Guía de Logs y Depuración
- **Backend:** `docker compose logs -f auth-service`.
- **Frontend:** Consola del navegador filtrada por `[AuthService]`.
- **Network:** Pestaña F12 para verificar cabeceras `Authorization`.