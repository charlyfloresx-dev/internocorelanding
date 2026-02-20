# LOG

### January 19, 2026

**Task**: Finalized `seed_data.py` business logic and updated `UserCompanyRole` foreign key.

**Details**:
*   Corrected `UserCompanyRole` model in `backend/auth_service/app/models/user_company_role.py` to use `role_id` (Integer, ForeignKey('roles.id')) as part of the primary key.
*   Updated `backend/auth_service/scripts/seed_data.py` to:
    *   Align `Company` creation (removed `is_active`).
    *   Create 'Aperture Science' and 'Black Mesa' companies.
    *   Associate user 'charly@internocore.app' with 'Aperture Science' with `is_new=False` (direct Dashboard access).
    *   Associate user 'charly@internocore.app' with 'Black Mesa' with `is_new=True` (activates Onboarding Wizard).
    *   Adjusted `sys.path.insert` for correct module imports within the Docker environment.
*   Confirmed that the backend's `/login` endpoint (via `SelectionTokenResponse`) calculates and delivers the `isNew` flag based on the `UserCompanyRole` relationships, adhering to Directive #002.

**Pending**: User to manually rebuild Docker images, reset database, run migrations, and execute the updated seed script.

---

### January 19, 2026 - Seed Script Correction (Company Instantiation)

**Task**: Correct `seed_data.py` to remove `is_active` and `company_code` from all `Company` instantiations.

**Details**:
*   Rewrote `backend/auth_service/scripts/seed_data.py` to ensure `Company` objects are instantiated *only* with the `name` argument and `logo` where applicable.
*   Specifically confirmed `internocore_company = Company(name="InternoCore Systems")` and similar for 'Aperture Science' and 'Black Mesa'.
*   This correction addresses the `TypeError: 'is_active'` error.

---

### January 19, 2026 - Dockerfile and Requirements Cleanup (PostgreSQL Focus)

**Task**: Review `requirements.txt` and `Dockerfile.prod` for MySQL/MariaDB dependencies and clean up to focus on PostgreSQL.

**Details**:
*   Reviewed `backend/auth_service/requirements.txt`: No MySQL/MariaDB specific packages were found. `psycopg2-binary` and `asyncpg` were correctly present. No changes needed.
*   Reviewed `backend/auth_service/Dockerfile.prod`: No MySQL/MariaDB specific installation commands (e.g., `default-libmysqlclient-dev`) were found. `libpq-dev` was correctly included for PostgreSQL client libraries. No changes needed.
*   Both files are already clean and optimized for PostgreSQL.

---

### Initial Checklist Import

# 🚀 Checklist de Desarrollo - InternoCore v2.1

## 1. Fase: Infraestructura y Modelos (Punto Actual 📍)
- [ ] 1.1 Configurar `common/models.py` con UUID y Relación N:M.
- [ ] 1.2 Crear Script de Seed (`seed.py`) con usuario `charly@internocore.app`.
- [ ] 1.3 Levantar Docker y ejecutar migraciones.

<h2> 2. Fase: Middleware y Estructura Global </h2>
- [x] 2.1 Implementar `InternoCoreGlobalMiddleware` en `main.py` y `common/middleware.py`.
- [x] 2.2 Validar formato JSON `data/meta` y `X-Transaction-ID` en un endpoint de prueba.

<h2> 3. Fase: Lógica de Autenticación Dual </h2>
- [x] 3.1 Endpoint `POST /auth/login` (Selection Token - 5 min).
- [x] 3.2 Endpoint `GET /auth/my-companies` (Lista de empresas vinculadas con `isNew` y `logo`).
- [x] 3.3 Endpoint `POST /auth/select-company` (Access Token Contextual - 8 hrs).

<h2> 4. Fase: Integración con Frontend (IA Studio Alignment) </h2>
- [ ] 4.1 Alinear el Interceptor de Angular/Typescript con el JSON de la API.
- [ ] 4.2 Probar flujo completo: Login -> Selección -> Dashboard.

---

<h2> ✅ Directivas InternoCore Implementadas </h2>

Las siguientes directivas han sido completamente implementadas y verificadas en el Auth-Service:

