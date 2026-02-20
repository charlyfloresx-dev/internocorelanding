# 📂 InternoCore – Documento Maestro de Identidad y Migración

## 1. 🎯 Visión General del Proyecto
**InternoCore** es una plataforma SaaS modular diseñada para la gestión de inventarios, servicios y operaciones. Está orientada a un funcionamiento híbrido (On-Premise y Cloud) sin cambios en el código base, priorizando la escalabilidad y la seguridad.

* **Estado de Origen:** Código heredado en **.NET Core 3.1** (WebApp, TodoApi).
* **Estado de Destino:** Microservicios en **Python (FastAPI)** y Frontend unificado en **Flutter**.
* **Directorio de Trabajo:** `c:\API\interno\internocore_base`.

---

## 2. 🏗️ Arquitectura Técnica de Destino

### Backend (Python / FastAPI)
* **Framework:** FastAPI (asíncrono, alto rendimiento).
* **ORM y Persistencia:** **SQLAlchemy** para garantizar independencia del motor de base de datos.
* **Motores Soportados:** PostgreSQL (Principal/Cloud) y MySQL (Compatible On-Premise).
* **Migraciones:** Gestión versionada mediante **Alembic**.

### Frontend (Flutter)
* **Estrategia:** Una sola base de código para Web, Mobile (Android/iOS) y Desktop, consumiendo la API de microservicios de forma desacoplada.

---

## 3. 🔐 Infraestructura y Seguridad (Prioridad Crítica)
Se deben mitigar los riesgos detectados en el `docker-compose.yml` actual.

* **Contenedores:** Migrar a imágenes `python:3.11-slim` o `alpine`. Prohibida la ejecución como usuario `root`.
* **Manejo de Secretos:** Los secretos deben estar fuera del código y del `docker-compose.yml`; usar archivos `.env` o gestores de secretos.
* **Auth Service (Módulo Identidad):** Implementar flujo JWT contextual:
    1. Login de usuario.
    2. Emisión de JWT inicial.
    3. Selección de empresa (Tenant).
    4. Emisión de JWT final con `company_id`, roles, permisos y validación de licencia en runtime.

---

## 4. 🗂️ Módulos y Prioridades de Desarrollo
1.  **Auth Service:** Gestión de identidad y seguridad (Atacar vulnerabilidades actuales).
2.  **Warehouse / Inventory Service:** Gestión de almacenes y productos (Foco en monetización temprana).
3.  **Tickets Service:** Soporte, mantenimiento y evidencias.
4.  **Gym Service:** Membresías, accesos y cobros.
5.  **Admin Service:** Gestión global de empresas y licencias.

---

## 5. 🛠️ Directrices Operativas para el Agente (IA)
Para asegurar que el agente trabaje correctamente, debe seguir estas reglas:

* **Regla de Oro:** **Extraer lógica, no corregir errores**. Ignorar fallos de archivos `.csproj` o NuGet del código antiguo. El objetivo es leer C# y generar Python moderno.
* **Aislamiento Multi-tenant:** Todo el código generado debe validar el `company_id` para garantizar el aislamiento de datos por empresa.
* **Independencia de DB:** No generar código SQL nativo específico; usar siempre las abstracciones del ORM para mantener la compatibilidad entre Postgres y MySQL.
* **Zero Trust:** Cada sugerencia de infraestructura (Docker/API) debe seguir los estándares más altos de seguridad.

---
# 🧬 Identidad y Gobernanza de InternoCore

## 1. Visión Técnica de Titulación
InternoCore es un ecosistema de microservicios híbrido diseñado para la convergencia entre despliegues **On-Premise** y **Cloud (AWS)**. Este proyecto se documenta bajo estándares de ingeniería para titulación profesional, priorizando la trazabilidad y la viabilidad económica.

## 2. Motor de Inteligencia y Desarrollo
* **Modelo Principal:** Gemini 1.5 Pro (Paid Tier 1).
* **Capacidad de Contexto:** 2,000,000 de tokens para análisis de código legacy y generación de documentación académica.
* **Límites Operativos:** 10,000 solicitudes diarias (RPD) y 150 solicitudes por minuto (RPM).
* **Gobernanza:** Operación mediante 4 agentes especializados (Supervisor, Orquestador, Migration, Authentication) coordinados por el archivo `global_rules.md`.

## 3. Arquitectura de Datos y Persistencia
* **Estrategia de Tenencia:** Multi-tenancy lógico basado en una **Base de Datos Única**.
* **Aislamiento:** Discriminación de datos obligatoria mediante la columna `company_id` en todas las tablas de dominio.
* **Motores Soportados:** PostgreSQL (Cloud/RDS) y MySQL 8 (On-Premise/Docker).
* **Hardware On-Premise Objetivo:** Servidor dedicado con **12 GB de RAM** y 4 núcleos de CPU.

## 4. Stack de Observabilidad y Cloud
* **Trazabilidad:** Integración nativa con **Cloud Logging** para auditoría de eventos y cumplimiento de seguridad.
* **Optimización:** El uso de **Silk Platform** se considera una directriz conceptual de rendimiento de la capa de datos, sin integración directa por ahora.
* **Infraestructura AWS:** Validación de identidad mediante SSL (ACM), gestión de DNS en Route 53 y protección de secretos en Secrets Manager.

## 5. Estrategia de Continuidad (Backups)
* **Local:** Backups cifrados en volúmenes Docker externos mediante tareas programadas.
* **Híbrido/Premium:** Sincronización redundante hacia buckets de **Amazon S3**.

## 6. 🏛️ Patrones de Arquitectura y Diseño
* **Identidad Federada (AWS):** La interacción con servicios de AWS se realizará mediante la asunción de roles de IAM a través de `boto3`. Se utilizará el patrón `assume_role_with_identity_context` que propaga el contexto de identidad del usuario (obtenido de un token JWT) a la sesión de AWS, garantizando una trazabilidad y seguridad detallada (Zero Trust).
* **Gestión de Identidad (Frontend):** La interfaz de usuario permitirá a los administradores de cada empresa definir su `nombre`, `descripción` y `email` de contacto a través de un componente específico (similar a React). Esta interfaz validará los datos en el cliente antes de persistirlos en el backend y en el almacenamiento local del navegador.
* **Transferencia de Archivos (API):** El estándar para la transferencia de archivos a través de la API será un objeto JSON que contenga `name` (nombre del archivo), `mime_type` (ej. 'application/pdf') y `content` (contenido del archivo codificado en Base64).

**Este documento es la Fuente Única de Verdad (SSOT) para el desarrollo de InternoCore.**