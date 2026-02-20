# Vista Consolidada del Proyecto

Este archivo es una compilación de todos los archivos de documentación y configuración relevantes del proyecto, generado para tener un único punto de referencia.

---

# File: agent_work_log.md

---

```markdown
# Agent Work Log

This file tracks the history of interactions and pending tasks to maintain context across sessions.

## Session: 2026-01-04

### User Request:
"te deje revisando el auth service y me dieras una propuesta de mejora, revisa el estado actual y revisa si dejaste algun plan de trabajo, como no puedes tener acceso a sesiones pasada quiero que dejes un archivo de historial y tareas pendiente para poder analizarlo cada vez que volvamos a empezar"

### Plan:
1.  **Create a history and pending tasks file.** (Completed)
2.  **Investigate the `auth-service` to understand its current state.** (In Progress)
3.  **Analyze the investigation results and identify areas for improvement.** (Pending)
4.  **Formulate and present a detailed improvement proposal.** (Pending)

### Pending Tasks:
- Analyze the `auth-service` in `internocore_final/auth-service`.
- Propose improvements based on the analysis.

```

---

# File: log_diario_tesis.md

---

```markdown
# Log Diario de Tesis - Proyecto InternoCore

---

### **Fecha:** 2026-01-06

#### Tareas Realizadas:
- Se migró el sitio estático de un endpoint HTTP (S3) a un endpoint **HTTPS** utilizando una distribución de **AWS CloudFront**.
- Se configuró el **Origin Access Control (OAC)** con ID `E2BIZMIE1-0VI63` para securizar el acceso al bucket S3.
- Se corrigieron errores en el archivo de configuración de la distribución (`distribution.json`) para asegurar el despliegue.
- Se validó el acceso correcto al sitio a través de la URL `https://d2m14uxf7tlfyw.cloudfront.net`, confirmando la visibilidad en dispositivos móviles.

#### Tareas Pendientes:
1.  **(Prioridad Alta)** Iniciar la creación del esquema y las tablas en la base de datos RDS `internocore-auth-db`.
2.  **(Prioridad Media)** Desarrollar la lógica de negocio para la autenticación de usuarios en Python, conectando con la nueva base de datos.

#### Comandos Críticos para Referencia Futura:

**1. Actualizar Frontend en S3:**
`bash
aws s3 cp c:\API\interno\index.html s3://internocore-static-files-3709/
`

**2. Invalidar Caché de CloudFront:**
`bash
aws cloudfront create-invalidation --distribution-id d2m14uxf7tlfyw --paths "/index.html"
`

---
*Este log se actualizará automáticamente al final de cada sesión para mantener un historial de auditoría de la infraestructura de AWS.*

```

---

# File: INTERNOCORE_CHECKLIST.md

---

```markdown
# Checklist del Proyecto: InternoCore

## Despliegue y Configuración de Infraestructura

