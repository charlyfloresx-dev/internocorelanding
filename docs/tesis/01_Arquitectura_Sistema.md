# 01: Arquitectura de Sistema y Entorno Híbrido

## 1. 🏛️ Infraestructura de Soporte Validada

Esta sección documenta los componentes de infraestructura y las directrices de hardware que forman la base del ecosistema InternoCore, garantizando la observabilidad, el rendimiento y la viabilidad tanto en despliegues On-Premise como en la nube.

*   **Trazabilidad y Auditoría (Cloud Logging):** Se empleará **Cloud Logging** de forma nativa para la ingesta y análisis de logs. Este servicio es fundamental para la auditoría de eventos de seguridad, el monitoreo del comportamiento del sistema y el cumplimiento de normativas. Todos los microservicios generarán logs estructurados que serán centralizados en esta plataforma.

*   **Optimización Conceptual de Datos (Silk Platform):** **Silk Platform** se establece como una directriz conceptual para la optimización del rendimiento en la capa de persistencia. Aunque no se realizará una integración directa en esta fase, sus principios de virtualización y desacoplamiento de la capa de datos inspirarán las decisiones de arquitectura para maximizar la eficiencia de I/O.

*   **Hardware Objetivo (On-Premise):** Para garantizar un rendimiento fluido en despliegues locales, el servidor dedicado objetivo deberá contar con un mínimo de **12 GB de RAM** y una CPU de 4 núcleos. Esta configuración está diseñada para soportar la ejecución concurrente de los microservicios contenerizados y la base de datos MySQL.

---

## 2. 📋 Checklist de Configuración de Entorno (`.env`)

Para mantener la flexibilidad entre un entorno de desarrollo local (On-Premise) y uno de producción en la nube, se utilizarán archivos de entorno `.env` específicos. A continuación, se detalla la estructura requerida.

### `.env.local` (Para despliegue On-Premise con MySQL)

```env
# Configuración del motor de base de datos
DB_ENGINE=mysql
DB_DIALECT=mysql+pymysql

# Credenciales de conexión a MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=internocore_user
DB_PASSWORD=tu_password_seguro_local
DB_NAME=internocore_db

# Cadena de conexión para SQLAlchemy
DATABASE_URL="${DB_DIALECT}://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Clave secreta para JWT
SECRET_KEY=tu_clave_secreta_para_desarrollo
```

### `.env.cloud` (Para despliegue en Cloud con PostgreSQL)

```env
# Configuración del motor de base de datos
DB_ENGINE=postgresql
DB_DIALECT=postgresql+psycopg2

# Credenciales de conexión a PostgreSQL (ej. AWS RDS)
DB_HOST=tu_endpoint_de_rds.amazonaws.com
DB_PORT=5432
DB_USER=internocore_admin
DB_PASSWORD=tu_password_seguro_de_produccion
DB_NAME=internocore_prod_db

# Cadena de conexión para SQLAlchemy
DATABASE_URL="${DB_DIALECT}://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Clave secreta para JWT (Debe cargarse desde un gestor de secretos)
SECRET_KEY=tu_clave_secreta_obtenida_de_secrets_manager
```
