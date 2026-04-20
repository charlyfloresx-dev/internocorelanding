# 01: Arquitectura de Sistema y Entorno Híbrido

## 1. 🏛️ Infraestructura de Soporte Validada

Esta sección documenta los componentes de infraestructura y las directrices de hardware que forman la base del ecosistema InternoCore, garantizando la observabilidad, el rendimiento y la viabilidad tanto en despliegues On-Premise como en la nube.

*   **Trazabilidad y Auditoría (Standardized Logging):** A partir de la Fase 43, todo log generado por el sistema se centraliza en el directorio `/logs`. Se emplean logs estructurados (JSON) para facilitar la ingesta en servicios como **AWS CloudWatch** o herramientas de análisis local. Este sistema garantiza la trazabilidad forense inmutable de todas las mutaciones mediante herencia de `AuditBase`.

*   **Persistencia y Rendimiento (PostgreSQL Async):** InternoCore ha estandarizado su persistencia en **PostgreSQL 15+** utilizando controladores asíncronos (`asyncpg`). El puerto estándar de operación en contenedores es el **5433**, permitiendo el aislamiento de instancias locales de base de datos.

*   **Hardware Objetivo (On-Premise Industrial):** 
    - **Servidor ERP:** Mínimo **12 GB de RAM** y CPU de 4 núcleos.
    - **Modo Kiosco (Edge):** Mini-PCs industriales (ej. Intel NUC) con **8-16 GB de RAM** y almacenamiento SSD de alta velocidad para la gestión de caché de imágenes en MinIO.

---

## 2. 📋 Checklist de Configuración de Entorno (`.env`)

El sistema utiliza una arquitectura **Zero Root Pollution**. Las configuraciones globales residen en el archivo `.env` en la raíz, mientras que configuraciones específicas pueden inyectarse por microservicio.

### `.env.standard` (Configuración PostgreSQL Async)

```env
# Configuración del motor de base de datos
DB_ENGINE=postgresql
DB_DIALECT=postgresql+asyncpg

# Credenciales de conexión (Puerto 5433 por defecto en Docker)
DB_HOST=localhost
DB_PORT=5433
DB_USER=user
DB_PASSWORD=password
DB_NAME=dbname

# Cadena de conexión para SQLAlchemy Async
CORE_DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Clave secreta para JWT
CORE_SECRET_KEY=tu_clave_secreta_industrial_12345
```

---

## 3. 🛡️ Gobernanza de Desarrollo (Phase 43)

Todo desarrollo dentro de la tesis de InternoCore debe cumplir con los siguientes pilares arquitectónicos:

1.  **Zero Trust & Multi-tenancy:** Uso mandatorio de `company_id` capturado del JWT. No se permite la visualización de datos sin el header `X-Company-ID` válido.
2.  **Clean Architecture:** Separación estricta de lógica de negocio (Servicios) y persistencia (Repositorios).
3.  **Universal Engine:** Para el ecosistema de eventos, se utiliza el motor de quórum de $N$ aprobadores, permitiendo una escalabilidad lógica sin precedentes en el manejo de contenido.
