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
* **Output (`ApiResponse`):** `access_token` (8 horas) con claims de `company_id` y `permissions`.

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