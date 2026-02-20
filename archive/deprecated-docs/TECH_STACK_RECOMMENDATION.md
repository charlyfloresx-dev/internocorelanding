# TECH STACK RECOMMENDATION - NEXOSUITE

**Autor:** Staff Software Architect (Auth-Service)  
**Propósito:** Este documento es la 'Constitución Técnica' que define el stack tecnológico, los principios y los patrones de diseño para todos los microservicios desarrollados dentro de `nexosuite_base`. Su objetivo es garantizar la creación de un sistema robusto, escalable y mantenible que funcione de manera idéntica en dos modelos de despliegue radicalmente diferentes: **SaaS Multi-tenant (Cloud)** y **Single-tenant (On-Premise)**.

---

### 1. Sincronización de Principios Fundamentales

Antes de definir tecnologías específicas, reafirmamos los principios arquitectónicos que guiarán nuestro desarrollo. Estos no son negociables y forman la base de nuestra calidad de software.

*   **Clean Architecture:** Seguiremos una estricta separación de capas (Dominio, Aplicación, Infraestructura). El núcleo del negocio (Dominio) no tendrá dependencias externas, asegurando su pureza y facilidad para las pruebas. La Inyección de Dependencias (DI) será fundamental.
*   **Domain-Driven Design (DDD):** Nos enfocaremos en modelar el dominio del negocio de manera precisa. Utilizaremos conceptos como Entidades, Agregados y un Lenguaje Ubicuo para alinear el código con la realidad operativa.
*   **Lenguaje Principal:** **Python 3.11+**. Específicamente, utilizaremos **FastAPI** como el framework principal para la creación de APIs por su alto rendimiento, sintaxis moderna, sistema de inyección de dependencias y generación automática de documentación OpenAPI.
*   **Base de Datos Relacional:** **PostgreSQL (última versión estable)**. Es la elección por defecto por su robustez, extensibilidad, rendimiento y excelente soporte en todos los entornos.
*   **Estándares de Seguridad:**
    *   **Hashing de Contraseñas:** **Bcrypt** es el estándar obligatorio.
    *   **Protocolo de Identidad:** **OpenID Connect (OIDC) sobre OAuth 2.0**.
    *   **Formato de Tokens:** **JSON Web Tokens (JWT)**.

---

### 2. El Desafío Híbrido: Un Código, Dos Modelos de Despliegue

El requisito principal es mantener una **única base de código fuente** que funcione sin modificaciones tanto en nuestro entorno cloud multi-tenant como en las instalaciones on-premise de un solo cliente.

La estrategia para lograr esto es simple pero poderosa: **la configuración del entorno dicta el comportamiento de la aplicación, no el código.** El mismo artefacto de despliegue (una imagen de Docker) se comportará de una u otra forma basándose exclusivamente en las variables de entorno que se le proporcionen al arrancar.

---

### 3. Stack Tecnológico Unificado

Este es el conjunto de herramientas que nos permitirá implementar la estrategia anterior.

*   **Contenerización:** **Docker**.
    *   **¿Por qué?:** Cada microservicio será empaquetado como una imagen de Docker. Esto nos da portabilidad absoluta y consistencia entre los entornos de desarrollo, pruebas y producción. Se eliminan los problemas de "en mi máquina funciona".
    *   **Despliegue On-Premise:** Se entregará a los clientes un archivo `docker-compose.yml` que orquestará el microservicio, su base de datos PostgreSQL y cualquier otra dependencia. La instalación se simplifica a un solo comando.

*   **Base de Datos:** **PostgreSQL**.
    *   **¿Por qué?:** Funciona de manera idéntica ya sea como un contenedor de Docker en una instalación On-Premise o como un servicio gestionado en la nube (ej. Amazon RDS, Azure Database for PostgreSQL). No hay cambios en el código de acceso a datos.

*   **Manejo de Secretos y Configuración:** **Variables de Entorno**.
    *   **¿Por qué?:** Siguiendo la metodología de [The Twelve-Factor App](https://12factor.net/config), toda la configuración que varía entre despliegues (credenciales de BBDD, secretos de JWT, URLs de servicios) se inyectará a través de variables de entorno.
    *   **Implementación Cloud:** Las variables de entorno serán pobladas por el sistema de orquestación (ej. Kubernetes Secrets) o un servicio de gestión de secretos (ej. AWS Secrets Manager, Azure Key Vault).
    *   **Implementación On-Premise:** Las variables de entorno se definirán directamente en el archivo `docker-compose.yml`.

*   **Almacenamiento de Archivos (Blobs):** **Abstracción de Repositorio**.
    *   **¿Por qué?:** Es el único punto donde la infraestructura subyacente es fundamentalmente diferente. La solución es abstraerla.
    *   **Implementación:** Crearemos una interfaz `IFileStorage` en la capa de Aplicación. Luego, tendremos dos implementaciones en la capa de Infraestructura:
        1.  `S3FileStorage`: Para el entorno Cloud, que utilizará un bucket de S3 (o similar de otro proveedor).
        2.  `LocalFileStorage`: Para el entorno On-Premise, que guardará los archivos en un volumen de Docker montado en el sistema de archivos local del servidor del cliente.
    *   La inyección de dependencias seleccionará la implementación correcta al inicio de la aplicación basándose en una variable de entorno (`STORAGE_TYPE=S3` o `STORAGE_TYPE=Local`).

---

### 4. Frontera de Seguridad y Manejo de Identidad

Este punto es crítico para la autonomía de los clientes On-Premise.

*   **Identidad Soberana On-Premise:**
    *   El `Auth-Service` se despliega como un contenedor Docker en la infraestructura del cliente. Se configura para usar su propia base de datos PostgreSQL local.
    *   Esto crea un **servidor de identidad OIDC completamente auto-contenido y aislado**. Los usuarios, roles y tokens de una instalación On-Premise **nunca** abandonan la red del cliente y no tienen ninguna dependencia con la nube de NexoSuite.
    *   Desde la perspectiva del código, el servicio simplemente opera en un modo "single-tenant", donde todas las operaciones se asocian implícitamente a un único `tenant_id` configurado en el entorno.

*   **Identidad Escalable en la Nube (SaaS):**
    *   El mismo `Auth-Service` se despliega en nuestra infraestructura cloud.
    *   Se conecta a nuestra base de datos PostgreSQL multi-tenant.
    *   El código está diseñado para identificar al tenant en cada petición (ej. a través del subdominio o un claim en el JWT) y aplicar un **filtrado a nivel de base de datos** para que las consultas de un tenant nunca puedan acceder a los datos de otro.

Este enfoque dual, habilitado por la misma base de código, nos da la máxima flexibilidad y seguridad, cumpliendo con los requisitos de ambos modelos de negocio.
