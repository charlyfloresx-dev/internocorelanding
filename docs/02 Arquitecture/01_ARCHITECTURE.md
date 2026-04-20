# 🏛️ INTERNO CORE - ARQUITECTURA Y STACK TECNOLÓGICO

> **Documento Unificado:** Consolida la visión técnica, principios de diseño y estrategia híbrida.
> **Last Updated:** 2026-04-13
> **Status:** Phase 43 - Root Governance Standardized

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

### Abstracción de Almacenamiento (StorageProvider)
*   **Interfaz Unificada**: `StorageProvider` (Capa de Infraestructura Común). Centraliza la lógica de activos para todos los microservicios.
*   **Implementaciones**: `S3StorageProvider` (AWS S3 / LocalStack) y `LocalStorageProvider` (On-Premise / Local dev).
*   **Jerarquía Multi-tenant**: Aislamiento físico de archivos mediante prefijos de S3: `{company_id}/{module}/{sub-path}/{filename}`.
*   **Seguridad de Acceso**: Uso mandatorio de URLs pre-firmadas (Pre-signed URLs) con expiración configurable (default: 3600s) para visualización en el frontend.
*   **Selección Dinámica**: Factory pattern basado en `CORE_STORAGE_BACKEND`.

### Identidad Soberana vs. Centralizada
*   **On-Premise:** El `Auth-Service` local actúa como un IdP autocontenido.
*   **Cloud:** El `Auth-Service` central gestiona múltiples tenants con aislamiento estricto mediante `CompanyAccessDto`.

### Estrategia de Internacionalización (i18n)
*   **Backend Agnostic:** El backend es agnóstico al idioma del usuario. Envía claves de traducción (`translation_key`) en lugar de textos traducidos.
*   **Frontend Responsibility:** La resolución de textos se realiza en el cliente utilizando archivos locales (JSON) para maximizar el rendimiento y la escalabilidad.
*   **Fallback:** Si no existe traducción para la clave, se utiliza el campo `name` original de la base de datos.

### Paginación Eficiente Integrada (Total Records SSOT)
Cuando se requiere paginación en el backend, no se debe realizar un `all()` y luego contar en memoria. El patrón core es realizar **dos consultas concurrentes o secuenciales** utilizando el mismo objeto `select`:
1. **Count Query:** `count_stmt = select(func.count()).select_from(base_stmt.subquery())`.
2. **Data Query:** `stmt = base_stmt.limit(limit).offset(offset)`.

Este patrón garantiza que el `total_records` en el objeto `meta` de la respuesta sea preciso incluso con filtros dinámicos, manteniendo O(1) en el uso de memoria del servidor durante la transferencia de datos.
*   **Estrategia (Clean Architecture):** Los repositorios en la capa de Infraestructura en Python deben retornar siempre la tupla `(data, total_count)` para listados paginados.
*   **Performance (SQLAlchemy):** El conteo total de registros se resuelve mediante una consulta secundaria independiente y optimizada con `func.count()`. Esto permite mantener el valor `total_records` exacto en la metadata de la API sin penalizar el plan de ejecución y los bloqueos de la consulta principal de datos paginados.

---

## 6. Ecosistema de Eventos (Kiosk Mode)
Introducido en la Fase 42, este ecosistema está diseñado para operación en sitio (On-Premise) con conectividad limitada.

### 6.1 Event Universal Engine
Evolución de modelos rígidos a un motor dinámico con:
- **Quórum de N-Aprobadores**: Lógica configurable para validación de contenido por múltiples usuarios (ej. Novio y Novia en bodas).
- **Identity Lock**: Vinculación de votos a `device_id` de hardware físico para prevenir suplantaciones.

### 6.2 Componentes del Kiosk
- **kiosk_service**: Microservicio core para procesamiento de imágenes (recorte 3:2 DNP) y orquestación de impresión.
- **MinIO**: Almacenamiento S3 local de baja latencia para visualización instantánea de fotos pesadas.
- **Print Worker**: Daemon asíncrono que consume estados `PURCHASED` y libera el spooler de CUPS (Linux/Mini-PC).

