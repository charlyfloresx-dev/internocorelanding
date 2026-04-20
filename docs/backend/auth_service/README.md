markdown
# 🔐 Auth Service (Identity & Tenancy)

Este servicio es el núcleo de seguridad y gestión de identidad de **InternoCore**. Implementa un modelo de aislamiento de datos estricto basado en el ADN del proyecto.

---

## 🔄 Flujo de Autenticación de Dos Tiempos (Handshake)

### Fase 1: Discovery (Identidad)
* **Endpoint:** `POST /api/v1/auth/login`
* **Output (`ApiResponse`):** `selection_token` y array de `companies`.
* **Flag `is_new`:** Ubicado dentro de cada objeto en `companies`. Determina la necesidad de Onboarding.

### Fase 2: Contextualización (Empresa)
* **Endpoint:** `POST /api/v1/auth/select-company`
* **Output (`ApiResponse`):** `access_token` enriquecido con `modules`, `status` y `readonly`.

### Modelo de Datos Empresarial
Para cumplir con el estándar de configuración:
*   **CompanyStatus:** Enum global (Activo, Inactivo, Demo).
*   **CompanyAccessDto:** DTO utilizado en la fase de Login para entregar el listado de empresas disponibles.
*   **Flexibilidad de Identidad:** Soporte para correo único global o usuarios aislados por empresa.
*   **Persistencia:** Todo registro de empresa debe generar un `company_id` único y persistente.

---

## 👤 Gestión de Usuarios y Roles (RBAC)

El sistema utiliza un control de acceso basado en roles (RBAC) granular por empresa.

### Especificaciones Técnicas (CQRS)

| Operación | Tipo | Descripción |
| :--- | :--- | :--- |
| `CreateUserCommand` | Comando | Crea la identidad global del usuario. |
| `AssignRoleCommand` | Comando | Vincula usuario a empresa con rol y scopes específicos. |
| `GetUserPermissionsQuery` | Consulta | Retorna permisos efectivos del usuario para el `company_id` actual. |
| `UpdateUserScopesCommand` | Comando | Agrega/quita permisos en `UserCompanyRole` sin alterar el Rol base. |

### Estructura del JWT (Claims)
El token generado debe incluir:
*   `sub`: UUID del usuario.
*   `company_id`: UUID de la empresa activa.
*   `role_names`: Lista de nombres de roles (ej. `['admin']`).
*   `scopes`: Lista plana de permisos (ej. `['inventory:read', 'catalog:admin']`).

### Lógica de Middleware
1.  **Extracción:** Obtiene `company_id` del JWT o header `X-Company-Id`.
2.  **Validación:** Verifica que el par `(user_id, company_id)` existe en `user_company_roles`.
3.  **Inyección:** Setea `UserContext` para filtrado automático en repositorios.

## 🛰️ Integración con Subscription Service
El `auth_service` actúa como cliente del `subscription_service` (Puerto 8002) durante la Fase 2 del Handshake.

### Resiliencia y Fallback
Para garantizar la continuidad operativa, el sistema implementa un modo de **Fallo Seguro**:
- **Si el servicio de suscripciones no responde:** Se otorga acceso restringido con los módulos `['auth_core', 'inventory_core']` y la bandera `readonly: true`.
- **Trazabilidad:** Cada handshake genera un `correlation_id` único que se viaja en el JWT y vincula los logs de ambos servicios.

### Reglas de Negocio en Token Final
- **Status EXPIRED:** Deniega la emisión del token (402 Payment Required).
- **Status PAST_DUE:** Permite el acceso pero fuerza `readonly: true` (Modo Lectura por periodo de gracia).

---

## 🛡️ Seguridad y Multi-Tenancy

### Cabecera Obligatoria: `X-Company-ID`
El middleware de seguridad valida que el ID en la cabecera coincida con el del `access_token`. Cualquier discrepancia resulta en `403 Forbidden`.



---

## 📅 Roadmap de Fases (Estatus del Proyecto)

### ✅ FASES COMPLETADAS
1. **Core Auth & Handshake:** Backend listo para emitir tokens de dos niveles.
2. **Standard Response:** Implementación del middleware `InternoCoreGlobalMiddleware` para el formato unificado JSON.
3. **Data Mirroring:** Sincronización de entidades `BaseEntity` y `MultiTenantBase` con el ADN .NET.

### ⏳ FASES PENDIENTES (Prioridad Alta)

#### 1. Control de Flujo UI (Frontend Guard)
* **Estado:** Pendiente.
* **Objetivo:** Implementar la guardia de navegación que evalúe el flag `is_new`. Si es `true`, debe bloquear el acceso al `/dashboard` y forzar la redirección a `/onboarding`.
* **Regla:** El usuario no puede salir del onboarding hasta que el backend actualice su estatus de "new" a "active".

#### 2. Autorización por Permisos (RBAC)
* **Estado:** Pendiente.
* **Objetivo:** Configurar el `NavigationService` en Angular para que consuma el array `permissions` del `access_token`. 
* **Regla:** Los módulos (WMS, MES, QMS) deben ocultarse dinámicamente si el permiso correspondiente no está presente en el token.

#### 3. Despliegue e Infraestructura AWS
* **Estado:** Programado (Mañana).
* **Objetivo:**
    - Configurar **ECR** para las imágenes de Docker del `auth-service`.
    - Implementar **S3 + CloudFront** para el hosting del frontend.
    - Asegurar que el sistema funcione bajo la misma lógica tanto **On-Premise** como en **AWS VPC**.



---

## 🔍 Guía para el Agente (Auditoría)
Al trabajar en fases pendientes, el agente debe verificar:
1. ¿El cambio respeta el aislamiento de datos (Multi-tenancy)?
2. ¿Se mantiene el formato de respuesta `ApiResponse`?
3. ¿Las nuevas rutas de Angular están protegidas por el `AuthGuard`?

## 🛡️ Auditoría de Integridad
Para verificar la salud de los datos y el cumplimiento de normas multi-tenant:
`docker compose exec auth-service python -m app.scripts.integrity_scan`

### God Mode (Super-Admin)
Capacidades de intervención mediante `CORE_ADMIN_MASTER_KEY` para soporte crítico:
*   **Force Assign:** Vinculación directa de usuarios a empresas sin flujo de invitación.
*   **Role Elevation:** Modificación de permisos en `user_company_roles` saltando restricciones de tenant.