- [x] Despliegue de Frontend en S3.
- [x] Configuración de AWS CloudFront con OAC (ID: E2BIZMIE10VI63).
- [x] Activación de HTTPS y visibilidad en dispositivos móviles (URL: https://d2m14uxf7tlfyw.cloudfront.net).
- [ ] Creación de tablas en la base de datos RDS `internocore-auth-db`.
- [ ] Implementación de lógica de autenticación en Python.

```

---

# File: INTERNOCORE_MASTER_IDENTITY.MD

---

```markdown
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
```

---

# File: Protocolo.md

---

```markdown
# 📑 NexoSuite: Master Protocol (v3.0 - Hybrid Edition)

## 🎯 1. Resumen de Funcionamiento (The Vision)
NexoSuite es una plataforma **Multi-tenant** diseñada para operar en dos modalidades:
1.  **Cloud SaaS:** Operada por nosotros en AWS para múltiples empresas.
2.  **Corporate On-Premise:** Instalada en servidores privados del cliente para una sola empresa o grupo corporativo.

* **Frontera de Datos:** En cualquier modalidad, el `company_id` sigue siendo obligatorio para permitir futuras migraciones de datos entre local y nube.

---

## 🤝 2. Roles y Directivas de Despliegue

1.  **Agente de Autenticación:** Debe permitir configuraciones de "Single Tenant" donde solo exista una empresa maestra, pero manteniendo la estructura de roles y permisos.
2.  **Orquestador:** Responsable de mantener dos "recetas":
    * **Receta AWS:** Terraform/CloudFormation + RDS + S3.
    * **Receta Local:** Docker Compose + MySQL Local + MinIO (S3 Local).
3.  **Migrador:** El código generado en `nexosuite_base/` debe ser **"Provider Agnostic"**. No puede usar librerías exclusivas de AWS que no tengan un equivalente local.

---

## 📂 3. Contexto de Rutas y Estructura
**Raíz del Proyecto:** `INTERNO/`

* **Configuración:** `./config/` (Contendrá `production.env` y `local.env`).
* **Despliegue:** `./docker/compose-corporate.yml` (Para clientes locales).

---

## 🛠️ 4. Estándares para Clientes Corporativos (On-Premise)

* **Stateless Obligatorio:** Nada se guarda en el disco local del contenedor. Todo va a la DB o al almacenamiento de objetos (S3/MinIO).
* **Abstracción de Almacenamiento:** Se usará el protocolo S3. En la nube apuntamos a AWS; en local, el Orquestador levantará un contenedor de **MinIO**.
* **Base de Datos:** Los microservicios deben soportar cualquier instancia de **MySQL 8.0+**, ya sea administrada (RDS) o en contenedor.

---

## 🚦 5. Flujo de Trabajo (Híbrido)

1.  **Prioridad:** El **Auth Architect** debe crear un "Flag" de configuración: `MULTI_TENANT_MODE=True/False`.
2.  **Validación:** Cada microservicio en `nexosuite_base` debe pasar una prueba de "Local-Only" (correr sin internet) antes de ser aprobado para clientes corporativos.

---

## 🏛️ 6. Gobernanza y Supervisión (The Supervisor)

Para asegurar la coherencia del proyecto, se establece la figura del **Supervisor Agent** [.github/agents/Supervisor.agent.md]. Sus directivas son:

1.  **Auditoría de Cumplimiento:** Antes de dar por terminada una tarea de cualquier agente, el Supervisor debe validar que se respetó la Clean Architecture y el Multi-tenancy.
2.  **Sincronización de Dependencias:** El Supervisor bloqueará al **Migrador** si detecta que intenta avanzar en un módulo sin que el **Auth Architect** haya definido primero los permisos y roles correspondientes.
3.  **Validación Híbrida:** El Supervisor rechazará cualquier propuesta técnica que sea exclusiva de la nube y que no tenga una alternativa funcional para despliegues **On-Premise** (Corporativos).
4.  **Reporte de Verdad Única:** En caso de conflicto entre lo que propone el Orquestador y el Migrador, el Supervisor decidirá basándose estrictamente en este Protocolo.

---

## 📅 7. Ritual de Inicio (Daily Sync)

Cada sesión de trabajo debe iniciar consultando al **Supervisor** con el siguiente comando:
> "Dame el estado de sincronización actual. ¿Hay algún agente desviándose del protocolo o bloqueando el progreso de los demás?"
```

---

# File: README.md

---

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta id="bb-bootstrap" data-current-user="{&quot;displayName&quot;: &quot;Carlos Flores Montoya&quot;, &quot;uuid&quot;: &quot;{78af2ea6-a72c-43ae-bccf-60055793628b}&quot;, &quot;hasPremium&quot;: false, &quot;avatarUrl&quot;: &quot;https://secure.gravatar.com/avatar/af37d5ab8824d592e6d74f8513abe7c1?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FCM-5.png&quot;, &quot;isTeam&quot;: false, &quot;isSshEnabled&quot;: false, &quot;mention_id&quot;: &quot;557058:84f2c8c9-04f5-491c-ba42-d604e40f18e0&quot;, &quot;isKbdShortcutsEnabled&quot;: true, &quot;avatarUrl2x&quot;: &quot;https://secure.gravatar.com/avatar/af37d5ab8824d592e6d74f8513abe7c1?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FCM-5.png&amp;s=64&quot;, &quot;nickname&quot;: &quot;Carlos Flores&quot;, &quot;id&quot;: 6347365, &quot;isAuthenticated&quot;: true}" 
    data-atlassian-id="557058:84f2c8c9-04f5-491c-ba42-d604e40f18e0" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Bitbucket</title>
    <script nonce="5jMIjF6II2gXR3M4" type="text/javascript">(window.NREUM||(NREUM={})).loader_config={licenseKey:"a2cef8c3d3",applicationID:"521597189"};window.NREUM||(NREUM={}),__nr_require=function(e,n,t){function r(t){if(!n[t]){var i=n[t]={exports:{}};e[t][0].call(i.exports,function(n){var i=e[t][1][n];return r(i||n)},i,i.exports)}return n[t].exports}if("function"==typeof __nr_require)return __nr_require;for(var i=0;i<t.length;i++)r(t[i]);return r}({1:[function(e,n,t){function r(){}function i(e,n,t){return function(){return o(e,[u.now()].concat(f(arguments)),n?null:this,t),n?void 0:this}}var o=e("handle"),a=e(4),f=e(5),c=e("ee").get("tracer"),u=e("loader"),s=NREUM;"undefined"==typeof window.newrelic&&(newrelic=s);var p=["setPageViewName","setCustomAttribute","setErrorHandler","finished","addToTrace","inlineHit","addRelease"],l="api-",d=l+"ixn-";a(p,function(e,n){s[n]=i(l+n,!0,"api")}),s.addPageAction=i(l+"addPageAction",!0),s.setCurrentRouteName=i(l+"routeName",!0),n.exports=newrelic,s.interaction=function(){return(new r).get()};var m=r.prototype={createTracer:function(e,n){var t={},r=this,i="function"==typeof n;return o(d+"tracer",[u.now(),e,t],r),function(){if(c.emit((i?"":"no-")+"fn-start",[u.now(),r,i],t),i)try{return n.apply(this,arguments)}catch(e){throw c.emit("fn-err",[arguments,this,e],t),e}finally{c.emit("fn-end",[u.now()],t)}}}};a("actionText,setName,setAttribute,save,ignore,onEnd,getContext,end,get".split(","),function(e,n){m[n]=i(d+n)}),newrelic.noticeError=function(e,n){"string"==typeof e&&(e=new Error(e)),o("err",[e,u.now(),!1,n])}},{}],2:[function(e,n,t){function r(e,n){var t=e.getEntries();t.forEach(function(e){"first-paint"===e.name?c("timing",["fp",Math.floor(e.startTime)]):"first-contentful-paint"===e.name&&c("timing",["fcp",Math.floor(e.startTime)])})}function i(e,n){var t=e.getEntries();t.length>0&&c("lcp",[t[t.length-1]])}function o(e){if(e instanceof s&&!l){var n,t=Math.round(e.timeStamp);n=t>1e12?Date.now()-t:u.now()-t,l=!0,c("timing",["f... [truncated]
```

---

# File: TECH_STACK_RECOMMENDATION.md

---

```markdown
# TECH STACK RECOMMENDATION - INTERNOCORE

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
    *   Esto crea un **servidor de identidad OIDC completamente auto-contenido y aislado**. Los usuarios, roles y tokens de una instalación On-Premise **nunca** abandonan la red del cliente y no tienen ninguna dependencia con la nube de InternoCore.
    *   Desde la perspectiva del código, el servicio simplemente opera en un modo "single-tenant", donde todas las operaciones se asocian implícitamente a un único `tenant_id` configurado en el entorno.

*   **Identidad Escalable en la Nube (SaaS):**
    *   El mismo `Auth-Service` se despliega en nuestra infraestructura cloud.
    *   Se conecta a nuestra base de datos PostgreSQL multi-tenant.
    *   El código está diseñado para identificar al tenant en cada petición (ej. a través del subdominio o un claim en el JWT) y aplicar un **filtrado a nivel de base de datos** para que las consultas de un tenant nunca puedan acceder a los datos de otro.

Este enfoque dual, habilitado por la misma base de código, nos da la máxima flexibilidad y seguridad, cumpliendo con los requisitos de ambos modelos de negocio.
```

---

# File: dist-config.json

---

```json
{
    "CallerReference": "internocore-v2",
    "Aliases": { "Quantity": 0 },
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-Origin",
                "DomainName": "internocore-static-files-3709.s3.us-east-2.amazonaws.com",
                "S3OriginConfig": { "OriginAccessIdentity": "" },
                "OriginAccessControlId": "E2BIZMIE10VI63"
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-Origin",
        "ViewerProtocolPolicy": "redirect-to-https",
        "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6"
    },
    "Comment": "Distribucion Segura InternoCore",
    "Enabled": true
}
```

---

# File: global.json

---

```json
{
  "sdk": {
    //"version": "3.1.401"
    "version": "8.0.401"
  }
}
```

---

# File: policy.json

---

```json
{"Version":"2012-10-17","Statement":[{"Sid":"PublicReadGetObject","Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource": "arn:aws:s3:::internocore-static-files-3709/*"}]}

```

---

# File: s3-policy.json

---

```json
{
    "Version": "2012-10-17",
    "Statement": {
        "Sid": "AllowCloudFront",
        "Effect": "Allow",
        "Principal": { "Service": "cloudfront.amazonaws.com" },
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::internocore-static-files-3709/*",
        "Condition": {
            "StringEquals": {
                "AWS:SourceArn": "arn:aws:cloudfront::584094645491:distribution/E3IMB3PV6PRKNG"
            }
        }
    }
}
```

---

# File: website.json

---

```json
{"IndexDocument":{"Suffix":"index.html"}}

```

---

# File: docker-compose.yml

---

```yaml
services:
  auth-service:
    build:
      context: ./auth-service
    container_name: auth-service
    ports:
      - "8000:8000"
    volumes:
      - ./auth-service:/app
    environment:
      - DATABASE_URL=mysql+pymysql://interno_user:3709Int3rn0673!!@db:3306/interno
    depends_on:
      - db
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: mysql:8
    container_name: mysql-db
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: 3709Int3rn0673!!
      MYSQL_DATABASE: interno
      MYSQL_USER: interno_user
      MYSQL_PASSWORD: 3709Int3rn0673!!
    ports:
      - "3307:3306"
    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
```