<h3> DIRECTIVA INTERNO-CORE #001: CONTRATO DE AUTENTICACIÓN Y TENANCY </h3>
- [x] **Propiedad de Identidad**: Auth-Service es dueño de `Users`, relación N:N con `Companies` a través de `UserCompanyRole`.
- [x] **Esquema de Respuesta Único**: Todas las respuestas siguen el formato `{ "status": "success/error", "data": {...}, "message": "...", "meta": {...} }` utilizando `StandardResponse`.
- [x] **Flujo Stateless en Dos Tiempos**:
    - [x] **T1 (Auth)**: `POST /api/v1/auth/login` emite un `selection_token` (JWT temporal) con `user_id` y array de `tenants` (empresas asociadas con `isNew`, `logo`, `name`).
    - [x] **T2 (Context)**: `POST /api/v1/auth/select-company` devuelve el JWT definitivo con `company_id` y `roles` incrustados.
- [x] **Flag `isNew`**: Calculado dinámicamente en `POST /api/v1/auth/login` y agregado al `SelectionTokenResponse`.
- [x] **Logging**: Se agregó logging para movimientos recientes, incluyendo el flag `isNew` y detalles relevantes.
- [x] **Middleware Global**: `InternoCoreGlobalMiddleware` implementado en `backend/common/middleware.py` para sincronizar `transaction_id` (`X-Transaction-ID`) y envolver respuestas/excepciones en `StandardResponse`.

<h3> DIRECTIVA #002: SINCRONIZACIÓN DE DISCOVERY-LOGIN </h3>
- [x] **Backend**: El endpoint `/login` solo emite el `discovery_token` (nuestro `selection_token`), no permisos finales.
- [x] **Payload de Discovery**: El objeto `tenants` (`companies`) dentro de `data` es el resultado de un JOIN entre `users`, `user_tenants` (nuestro `UserCompanyRole`) y `companies`.
- [x] **Frontend**: La lógica backend soporta que el frontend no acceda a rutas protegidas sin el JWT final (emitido por `/select-company`).

---

<h3> January 19, 2026 - Dockerfile, requirements.txt, and alembic.ini cleanup </h3>

**Task**: Apply changes to `alembic.ini`, `requirements.txt`, and `Dockerfile` as requested by the user.

**Details**:
*   **User Request**:
    *   `alembic.ini`: Change `script_location = auth_service/alembic` to `script_location = alembic`.
    *   `requirements.txt`: Remove `mysqlclient` and leave only `asyncpg` and `sqlalchemy`.
    *   `Dockerfile` (dev): Remove the installation of `default-libmysqlclient-dev`.

*   **Execution Log**:
    *   **Locating Files**: Confirmed `alembic.ini`, `requirements.txt`, and `Dockerfile` are in `backend/auth_service`.

    *   **1. Modifying `alembic.ini`**:
        *   Read `backend/auth_service/alembic.ini`.
        *   **Observation**: The `script_location` was already set to `alembic`. No changes were applied.

    *   **2. Modifying `requirements.txt`**:
        *   Read `backend/auth_service/requirements.txt`.
        *   **Action**: Replaced the entire content with:
            ```
            sqlalchemy[asyncio]==2.0.30
            asyncpg==0.29.0
            ```
        *   **Result**: `requirements.txt` now contains only the specified packages.

    *   **3. Modifying `Dockerfile` (dev)**:
        *   Read `backend/auth_service/Dockerfile`.
        *   **Observation**: The string `default-libmysqlclient-dev` was not found in the file. No changes were applied.

**Summary**: All requested modifications were addressed. `alembic.ini` and `Dockerfile` were already in the desired state or did not contain the specified string, thus no actual changes were made to them. `requirements.txt` was updated as instructed.

---

<h3> Estado actual del Proyecto (January 19, 2026) </h3>

**Estado Técnico**: El InternoCore Auth-Service y la base de datos Postgres ya están operativos y validados mediante Docker Compose (recreados exitosamente).

**Conexión y Base de Datos**: Se ha verificado la conexión exitosa a la DB y la creación automática de las tablas del modelo multi-empresa (users, companies, roles, permissions, role_permissions, user_company_roles).

