# 🏛️ INTERNO CORE - ARQUITECTURA Y STACK TECNOLÓGICO

> **Documento Unificado:** Consolida la visión técnica, principios de diseño y estrategia híbrida.
> **Fuente Original:** TECH_STACK_RECOMMENDATION_INTERNOCORE.md
> **Última Actualización:** 2026-02-12

## 1. Principios Fundamentales

La arquitectura de **Interno Core** se rige por principios no negociables que garantizan la calidad y mantenibilidad del software:

*   **Clean Architecture:** Separación estricta de capas (Dominio, Aplicación, Infraestructura). El núcleo del negocio (Dominio) permanece puro y sin dependencias externas.
*   **Domain-Driven Design (DDD):** Modelado preciso del negocio utilizando Entidades, Agregados y Lenguaje Ubicuo.
*   **Single Source of Truth (SSOT):** Unificación de lógica y datos para evitar duplicidad y desincronización.
*   **Zero Trust:** Validación continua de identidad y permisos, sin confiar en la persistencia local o redes internas.

## 2. Stack Tecnológico (Core Stack)

### Backend
*   **Lenguaje:** Python 3.11+
*   **Framework:** FastAPI (Alto rendimiento, Async, OpenAPI).
*   **ORM:** SQLAlchemy 2.0 (Async).
*   **Base de Datos:** PostgreSQL (Producción Cloud/On-Premise) / MySQL (Soporte Legacy/Local).
*   **Seguridad:** OAuth2 con OIDC, JWT, Bcrypt (v4.0.1).

### Frontend
*   **Framework:** Angular 19+ (Zoneless Architecture).
*   **Estado:** Angular Signals (signal, computed, effect).
*   **Estilos:** Tailwind CSS.

### Infraestructura & DevOps
*   **Contenerización:** Docker (Imágenes unificadas).
*   **Orquestación:** Docker Compose (Local/On-Premise), ECS/Kubernetes (Cloud AWS).

---

## 3. El Desafío Híbrido: Un Código, Dos Modelos

El requisito distintivo de Interno Core es mantener una **única base de código** que opere en dos entornos radicalmente diferentes.

### Estrategia de Configuración
La configuración del entorno dicta el comportamiento, no el código.

**SaaS Multi-tenant (Cloud):**

*   **Despliegue:** AWS (ECS/EKS).
*   **Datos:** Base de datos PostgreSQL Multi-tenant.
*   **Aislamiento:** Lógico (Row-level security, filtrado por `company_id`).
*   **Secretos:** AWS Secrets Manager.

**Single-tenant (On-Premise):**

*   **Despliegue:** Servidor local del cliente (Docker Compose).
*   **Datos:** Base de datos PostgreSQL/MySQL local dedicada.
*   **Aislamiento:** Físico (Infraestructura separada).
*   **Secretos:** Variables de entorno locales (`.env`).

---

## 4. Protocolo de Expansión: Nuevos Microservicios
Para garantizar la integridad y evitar la "contaminación" del repositorio, todo nuevo desarrollo debe seguir este protocolo estrictamente.

### 4.1 Ubicación y Estructura (Scaffolding)
Queda estrictamente prohibido generar archivos de lógica (`.py`), configuraciones o documentación técnica en la raíz del repositorio (`/`) o en la raíz de `/backend`. Todo debe residir en su carpeta de servicio.

**Estructura Estándar por Servicio:** `/backend/[servicio]_service/`

*   `app/api/v1/endpoints/`: Controladores y definición de rutas.
*   `app/services/`: Lógica de negocio y CQRS.
*   `app/models/`: Entidades SQLAlchemy (Heredan de `MultiTenantBase`).
*   `app/infrastructure/`: Configuración de DB (`database.py`) y clientes externos.
*   `app/core/`: Enums, constantes y configuraciones locales.
*   `app/main.py`: Punto de entrada FastAPI.
*   `alembic/versions/`: Scripts de migración de base de datos.
*   `Dockerfile`: Configuración multi-stage que referencia a `/common`.

### 4.2 Guardrails para la IA (Instrucciones Críticas)
*   **Zero Root Pollution:** No crear archivos en la raíz. El incumplimiento se considera un error crítico de arquitectura.
*   **Herencia de Tenancy:** Todos los modelos deben importar y heredar de `common.models.MultiTenantBase`. El campo `company_id` es obligatorio.
*   **Contexto de Build:** El contexto para Docker es siempre `/backend`. El `PYTHONPATH` debe incluir `/app` para resolver `from app...` y `from common...`.
*   **Response Pattern:** Es obligatorio el uso de `ApiResponse` (de `common.schemas`) para todas las respuestas de la API.

---

## 5. Patrones de Diseño Clave

### Abstracción de Almacenamiento (IFileStorage)
*   **Interfaz:** `IFileStorage` (Capa de Aplicación).
*   **Implementaciones:** `S3FileStorage` (AWS) y `LocalFileStorage` (On-Premise).
*   **Selección:** Inyección de dependencias basada en `STORAGE_TYPE`.

### Identidad Soberana vs. Centralizada
*   **On-Premise:** El `Auth-Service` local actúa como un IdP autocontenido.
*   **Cloud:** El `Auth-Service` central gestiona múltiples tenants con aislamiento estricto mediante `CompanyAccessDto`.

### Estrategia de Internacionalización (i18n)
*   **Backend Agnostic:** El backend es agnóstico al idioma del usuario. Envía claves de traducción (`translation_key`) en lugar de textos traducidos.
*   **Frontend Responsibility:** La resolución de textos se realiza en el cliente utilizando archivos locales (JSON) para maximizar el rendimiento y la escalabilidad.
*   **Fallback:** Si no existe traducción para la clave, se utiliza el campo `name` original de la base de datos.

---

## 6. Variables de Entorno Críticas

*   `ENV_MODE`: `local`, `dev`, `prod`, `aws`.
*   `MULTI_TENANT_MODE`: `true` (Cloud), `false` (On-Premise).
*   `DB_ENGINE`: `postgresql`, `mysql`.
*   `STORAGE_TYPE`: `s3`, `local`.