---

## 7. Gobernanza de Directorios (Zero Root Pollution)
A partir de la Fase 43, se aplica una política estricta de limpieza en la raíz para mantener el estándar SSOT.

### Estructura de Carpetas Core:
- `/backend`: Microservicios FastAPI.
- `/frontend`: Aplicación principal Angular.
- `/eventKiosk`: Frontend especializado para eventos.
- `/scripts`: Única ubicación permitida para scripts operativos (`.ps1`, `.sh`, `.py`).
- `/logs`: Repositorio centralizado para reportes de auditoría y logs de sistema.
- `/docs`: Documentación técnica, specs de fase y logs de ingeniería.
- `/docker`: Definiciones de infraestructura y orquestación.

### Reglas de Desarrollo:
1. **No Pollute Root**: Prohibida la creación de archivos de texto o scripts en la raíz.
2. **Contexto Docker**: El build context siempre debe ser la carpeta del servicio o `/backend` para compartir la capa `/common`.
3. **Persistencia**: Toda mutación de datos debe heredar de `AuditBase` o `MultiTenantBase`.

---

## 8. Variables de Entorno Críticas

## 7. Flujos Arquitectónicos Core

### 7.1 Flujo de Login y Selección de Empresa (Multitenancy)
1. **Paso 1 (Autenticación - T1):** El usuario envía sus credenciales al `auth_service` (`/login`). El sistema valida y devuelve un `selection_token` temporal junto con la lista de empresas (inquilinos) a las que tiene acceso.
2. **Paso 2 (Selección - T2):** El usuario selecciona una empresa destino enviando el `selection_token` al endpoint `/select-company`.
3. **Paso 3 (JWT Final):** El `auth_service` emite el `access_token` JWT definitivo que inyecta el `company_id` seleccionado, los claims de RBAC (roles) y los módulos permitidos según la suscripción. Todos los repositorios usarán automáticamente este `company_id` interceptado para garantizar el aislamiento estricto (Zero Trust).

### 7.2 Emisión y Recepción de Transferencia Inter-Company
La transferencia se compone de dos eventos atómicos vinculados por un `TransferGroupGuid` único (o `TransactionPairId`) que ocurren en diferentes contextos de `tenant_id`.

#### Emisión (WMS -> Inventory)
1. **Command Origen (`CreateInterCompanyTransferCommand`):** Registra el **Egreso (Salida)** en la empresa origen.
2. **Validación:** El sistema verifica stock en la bodega origen y confirma que el usuario tiene acceso a ambos tenants (`CompanyAccessDto`) o posee privilegios de `God Mode`.
3. **Persistencia:** Genera el documento de "Salida por Transferencia" (Hereda de `MultiTenantBase` y `AuditBase`).
4. **Evento de Dominio (`TransferCreatedDomainEvent`):** Al persistir la salida, se dispara un proceso (vía Outbox Pattern) para notificar al tenant destino. El stock remanente queda en estado `InTransit`.

#### Recepción y Monitoreo (Inventory)
1. **Command Destino (`ReceiveInterCompanyTransferCommand`):** Registra el **Ingreso (Entrada)** en el contexto de la empresa destino.
2. **Simetría:** El documento de entrada referencia el `TransactionPairId` de origen.
3. **Consistencia:** Se implementan Sagas para asegurar que la actualización en la Empresa B sea consistente con la confirmación de la Empresa A.
4. **Estados:** `Pending` -> `InTransit` -> `Completed` / `Cancelled`.

#### Reglas de Oro de Transferencia
* **Vínculo Unívoco:** Ambas operaciones comparten el `TransferGroupGuid` para conciliación y auditoría.
* **Precios y Costos:** Se utiliza el objeto de valor `Money` según la configuración de la bodega destino.
* **Seguridad:** Validación de acceso obligatoria en ambas entidades involucradas.