**Configuración Docker**: Se confirma que el docker-compose.yml actual es funcional y no requiere modificaciones adicionales por ahora.

**Próximo Hito**: Iniciamos la fase de despliegue en AWS. El usuario proporcionará imágenes de configuración de la infraestructura para su análisis y asistencia en la implementación.

---

<h3> January 19, 2026 - Creación del Manual de Recuperación ante Desastres </h3>

**Task**: Crear un "Manual de Recuperación ante Desastres" para el microservicio de Auth de NexoSuite.

**Details**:
*   El manual `DR_Manual_Auth_Microservice.md` fue creado en el directorio `docs/`.
*   El documento incluye secciones sobre arquitectura, variables de entorno clave, pasos detallados para la reconstrucción de infraestructura (AWS RDS y Secrets Manager) usando AWS CLI, pruebas de conectividad (Telnet/PowerShell, script Python para secretos) y políticas de seguridad post-recuperación.
*   Se proporcionaron comandos AWS CLI de ejemplo y un script Python para facilitar los pasos de recuperación.

---

<h3> January 19, 2026 - Creación de HOWTO.md (Guía de Recuperación Técnica) </h3>

**Task**: Generar el archivo HOWTO.md final para el microservicio de Auth de NexoSuite, actuando como Senior DevOps Engineer y Technical Writer.

**Details**:
*   El archivo `HOWTO.md` fue creado en el directorio `docs/`.
*   El documento proporciona una guía técnica estructurada para la recuperación del sistema en caso de desastre.
*   Incluye secciones sobre arquitectura (FastAPI, Docker, AWS RDS, Secrets Manager), configuración de AWS (detalles de RDS y Secrets Manager, comandos críticos de recuperación con AWS CLI), un checklist de pruebas de fuego (DBeaver, AWS CLI, Health Check API, Persistencia en la nube) y un plan de contingencia.
*   Se utilizaron tablas para credenciales y bloques de código para los comandos de AWS CLI, manteniendo un formato Markdown limpio y técnico.

---

<h3> January 19, 2026 - Contexto de Sincronización del Proyecto InternoCore </h3>

**Contexto General**:
*   **Backend**: Microservicios FastAPI en `/backend`. Contexto de build: `/backend`. Uso de `/common` para modelos y middlewares. Docker Config: `PYTHONPATH` incluye `/app` y la subcarpeta del servicio (ej. `/app/auth_service`). `WORKDIR` es la carpeta del servicio. Estado: Backend validado localmente, tablas de base de datos (`user_company_roles`, etc.) creadas y Uvicorn corriendo.
*   **Frontend**: Aplicación Angular/TS. Estrategia AWS: Despliegue estático en Amazon S3 servido a través de Amazon CloudFront (CDN). Configuración Crítica: Manejo de rutas SPA mediante redirección de errores 403/404 al `index.html` en CloudFront. CI/CD: Se planea automatizar mediante GitHub Actions o AWS Amplify para sincronizar el build (`dist/`) con S3.

**Instrucciones Clave**:
*   Recordar la estructura de multitenancy: login por correo/usuario por empresa y carga dinámica de roles tras el login.
*   El contexto de build para Docker siempre es `/backend`.

**Tareas Pendientes Inmediatas**:
*   Consolidar documentación de logs y checklists.
*   Crear repositorio en ECR para el backend y subir la primera imagen.
*   Configurar el bucket de S3 y la distribución de CloudFront para el frontend.

January 27, 2026 - Evolución Estratégica: Ecosistema CFX y Modo Demo
Task: Integrar la filosofía de "Claridad Operativa" de CFX y preparar el entorno para pruebas de usuario.

Details:

Pivot de Marca: Se establece que Interno Core es el brazo tecnológico del ecosistema CFX, enfocado en visibilidad operativa y adopción en piso.

Modo Demo: Se acuerda mantener una versión de prueba de todos los módulos disponible para el usuario, facilitando presentaciones y validaciones rápidas.

Principios CFX: Se integran los 5 pilares (El proceso manda, adopción del operador, validación en piso, etc.) como guías de diseño para futuros módulos.

January 28, 2026 - Diseño de Autenticación Operativa y Checklist de Fase 2
Task: Definir el flujo de acceso para personal de piso (RFID/Badge) y actualizar el roadmap técnico.

Details:

Login Operativo: Se define una nueva vía de acceso mediante escaneo de credencial/RFID para eliminar el uso de teclado en estaciones de trabajo.

Actualización de Modelos: Se añade al checklist la creación del campo badge_id en la entidad User dentro de la librería common.

Selector de Empresa: Se confirma que, tras el escaneo o login, si un usuario tiene múltiples accesos ("usuario por empresa"), el sistema presentará un selector para cargar el contexto operativo correcto.

Arquitectura de Microservicios: Se validan las responsabilidades de los nuevos servicios:

Warehouse: Incluye trazabilidad y cumplimiento de Anexo 24/31.

MES: Gestión de producción, tiempos muertos y Pull System.

Quality: Análisis de defectos con enfoque en impacto monetario y Pareto.

Billing: Integración con Stripe para el modelo SaaS.

🚀 Checklist Actualizado - InternoCore / CFX v2.4
1. Fase: Infraestructura y Modelos (Finalizando 🏁)
[x] 1.1 Configurar common/models.py con UUID y Relación N:M.

[x] 1.2 Crear Script de Seed (seed.py) con usuario charly@internocore.app.

[x] 1.3 Levantar Docker y ejecutar migraciones exitosamente.

[ ] 1.4 Configuración AWS (Mañana): Despliegue de microservicios en ECS/App Runner y DB en RDS.

2. Fase: Middleware y Estructura Global
[x] 2.1 Implementar InternoCoreGlobalMiddleware para trazabilidad de transacciones.

[x] 2.2 Sincronización de PYTHONPATH y contexto de build en /backend.

3. Fase: Autenticación y Multi-tenancy
[x] 3.1 Endpoint POST /auth/login (Selection Token).

[x] 3.2 Endpoint GET /auth/my-companies (Retorno de CompanyAccessDto).

[x] 3.3 Soporte para múltiples identidades (correo/teléfono) por empresa.

[ ] 3.4 Acceso Operativo (Fase 2): Implementar login vía badge_id (RFID).

4. Fase: Módulos Core CFX (Roadmap)
[ ] 4.1 Warehouse: Lógica de inventarios y cumplimiento legal (Anexo 24).

[ ] 4.2 MES: Registro de producción y eficiencia en tiempo real.

[ ] 4.3 Billing: Sistema de suscripciones SaaS con Stripe.

Estado actual del Proyecto (January 28, 2026)
Estado Estratégico: El proyecto ha evolucionado de un software aislado a un componente clave de la consultoría CFX. La interfaz de usuario ya refleja las opciones de Iniciar Sesión, Unirse y Crear Empresa.

Estado Técnico: Backend validado localmente con Bcrypt 4.0.1 y aiosqlite para tests. La estructura de common ya es un espejo funcional de la arquitectura .NET original.

Próximo Hito: Configuración de infraestructura en AWS para permitir el acceso a la API desde dispositivos externos y aplicaciones móviles.

### January 29, 2026 - Implementación Frontend Auth Handshake

**Task**: Implementación de Fase 1 y 2 del flujo de autenticación en Frontend.

**Details**:
*   **AuthService**: Se implementó el método `selectCompany` cumpliendo el contrato v1.1:
    *   Envío de `company_id` en Body y `selection_token` en Header `X-Selection-Token`.
    *   Persistencia de `access_token` y `company_id` en LocalStorage tras respuesta exitosa.
*   **TenantSelectionComponent**: Implementada lógica de redirección post-selección basada en el flag `is_new` (Wizard vs Dashboard).

### January 29, 2026 - Implementación Interceptor Multitenant

**Task**: Configuración de la capa de red para inyección automática de contexto.