### 7.3 Gobernanza de Precios y Auditoría (WMS)
Los precios en Interno Core no son propiedades mutables directas, sino registros de un ledger transaccional (Append-Only) para mantener la integridad financiera e histórica:

1. **Contexto de Operación (`price_type`)**:
   - `PURCHASE` (Costo): Valor pagado al proveedor. Usado como base para valuación (PEPS/UEPS).
   - `SALE` (Venta): Valor emitido en Ticket/Factura hacia un cliente externo.
   - `TRANSFER` (Traslado): Valor declarado para mover mercancía inter-company (vital para trazabilidad aduanal/fiscal).
   - *El servicio consumidor (Ej. Ventas o Compras) tiene la obligación de especificar el contexto de la transacción al consultar con WMS.*

2. **Inmutabilidad por Vigencia (Append-Only)**:
   - Los precios no se desactivan con un campo `is_active = False` al cambiar. 
   - El sistema invalida un precio anterior manipulando su **Fecha de Expiración (`end_date`)**.
   - **Regla de Auditoría**: Al insertar un nuevo precio para un `item_id` y `type`, el sistema:
     1. Localiza el precio actual con `end_date` en el futuro (o null).
     2. Modifica dicho `end_date` a `now() - 1 second`.
     3. Inserta el nuevo registro con `start_date = now()`, generando una nueva `version`.

3. **Estructura de Auditoría Exigida**:
   - El modelo hereda de `AuditBase`, forzando el registro de `version` y `change_reason` obligatorios ("Ajuste por inflación", "Contrato re-negociado") por cumplimiento de compliance interno.

## 8. Estándar de Configuración Empresarial

Para configurar correctamente una empresa dentro de Interno Core, es imperativo cumplir con los siguientes pilares de arquitectura multitenant y esquemas de datos:

### 8.1 Configuración de Identidad y Acceso
Cada empresa debe registrarse en el sistema central (`auth_service`) habilitando el flujo de autenticación:
*   **Company ID:** Identificador único (UUID) obligatorio, persistido en todas las tablas relacionales.
*   **CompanyStatus:** Estado global definido por enums (Activo, Inactivo, Demo).
*   **CompanyAccessDto:** Objeto de transferencia para la relación usuario-empresa. El login debe retornar el listado de empresas permitidas, delegando la carga de roles específicos al contexto de la organización seleccionada.

### 8.2 Estructura de Base de Datos (Aislamiento)
Garantía de aislamiento de datos bajo Clean Architecture:
*   **Herencia Base:** Toda tabla principal debe heredar de `MultiTenantBase`.
*   **Header de Contexto:** Las peticiones API deben incluir `X-Company-ID` para el filtrado de filas (Row-Level Security lógico).
*   **Esquema de Auditoría:** Implementación obligatoria de `AuditBase` para asegurar que cada acción dentro de la empresa sea rastreable.

### 8.3 Parámetros de Almacén y Precios (WMS/ERP)
Configuración operativa a nivel de empresa:
*   **Relación Empresa-Almacén:** Asociación explícita de `warehouses` a la identidad de la empresa.
*   **Listas de Precios:** Parametrización granular por empresa (`company_id`) y almacén (`warehouse_id`), permitiendo diferenciación de costos logísticos.

### 8.4 Entorno de Ejecución
Configuración agnóstica del despliegue:
*   **Variables de Entorno:** El sistema debe operar indistintamente como SaaS Multi-tenant (AWS) o On-Premise Single-tenant mediante flags de configuración (ej. `MULTI_TENANT_MODE`), manteniendo un único código base.

## 9. Políticas de Acceso y Suscripción (Governance)

Especificaciones fundamentales que rigen la lógica de acceso y suscripción del sistema:

### 9.1 Arquitectura Multi-inquilino (Multitenancy)
El sistema está diseñado para manejar múltiples empresas de forma aislada. La lógica de suscripción debe respetar esta separación, asegurando que un usuario pueda tener acceso a diferentes empresas (`CompanyAccessDto`) tras el login.

### 9.2 Identidad y Acceso
Un usuario puede tener un correo único global o un usuario específico por empresa. El proceso de login debe validar a qué listado de empresas tiene acceso el usuario para cargar los roles correspondientes.

### 9.3 Mandato de company_id
Para la integridad de los datos de suscripción y operación, el `company_id` es obligatorio en la mayoría de las tablas de la base de datos (Integridad Referencial Multitenant).

### 9.4 Compatibilidad de Entorno
Las suscripciones y el funcionamiento general del sistema deben operar de manera idéntica tanto en entornos On-Premise como en AWS.

### 9.5 Estructura de Backend (CQRS)
El proyecto utiliza Clean Architecture con CQRS, lo que implica que las acciones relacionadas con suscripciones (crear, actualizar, cancelar) deben manejarse a través de comandos y consultas específicos en el dominio.

## 10. Especificaciones de la Infraestructura de Suscripción

El sistema opera bajo un modelo de SaaS con Aislamiento Estricto, donde la suscripción no es solo un registro de pago, sino la "llave de paso" de la infraestructura.

### 10.1 Especificaciones Técnicas
*   **Vinculación:** Basada en el `company_id`. La suscripción pertenece a la Entidad Empresa, no al usuario individual.
*   **Validación de Acceso:** El middleware de seguridad verifica el estado de la suscripción en cada handshake (T1/T2).
*   **Motor de Webhooks:** Implementado en el `subscription_service` (puerto 8002) para procesar eventos de Stripe en tiempo real.
*   **Ciclo de Vida:** Estados soportados: `TRIAL`, `ACTIVE`, `PAST_DUE`, `CANCELED`.
*   **Persistencia:** Registro histórico en `AuditSubscriptionLog` (Timeline Forense) para auditorías industriales.

### 10.2 Reglas de Negocio (Stripe Integration)
*   **Activación Automática:** Al recibir el evento `checkout.session.completed`, el servicio busca el `client_reference_id` (mapeo a `company_id`) y cambia el estado a `ACTIVE` automáticamente.
*   **Sincronización de Periodos:** Se extrae el `current_period_end` de Stripe para actualizar la fecha de expiración local, permitiendo funcionamiento Offline/On-premise sin consultas externas constantes.
*   **Resiliencia de Triggers:** El sistema ignora triggers de prueba sin metadatos válidos (200 OK ignored) para mantener la salud del webhook.

### 10.3 Notificaciones de Suscripción
*   **Branding Dinámico:** Uso de `TemplateService` con Jinja2 y logo `InternoCoreSVGBlack.svg` (Base64) para evitar bloqueos.
*   **Confirmación Real:** Disparo inmediato de correo al admin del tenant tras validación del pago.

### 10.4 Protocolo de Degradación por Fallo de Pago (Grace Period)
En un entorno industrial, un pago fallido no puede detener la operación. El sistema implementa una degradación controlada del servicio ante el evento `invoice.payment_failed` de Stripe.

#### Flujo del Webhook (`invoice.payment_failed`)
1.  **Recepción del Evento:** El `subscription_service` recibe la notificación de Stripe.
2.  **Actualización de Estado:** El estado de la suscripción del `company_id` correspondiente se cambia a `PAST_DUE`.
3.  **Notificación de Urgencia:** Se dispara un correo electrónico vía Resend al administrador del tenant, informando sobre el fallo del método de pago.

#### Niveles de Bloqueo Controlado