**Details**:
*   **ApiInterceptor**: Creado interceptor funcional (`HttpInterceptorFn`) que inyecta `Authorization` y `X-Company-ID` leyendo de `localStorage`. Se excluye explícitamente la ruta `/auth/login`.
*   **AppConfig**: Registrado el interceptor mediante `provideHttpClient(withInterceptors([...]))` en `app.config.ts`.

### January 29, 2026 - Despliegue de Código Frontend (Fase 1 & 2)

**Task**: Sobrescritura de archivos core del Frontend para habilitar autenticación real.

**Details**:
*   **AuthService**: Implementado `selectCompany` con headers `X-Selection-Token` y persistencia en `localStorage`.
*   **ApiInterceptor**: Implementada inyección de `X-Company-ID` para peticiones de negocio.
*   **TenantSelection**: Implementada redirección condicional (`isNew` -> `/setup-wizard`).

### January 29, 2026 - Implementación de Protección de Rutas (Fase 3)

**Task**: Asegurar rutas protegidas para prevenir acceso no autorizado.

**Details**:
*   **AuthGuard**: Creado guard funcional (`CanActivateFn`) en `auth.guard.ts` que verifica la existencia de `interno_auth_token` y `interno_auth_company_id` en `localStorage`.
*   **AppRoutes**: Aplicado `authGuard` a las rutas `/dashboard` y `/setup-wizard` en `app.routes.ts` para redirigir a `/login` si no hay sesión activa.

### January 29, 2026 - Implementación de Filtrado por Roles (Fase 4)

**Task**: Implementación de RBAC en la interfaz de usuario (Sidebar).

**Details**:
*   **SidebarComponent**: Implementada lógica de decodificación de JWT (sin librerías externas) para extraer roles del payload.
*   **Sidebar Template**: Aplicadas directivas `*ngIf` para segregar menús:
    *   `Inventarios`: Visible para `admin` y `operator`.
    *   `Configuración/Ajustes`: Visible exclusivamente para `admin`.

### January 29, 2026 - Corrección de Redirección en Selección de Tenant

**Task**: Solución de discrepancia en formato de flag `isNew` y persistencia de contexto.

**Details**:
*   **TenantSelectionComponent**: 
    *   Actualizada interfaz `Tenant` para soportar `isNew` (camelCase) y `is_new` (snake_case).
    *   Añadida persistencia explícita de `interno_auth_company_id` en `localStorage` antes de la navegación.
    *   Implementada lógica robusta para evaluar el flag de nueva empresa (`isNew || is_new`).

### January 29, 2026 - Actualización de Dependencias

**Task**: Corrección de error de importación de JWT.

**Details**:
*   **requirements.txt**: Se añadió `PyJWT==2.8.0` a las dependencias del `auth_service` para soportar la generación y validación de tokens.

### January 29, 2026 - Sincronización de Modelos Frontend-Backend

**Task**: Ajuste de interfaces y lógica RBAC para coincidir con el JSON real del Backend v1.1.

**Details**:
*   **TenantSelectionComponent**: Actualizada interfaz `Tenant` para incluir `company_name`, `role_names` y `is_new` (snake_case). Lógica de redirección simplificada para usar `is_new`.
*   **SidebarComponent**: Ajustada la decodificación del token para priorizar la lectura de `role_names` para la asignación de permisos de administrador/operador.

### January 29, 2026 - Sincronización de Dominio Core (Backend Common)

**Task**: Definición y mapeo de entidades core y enums en `backend/common/domain`.

**Details**:
*   **Enums**: Actualizados `WorkOrderStatus` (incluyendo estados MES: PARTIAL, QUALITY_CHECK), `CompanyStatus` y `UserStatus` en `backend/common/domain/enums.py`.
*   **Entities**: Confirmada la estructura de `Product`, `Warehouse` y `WorkOrder` en `backend/common/domain/entities.py` con herencia `MultiTenantBase`.
*   **Value Objects**: Verificada la implementación de `Address` y `Money` en `backend/common/domain/value_objects.py`.
*   **Base**: Verificada la definición de `BaseEntity`, `AuditBase` y `MultiTenantBase` en `backend/common/domain/base.py`.
*   **Confirmación**: Todos los archivos de dominio residen estrictamente en `backend/common/domain/`.