| Nivel de Bloqueo | Estado | Acción del Sistema |
| :--- | :--- | :--- |
| **Aviso (Día 1-3)** | `PAST_DUE` | El sistema permite acceso total, pero muestra un Banner de Alerta persistente en el Frontend. |
| **Restricción (Día 4-7)** | `PAST_DUE` | Bloqueo de escritura en módulos no críticos (Configuración, Usuarios). La operación core (Inventario, Producción) sigue en modo lectura/escritura. |
| **Suspensión (Día 7+)** | `UNPAID` / `CANCELED` | Bloqueo total de la API para ese `company_id`. Redirección forzada al Portal de Pago de Stripe. |

## 11. Protocolo God Mode (Super-Admin)

El God Mode es un protocolo de super-administración transaccional y volátil diseñado para garantizar la continuidad operativa ante incidentes críticos. No es un rol de usuario, sino un estado de ejecución privilegiado activado por infraestructura.

### 11.1 Seguridad y Autenticación (Fail-Closed)
El sistema está diseñado para que, en ausencia de configuración, el acceso administrativo sea físicamente imposible.
*   **Llave Maestra:** Credencial única `CORE_ADMIN_MASTER_KEY`. Si no se detecta en el entorno, todas las rutas administrativas se bloquean físicamente (**Fail-Closed**).
*   **Principio de Volatilidad:** La credencial de acceso vive únicamente en la memoria del sistema y nunca se persiste en bases de datos de clientes ni en el almacenamiento local del navegador (Angular Signals en `AdminAuthService`).
*   **Validación de Header:** Las peticiones administrativas requieren el header `x-admin-master-key`, validado directamente por `InternoSettings`.

### 11.2 Capacidades de Intervención (Backend)
Permite bypassar las restricciones normales de Multitenancy y suscripción para realizar "rescates técnicos".
*   **Rescate de Tenants (Subscription):** Permite el override manual de `grace_period_until`. El tenant permanece en `PAST_DUE` para garantizar que el sistema intente el cobro automático al expirar la prórroga (**Prórroga no es Regalo**).
*   **Gestión de Identidad (Auth):** Implementa `force-assign` para vinculación directa usuario-empresa saltando invitaciones, y elevación de roles bajo bypass de seguridad.
*   **Asignación Forzada:** Vínculo manual usuario-empresa (`force-assign`) y elevación directa de roles saltando validaciones de invitación.
*   **Bypass de Repositorio:** El `BaseRepository` cuenta con un flag `bypass_tenant` (protegido por defecto) que permite ignorar el filtro de `company_id` exclusivamente durante la ejecución de tareas administrativas.

### 11.3 Auditoría y Transparencia (Anti-Stealth)
Para evitar acciones invisibles, cada intervención queda registrada bajo estándar forense:
*   **Log Estándar:** `[GOD_MODE] | Action: {action} | Target: {entity_id} | Company: {company_id} | TX: {trace_id}`.
*   **Trazabilidad AuditBase:** `UserCompanyRole` hereda de `AuditBase` para registrar quién (`created_by`) realizó la intervención.
*   **Visibilidad para el Cliente:** El sistema genera un log específico que la empresa afectada puede consultar, detallando motivo y duración.
*   **Aislamiento de Documentos:** Se permite auditar documentos pero cada consulta queda grabada en el log del tenant.

## 12. Gestión de Usuarios y Roles (RBAC Multitenant)

Para cumplir con los estándares de Interno Core, la gestión de usuarios y roles está desacoplada pero integrada mediante el header de tenant.

### 12.1 Modelo de Datos (Relación)
*   **User:** Identidad global (email, password hash).
*   **Role:** Definición de perfil base (ej. Admin, Operador).
*   **UserCompanyRole:** Tabla pivot que rompe la relación N:N e incluye el `company_id`. Contiene `scopes` (JSONB) para personalizar permisos sin alterar el rol base.

### 12.2 Flujos Funcionales
*   **Invitación (Onboarding):** Generación de códigos únicos vinculados a un `company_id` y `role_id`.
*   **Cambio de Contexto:** El usuario alterna empresas y el backend emite un nuevo `access_token` con el `company_id` y scopes específicos de esa relación.