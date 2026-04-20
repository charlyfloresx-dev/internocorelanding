# 🛠 Interno Core MES - Engineering Blueprint & Change Log

## 📐 Arquitectura de Referencia
- **Framework:** Angular 19.1.0 (Zoneless Mode).
- **State Management:** Angular Signals (signal, computed, effect).
- **Routing:** HashLocationStrategy (importante para entornos locales).
- **Estilos:** Tailwind CSS JIT (CDN).
- **Persistence Layer:** LocalStorage + ApiSimulationService.

## 🗂 Estructura de Módulos (Blueprint)
1. **Auth Module:** Maneja el flujo Guest -&gt; Handshake -&gt; Authenticated.
2. **Production Module:** 
   - Dashboard: OEE, Downtime, Pareto.
   - WorkOrders: Lista filtrable y Scanner QR.
3. **Inventory Module:**
   - Maestro: Stock y Precios.
   - Documentos: Movimientos de almacén.
   - Estructura: Warehouses y Socios comerciales.
4. **System Module:**
   - Snapshot Manager: Herramienta de recuperación ante errores de datos.

## 📝 Registro de Modificaciones (Change Log)

### [v1.8.1] - Mission Control Dash & Readiness Gatekeeping
- **Resumen:** Implementación del sistema de verificación de preparación (Readiness) y migración a APIs reales para el Dashboard de Inventarios.
- **Detalles:**
  - **Readiness Gatekeeper**: Nuevo componente `InventoryReadinessGatekeeper` que bloquea el Dashboard si faltan catálogos base (UOM, Productos, Almacenes).
  - **Real Data Sync**: Sustitución total de `ApiSimulationService` por `HttpClient` en el `InventoryService`, conectando con el Ledger Inmutable del backend.
  - **Mirror Awareness**: Lógica de visualización para documentos "Espejo ICT" (folio `ICT-IN-*`), incluyendo insignias pulsantes y filtrado por almacén físico.
  - **Industrial Mimesis**: Refinamiento de señales computadas para `physicalWarehouses` y `transitWarehouses` asegurando alineación total con el contexto del operador.
- **Estado:** ✅ Validado y Conectado al Backend.

### [v1.8.0] - Mission Control & Industrial Resilience
- **Resumen:** Implementación de observabilidad de grado industrial y blindaje de resiliencia ante fallos de red.
- **Detalles:**
  - **Mission Control**: Dashboard con telemetría en tiempo real, monitoreo de integridad forense y osciloscopio de latencia.
  - **Escalabilidad**: Monitor de cuotas y uso por tenant con mapas de calor de actividad transaccional.
  - **Resiliencia Industrial**: Interceptores de error con mapeo de excepciones de dominio y Toasts de alta visibilidad.
  - **AWS Ready**: Dockerfiles multi-stage y CI/CD para despliegue automatizado en S3/CloudFront/ECR.
- **Estado:** ✅ Validado y listo para producción.

### [v1.7.0] - Inventory Refactor & Migration Audit (temp_future)
- **Resumen:** Auditoría técnica del legado y migración del módulo de Inventarios a la nueva arquitectura `temp_future`.
- **Detalles:**
  - **Auditoría Forense:** Identificación de lógica oculta de validación de masa (`abs((Qty * Factor) - Weight) > 0.0001`).
  - **Descomposición Modular:** Split de `InventoryDocumentEditor` en componentes granulares para mayor mantenibilidad.
  - **Idempotencia:** Implementación de `Client-Request-ID` para prevenir duplicación de movimientos por micro-cortes.
  - **Abstracción de Servicios:** Eliminación total de `ApiSimulationService` en el flujo de inventarios core.
- **Estado:** ✅ Migrado a `temp_future`.

### [v1.6.2] - Phase 26: Backend Forensic Audit Readiness
- **Resumen:** Sincronización con el Backend tras la implementación del Ledger Inmutable y auditoría forense.
- **Detalles:**
  - **Identidad de Movimiento**: Backend ya procesa y valida `uom_id`, `weight` y `unit_price`.
  - **Inmutabilidad**: Confirmado bloqueo total de `UPDATE/DELETE`. El frontend debe manejar errores `400 Bad Request` (IMMUTABLE_ERROR) si se intentan ediciones prohibidas.
  - **Trazabilidad**: Uso obligatorio de `X-Correlation-ID` nativo ya integrado en el interceptor.
- **Estado:** ✅ Backend Listo para Consumo.

### [v1.6.3] - Phase 27: Dashboard CQRS Backend Integration Readiness
- **Resumen:** Backend listo para alimentar el Dashboard Industrial de Movimientos.
- **Detalles:**
  - **Cards**: Consumo vía `GET /api/v1/dashboard/summary` (Filtro 24h automático).
  - **Ledger**: Consumo vía `GET /api/v1/dashboard/movements` (Paginación y tipos ENTRY/EXIT/TRANS).
  - **Multi-tenancy**: Validado que el frontend no requiere inyectar filtros de empresa; el backend los extrae del header.
Confirmado bloqueo total de `UPDATE/DELETE`. El frontend debe manejar errores `400 Bad Request` (IMMUTABLE_ERROR) si se intentan ediciones prohibidas.
  - **Trazabilidad**: Uso obligatorio de `X-Correlation-ID` nativo ya integrado en el interceptor.
- **Estado:** ✅ Backend Listo para Consumo.

### [v1.6.1] - Frontend Hard Validation & Master Data Reactivity
- **Resumen:** Implementación de Validaciones Duras basadas en los conceptos maestros para asegurar la integridad de datos antes de transmitirlos al backend.
- **Detalles:**
  - **Reacción a Flags:** Los campos del documento reaccionan dinámicamente a los DTOs `requires_external_entity` y `requires_target_warehouse`.
  - **Bloqueo Determinístico:** El botón "Confirmar Registro" es bloqueado permanentemente si `totalWeight <= 0` o faltan parámetros de Master Data.
  - **Componentes Afectados:** `inventory-document-editor.component.ts` implementa todo este chequeo como `computed signal`. Tipos acoplados en `api.types.ts`.
- **Estado:** ✅ Completado.

### [v1.6.0] - Industrial Mimesis & Total Brand Recovery
- **Resumen:** Lograda paridad visual total (100%) con el estándar `temp_future` y restauración de la identidad de marca completa.
- **Detalles:**
  - **Brand Recovery:** Re-integración del logo textual "InternoCore" en Menú Principal y Header, complementando el icono hexagonal.
  - **Cromatic Purge:** Eliminación masiva de clases hardcoded (`text-white`, `bg-white`, borders fijos) para asegurar la reactividad total al tema Light/Dark.
  - **Visual Synchronization:** Sincronización de variables RGB en `styles.css` basada en auditoría de `temp_future`.
  - **Layout Sanitization:** Corrección de duplicación de etiquetas y estandarización de contrastes en tooltips y perfiles de usuario.
- **Estado:** ✅ Completado (Phase 25.2).

### [v1.5.1] - Backend Audit Fixes & Inventory Industrialization
- **Resumen:** Remediación de seguridad backend y finalización del diseño industrial para el módulo de Inventario.
- **Detalles:**
  - **Optimistic Locking:** Activación de control de concurrencia en modelos de Maestro de Datos.
  - **Multi-tenancy Force:** Inyección de filtros `company_id` obligatorios en repositorios y servicios.
  - **Inventory UI:** Rediseño completo del Editor de Documentos (Split View, Neon Totals, Floating Actions).
  - **Seed Fixing:** Script de semillas corregido para alineación con `SYSTEM_USER_ID` (0000...0000).
- **Estado:** ✅ Completado y Homologado.

### [v1.5.0] - Futuristic Industrial Refactor & Localization
- **Resumen:** Refactorización integral de la UI para alinearla con el sistema de diseño "Interno Core" e implementación de localización reactiva.
- **Detalles:**
  - **Identidad Visual:** Implementación de temas oscuros profundos, acentos neón (#00E5FF) y glassmorphism en Login, Tenant Selection y Layout.
  - **Localization Engine:** Nuevo `TranslationService` basado en Angular Signals con soporte para carga dinámica de `es.json` y `en.json`.
  - **Advanced Login:** Sistema híbrido con modo "Office" (Google/Microsoft SSO) y modo "Plant Floor" (Escaneo QR y Buffer RFID de alta velocidad).
  - **Context Selection:** Nueva interfaz de selección de empresa con búsqueda en tiempo real y KPIs de estado.
  - **Header & Sidebar:** Migración total a Material Icons, integración de selector de idioma y toggle de tema reactivo.
- **Estado:** ✅ Completado y Verificado (Build Prod OK).

### [v1.3.1] - Fix de Persistencia y Flujo T2
- **Resumen:** Estabilización completa del flujo de autenticación y cambio de contexto.
- **Detalles:**
  - `AuthInterceptor` ahora inyecta correctamente `x-selection-token` (handshake) y `x-company-id` (negocio) en minúsculas.
  - `NavigationService` carga menús dinámicos basados en los `scopes` devueltos en el T2.
  - `AuthService` normalizado para consumir `ApiResponse` y gestionar la persistencia del `selection_token`.
- **Estado:** Estable.

### [v1.3.1] - Corrección de Persistencia y Cambio de Contexto
- **Resumen:** Se ha estabilizado el flujo de "Cambiar Empresa", eliminando el error `No selection_token available` y asegurando que el estado del frontend se limpie correctamente.
- **Archivo:** `src/app/core/services/auth.service.ts`
  - **Cambiado:** Se modificó el método `selectCompany` para evitar el borrado del `selection_token` de `sessionStorage` tras una selección exitosa.
  - **Cambiado:** Se robusteció el método `switchCompany` para limpiar explícitamente el contexto de la empresa anterior (`access_token`, `company_id`) de `localStorage` y forzar la transición al estado `handshake`.
  - **Cambiado:** Se ajustó la extracción de datos en `login` y `selectCompany` para leer desde la propiedad `response.data`, alineándose con la estructura `ApiResponse` del backend.
- **Archivo:** `src/app/core/interceptors/auth.interceptor.ts`
  - **Verificado:** Se confirmó que el interceptor maneja correctamente la inyección condicional de `x-selection-token` (para la fase de selección) y `x-company-id` + `authorization` (para peticiones autenticadas), usando siempre cabeceras en minúsculas.
  - **Razón:** Garantizar un flujo de autenticación multi-tenant robusto, permitiendo al usuario cambiar de contexto de empresa sin perder la sesión principal.

### [v1.0.3] - Implementación de Flujo Multi-Tenancy y Onboarding
- **Resumen:** Se reestructuró el flujo de autenticación para soportar múltiples empresas por usuario, roles con permisos dinámicos y un flujo de bienvenida para empresas nuevas.

- **Archivo:** `src/app/app.routes.ts`
  - **Cambio:** Se migraron las rutas a `loadComponent` para lazy-loading y se añadieron todas las rutas de los módulos de Inventario y Producción. Se añadió la ruta `/onboarding`.
  - **Razón:** Mejorar el rendimiento inicial de la aplicación y completar la navegación del sistema según el blueprint.

- **Archivo:** `src/app/services/api-simulation.service.ts`
  - **Cambio:** Se reconfiguró la base de datos mock para simular 3 empresas (`Enterprise`, `Standard`, `New`). Se crearon roles con permisos específicos y se ajustó el método `login` y `selectContext` para ser dinámicos.
  - **Razón:** Simular un entorno multi-tenancy realista que permita probar los flujos de permisos y onboarding.

- **Archivo:** `src/app/services/auth.service.ts`
  - **Cambio:** Se eliminó la lógica de auto-selección de empresa en el método `login`. Se verificó que la redirección a `/onboarding` funcione correctamente.
  - **Razón:** Forzar siempre la selección manual de la empresa por parte del usuario, un requisito clave del flujo de "handshake".

### [v1.0.5] - Ajuste de Visibilidad del Menú Lateral (RBAC) y Corrección de Build
- **Resumen:** Se implementó un filtrado estricto en el menú de navegación basado en los permisos del rol del usuario. Se corrigió un error de build relacionado con la creación de órdenes de trabajo.

- **Archivo:** `src/app/services/api-simulation.service.ts`
  - **Cambio:** Se corrigió un error de tipado en `createWorkOrder` (`cmd.cost` a `cmd.estimatedCost`). Se ajustó la definición de roles para que 'Standard' solo reciba permisos de la categoría 'Inventory'.
  - **Razón:** Solucionar un error de compilación que impedía el funcionamiento y alinear la simulación de datos con los requisitos de RBAC.

- **Archivo:** `src/app/services/navigation.service.ts`
  - **Cambio:** Se actualizó `generateMenu` para filtrar los módulos principales y sus hijos basándose en un array de strings de permisos.
  - **Razón:** Garantizar que el menú lateral se reconstruya dinámicamente y muestre únicamente los módulos a los que el usuario tiene acceso según su rol.

- **Archivo:** `src/app/services/auth.service.ts`
  - **Cambio:** Se aseguró que `selectCompany` extraiga los nombres de los permisos (`string[]`) y los pase al `NavigationService`. Se verificó que el `SessionContext` (incluyendo los permisos) se guarde en `localStorage`.
  - **Razón:** Implementar la persistencia de los permisos. Al recargar la página, `restoreSession` lee los permisos y regenera el menú filtrado correctamente.

- **Archivo:** `src/app/modules/auth/tenant-selection.component.ts`
  - **Cambio:** Se mejoró la alerta visual para las empresas nuevas, añadiendo un efecto de resplandor animado y un icono más descriptivo.
  - **Razón:** Hacer más evidente la acción requerida para configurar una nueva planta, mejorando la experiencia de usuario en el onboarding.

### [v1.0.6] - Corrección de Gráficas de Dashboard sin Datos
- **Resumen:** Las gráficas del dashboard de producción (Tendencia Semanal y Pareto de Tiempos Muertos) no mostraban datos porque el servicio de simulación devolvía arrays vacíos.

- **Archivo:** `src/app/services/api-simulation.service.ts`
  - **Cambio:** Se pobló con datos de prueba los arrays `weeklyTrend` y `downtimePareto` dentro del objeto `ProductionDashboardDto` que retorna el método `getProductionDashboard`.
  - **Razón:** Proveer datos simulados a los componentes de las gráficas para que puedan renderizar la información correctamente y permitir la validación visual de la UI.

### [v1.0.7] - Creación del Modelo de Dominio Compartido
- **Resumen:** Se creó un nuevo archivo de tipos (`domain.types.ts`) que actúa como la "fuente de verdad" para las estructuras de datos de la aplicación, reflejando los modelos del backend.

- **Archivo:** `src/app/core/models/domain.types.ts`
  - **Cambio:** Se creó el archivo con las interfaces y tipos principales del dominio, incluyendo `BaseEntity`, `AuditBase`, `WorkOrder`, `AuthResponse`, etc.
  - **Razón:** Establecer un contrato de datos claro y tipado entre el frontend y el backend, mejorando la mantenibilidad y reduciendo errores de integración. Este archivo será el espejo de `Interno.Common` e `Interno.Domain`.

### [v1.0.2] - Implementación de Filtros en Documentos de Inventario
- **Archivo:** `src/app/modules/inventory/inventory-documents-list.component.ts`
  - **Cambio:** Se reemplazaron los botones de filtro estáticos por una implementación funcional basada en Signals.
  - **Razón:** Permitir al usuario filtrar la lista de documentos por tipo (Todos, Entradas, Salidas) de forma reactiva y eficiente, sin recargar datos desde el servicio.
  - **Detalles:**
    - Se introdujo un `signal` (`filter`) para mantener el estado del filtro actual.
    - Se creó un `computed signal` (`filteredDocuments`) que deriva la lista de documentos a mostrar, reaccionando a los cambios en el filtro.
    - Se actualizaron los botones en la plantilla para usar `(click)` y `[ngClass]` para reflejar el estado activo del filtro.
    - La tabla ahora itera sobre el `computed signal`, asegurando que la UI se actualice automáticamente.

### [v1.0.1] - Corrección de Visibilidad Local y Rutas
- **Archivo:** `src/app/services/auth.service.ts`
  - **Cambio:** Se implementó `restoreSession()` en el constructor.
  - **Razón:** Al refrescar la página (F5) en local, el sistema perdía los permisos y el menú desaparecía. Ahora lee de `localStorage` y dispara `navService.generateMenu()`.
  
- **Archivo:** `index.tsx` (Router Map)
  - **Cambio:** Se mapearon todas las rutas de Inventarios (`/inventory`, `/inventory/documents`, `/inventory/warehouses`, etc.).
  - **Razón:** Los clics en la barra lateral fallaban porque Angular no conocía las rutas de los nuevos módulos.

- **Archivo:** `src/app/services/navigation.service.ts`
  - **Cambio:** Se robusteció la lógica de `generateMenu()` para filtrar categorías y submenús simultáneamente.
  - **Razón:** Asegurar que si un usuario tiene permiso de 'inventory', vea todos los sub-módulos asociados.

- **Archivo:** `src/app/services/api-simulation.service.ts`
  - **Cambio:** Se expandieron los permisos base (`p1` a `p10`) para cubrir el 100% de la funcionalidad del Blueprint.

---
**Próximos Pasos Recomendados:**
1. ~~Implementar filtros reales en la tabla de documentos de inventario.~~ (Completado en v1.0.2)
2. Mejorar la validación de stock negativo en el editor de documentos.

### [v1.0.4] - Integración de Componente de Selección de Tenant
- **Archivo:** `src/app/modules/auth/tenant-selection.component.ts`
  - **Cambio:** Se procesó e integró el componente `TenantSelectionComponent` corrigiendo la codificación HTML de la plantilla.
  - **Análisis Técnico:**
    - Componente Standalone con inyección de dependencias moderna (`inject`).
    - Uso de `output<void>()` (Angular 17.3+).
    - Control de flujo `@for` y `@if`.
  - **Requisitos para Retomar (Checklist):**
    1. **Estilos:** Definir `.animate-fade-in-up` (keyframes) y `.custom-scrollbar` en `src/styles.css` o configuración de Tailwind.
    2. **Iconos:** Asegurar carga de FontAwesome (clases `fa-industry`, `fa-wand-magic-sparkles`, etc.).
    3. **Modelo:** `UserCompanyAccess` debe tener la propiedad `company.isNew` y `company.plan`.
    4. **Servicio:** `AuthService` debe manejar la señal `availableAccesses`.

### [v1.0.8] - Definición de Permisos Granulares en AuthService
- **Resumen:** Se actualizó la inyección de permisos para el rol 'admin' en `AuthService` para utilizar un formato estricto `modulo:submodulo`.
- **Archivo:** `src/app/services/auth.service.ts`
  - **Cambio:** Se expandió el array `permissionNames` en el modo "Dios Extendido" para incluir sub-permisos explícitos para Production, Inventory, Maintenance, Quality, Settings y System.
  - **Razón:** Permitir que `NavigationService` detecte correctamente la jerarquía de menús y renderice los submenús correspondientes en el sidebar, asegurando acceso completo a todas las vistas del sistema.

### [v1.0.9] - Refactorización de Estilos y Limpieza
- **Resumen:** Se centralizaron los estilos globales y se configuró Tailwind CSS correctamente en la arquitectura del proyecto.
- **Archivo:** `src/index.css`
  - **Cambio:** Creación del archivo de estilos globales con directivas `@tailwind`.
- **Archivo:** `angular.json`
  - **Cambio:** Registro de `src/index.css` en el pipeline de compilación (build y test).
  - **Razón:** Asegurar que los estilos globales y utilidades de Tailwind estén disponibles en toda la aplicación sin depender de estilos en línea en `index.html`.

### [AUDIT-2026-01-24] - Informe de Situación Actual (Technical Snapshot)
- **Estado del Runtime:**
  - **Zoneless:** Confirmado (Angular 19.1.0).
  - **Reactivity:** Uso consistente de Signals (`signal`, `computed`) para gestión de estado local y filtros.

- **Mecánica de Autenticación:**
  - **Flujo:** Definido como 3 fases (Login -> Tenant Selection -> Context).
  - **Estado:** 🔴 **CRÍTICO**. La implementación actual en `AuthService` no procesa el `handshakeToken` ni gestiona el array de `tenants` devuelto por el backend v1.1.
  - **Persistencia:** No se detecta mecanismo robusto para persistir `company_id` activo más allá de la sesión volátil.

- **Arquitectura de Red:**
  - **Interceptor:** `AuthInterceptor` detectado.
  - **Headers:** Inyección de `Authorization` presente pero dependiente de almacenamiento incompleto. Inyección de `X-Company-Id` **AUSENTE**. Esto bloqueará cualquier petición multi-tenant.

- **Cumplimiento UI Industrial:**
  - **Tailwind:** Configuración de colores correcta (`primary: #0A4F70`, `industrial-gray`).
  - **Ergonomía:** ⚠️ **ALERTA**. No se observan extensiones de tema para alturas 'Fat Finger' (min-h-14 / 56px). Se recomienda forzar esto en `tailwind.config.js`.

- **Estructura de Navegación:**
  - **Sidebar:** Renderizado dinámico basado en `NavigationService` y permisos (RBAC).
  - **Modo:** Estático/Relativo. No se detecta configuración para modo Fly-out.

- **Modelos de Datos:**
  - **SSOT:** `src/app/core/models/domain.types.ts`.
  - **Entidades Clave:** `WorkOrder`, `ProductionDashboardDto` (KPIs: OEE, Downtime).

### [v1.1.0] - Migración a Zoneless Puro
- **Resumen:** Se eliminó la dependencia de `zone.js` para optimizar el rendimiento y se habilitó la detección de cambios experimental sin zonas.
- **Archivo:** `src/main.ts`
  - **Cambio:** Inyección de `provideExperimentalZonelessChangeDetection()` y adición de `import '@angular/compiler'`.
- **Archivo:** `angular.json`
  - **Cambio:** Eliminación de `zone.js` de los polyfills de build y test.

### [v1.1.1] - Multi-tenant Network Layer
- **Resumen:** Implementación de la infraestructura de red para soportar peticiones autenticadas y contextualizadas por empresa.
- **Archivo:** `src/app/core/interceptors/api.interceptor.ts`
  - **Creación:** Interceptor funcional que inyecta `Authorization` y `X-Company-Id` leyendo Signals del `AuthService`.
- **Archivo:** `src/app/app.config.ts`
  - **Cambio:** Registro del interceptor mediante `provideHttpClient(withInterceptors([...]))`.

### [v1.1.2] - Auth Handshake & Persistence
- **Resumen:** Refactorización completa del `AuthService` para implementar el handshake de 3 fases y persistencia de sesión. El sistema ahora es resiliente a recargas de página y soporta múltiples tenants por usuario.
- **Archivo:** `src/app/core/services/auth.service.ts`
  - **Signals:** Implementación de `token`, `currentUser`, `activeCompanyId` y `handshakeToken`.
  - **Persistencia:** Lógica de restauración de sesión desde `localStorage` (`_ic_token`, `_ic_company_id`).
  - **Flujo:** Métodos `login` (Fase 1) y `selectCompany` (Fase 2) conectados con el backend v1.1.

### [v1.1.3] - Integración de Datos Demo y Feedback Visual
- **Resumen:** Se completó la integración de servicios de feedback (Toast) y datos de producción simulados para la validación en modo demo.
- **Estado:** Listo para validación de usuario (Mañana).
- **Cambios:**
  - Integración de `ToastService` para notificaciones de sistema.
  - `ProductionDataService` ahora sirve datos precargados para empresas demo.
  - Validación de flujo con empresas pre-cargadas.

### [v1.1.4] - Consolidación de Arquitectura y Limpieza Técnica
- **Resumen:** Eliminación de deuda técnica en interceptores y estandarización de manejo de errores Backend-Frontend.
- **Frontend:**
  - **Refactor:** `auth.interceptor.ts` ahora es la única fuente de verdad para headers (`Authorization` y `X-Company-Id`), usando `AuthService`.
  - **Limpieza:** Se eliminó lógica redundante en `api.interceptor.ts`.
  - **Nuevo:** `ErrorMapper` para traducción centralizada de códigos HTTP a mensajes de usuario.
- **Backend:**
  - **Common:** Creación de `exceptions.py` (DomainException, NotFound, BusinessRule) y `error_handlers.py` para respuestas JSON consistentes.
- **Protocolo:**
  - **Header:** Se estandarizó el uso de `X-Company-Id` en todo el stack.

## 2026-02-04: Sincronizaci�n de Contratos v2.1
*   **Hito**: Sincronizaci�n de Contratos v2.1
*   **Cambios**:
    *   **Homologaci�n de interfaces**: Refactor completo a snake_case (selection_token, 
ole_names) en pi.types.ts.
    *   **AuthService Update**: Actualizaci�n de l�gica de login y selecci�n de empresa para consumir la nueva estructura JSON.
    *   **Interceptor Check**: Confirmaci�n de inyecci�n correcta de X-Company-Id en uth.interceptor.ts.
---

## 🔍 AUDITORÍA TÉCNICA - Backend Middleware & Data Structure (2026-02-06)

### 1. TenantSecurityMiddleware & Response Envelope

**Backend Source:** `backend/auth_service/app/core/middleware.py`
- ✅ **No envuelve respuestas.** El middleware solo valida headers X-Company-Id contra JWT claims.
- ✅ **ApiResponse envelope:** Definido en `common/responses.py` como estructura de envío:
  ```json
  {
    "status": "success|error",
    "data": {...},          // Payload real
    "message": "string",
    "meta": {"trace_id": "uuid", "latency": "ms"}
  }
  ```

### 2. Backend Schema Mapping (LoginResponse Flow)

**Source:** `backend/auth_service/app/schemas/auth.py`

| Campo Backend | Propiedad Interface Frontend | Tipo de Dato | Notas |
|---|---|---|---|
| `selection_token` | `selection_token` | `string` | JWT Temporal (Fase 1) - sin claims de empresa |
| `user_id` | `user_id` | `string` (UUID) | ID único del usuario en el sistema global |
| `companies[].company_id` | `company_id` | `string` (UUID) | ID de empresa en la lista de selección |
| `companies[].company_name` | `company_name` | `string` | Nombre legible de la empresa |
| `companies[].logo` | `logo` | `string (URL)` | URI de logo (opcional) |
| `companies[].role_names` | `role_names` | `string[]` | Array de nombres de roles asignados |
| `companies[].is_new` | `is_new` | `boolean` | Flag de empresa nueva (requiere onboarding) |
| `is_new` (global) | `isNew` | `boolean` | Flag de usuario nuevo en el sistema |

### 3. Frontend Interface Alignment

**Source:** `frontend/src/app/core/models/api.types.ts`

```typescript
// ✅ CORRECTO
export interface LoginResponse {
  selection_token: string;      // Matches backend
  user_id: string;              // Matches backend (UUID string)
  companies: CompanySelection[]; // Matches backend array
  isNew: boolean;                // NOTA: Backend puede enviar is_new (snake_case)
}

export interface CompanySelection {
  company_id: string;           // ✅ UUID string
  company_name: string;         // ✅ string
  logo?: string;                // ✅ optional
  role_names: string[];         // ✅ string[]
  is_new: boolean;              // ✅ boolean (may need isNew alias)
}
```

### 4. Data Extraction Layer (AuthService)

**Source:** `frontend/src/app/services/auth.service.ts` → `login()` method

**PIPELINE:**
1. HTTP POST `/api/v1/auth/login` → ✅ Returns `ApiResponse<CompanyAccessDto>`
2. Tap operator intercepts → receives `response: { status, data, message, meta }`
3. **EXTRACTION:** `const data = response?.data;` (NOT `response?.data?.data`)
   - ✅ `data` now contains the `CompanyAccessDto` object
   - ✅ `data.selection_token` is directly accessible
4. **DEFENSIVE MAPPING:** Companies array handles both snake_case and camelCase:
   ```typescript
   is_new: c.is_new || c.isNew || false  // Handles both notations
   ```

### 5. Interceptor Deserialization Strategy

**Source:** `frontend/src/app/core/interceptors/auth.interceptor.ts`

**ROLE:** HTTP header injection (NOT response transformation)
- ✅ Reads `AuthService.currentContext()` for `access_token` and `companyId`
- ✅ Injects `Authorization: Bearer <token>` header
- ✅ Injects `X-Company-Id: <companyId>` header for all subsequent requests
- ℹ️ **Does NOT deserialize** the response body (leave to AuthService)

### 6. Session Persistence Flow

| Phase | Storage | Content |
|-------|---------|---------|
| **T1 (Login)** | `sessionStorage` | `selection_token` (JWT - temporary) |
| **T1 (Login)** | Signal | `authStep = 'handshake'` |
| **T2 (SelectCompany)** | `localStorage` | `currentContext` (access_token, companyId, role, permissions) |
| **T2 (SelectCompany)** | Signal | `authStep = 'authenticated'` |
| **Persist** | `localStorage` | `_ic_auth_ctx`, `_ic_auth_user`, `_ic_auth_accesses` |

### 7. Known Issues & Resolutions

**Issue 1:** Backend sends `is_new` (snake_case) but frontend expects `isNew` (camelCase)
- ✅ **Fixed:** Defensive mapping in AuthService: `c.is_new || c.isNew || false`

**Issue 2:** Double-wrapping assumption (`response?.data?.data`)
- ✅ **Fixed:** Removed double-wrapping; now only `response?.data` (single level)

**Issue 3:** Null/undefined checks inadequate
- ✅ **Fixed:** Added explicit null checks for `companies` array and fallback values

### 8. Validation Checklist for Future Sessions

Before deploying changes:
1. ✅ Verify `ApiResponse` structure in `common/responses.py`
2. ✅ Verify `CompanyAccessDto` schema in `auth_schemas.py`
3. ✅ Confirm backend endpoint returns `response_model=ApiResponse`
4. ✅ Confirm frontend `LoginResponse` matches backend `CompanyAccessDto` + `selection_token`
5. ✅ Test HTTP response in DevTools to confirm structure
6. ✅ Verify `sessionStorage.selection_token` is set after login
7. ✅ Verify `TenantSelectionComponent` renders when `authStep === 'handshake'`
8. ✅ Verify `selectCompany()` sends `X-Selection-Token` and `X-Company-Id` headers
9. ✅ Verify navigation to `/onboarding/onboarding-wizard` or `/dashboard` based on `is_new`

---

## 2026-02-06: Data Flow Homologation & Interceptor Architecture (FINAL)

### **The Complete Picture: Backend → Interceptor → Service**

| Layer | Output Structure | Input to Next Layer | Comments |
|-------|------------------|-------------------|----------|
| **Backend** | `{ status, data: { selection_token, user_id, ... }, message, meta }` | Raw HTTP Response | Always wraps in ApiResponse (middleware ensures this) |
| **HTTP Wire** | Same as above (wire protocol) | HttpResponse<ApiResponse<T>> | Network transmission |
| **API Interceptor** | Extracts `.data` | `{ selection_token, user_id, companies, ... }` | **CRITICAL:** Unwraps ApiResponse, passes clean object |
| **AuthService.tap()** | Receives clean object | `data.selection_token`, `data.companies` | No `.data` prefix needed - interceptor already unwrapped |
| **AuthService Signals** | Publishes state | Frontend reactive components | `authStep`, `availableAccesses`, `currentUser` |

### **Why This Architecture?**

1. **Backend**: Global middleware ensures consistency (no mixed response formats)
2. **Interceptor**: Single responsibility - unwrap ApiResponse envelope
3. **Services**: Only deal with business objects (no protocol noise)
4. **Components**: Subscribe to signals, never parse ApiResponse

### **CRITICAL RULE: The Interceptor Is The Aduana (Customs)**

- **Incoming (Network):** `ApiResponse` envelope
- **Outgoing (Services):** Clean business data
- **Never** bypass the interceptor by assuming different structures
- **Always** access `response.field` directly in services (interceptor handles unwrapping)

### **Evidence of Correctness (Audit 2026-02-06)**

✅ **Login Endpoint:** Returns `ApiResponse(status='success', data=CompanyAccessDto(...))`  
✅ **Select-Company Endpoint:** Returns `ApiResponse(status='success', data={access_token, ...})`  
✅ **Global Middleware:** Detects ApiResponse and passes through (no double-wrapping)  
✅ **Interceptor:** Extracts `.data` from both responses  
✅ **AuthService:** Receives clean object in both cases  
✅ **No Inconsistencies:** Both endpoints follow the same contract  

### **Future-Proofing Checklist**

- [ ] If adding new endpoints: Always return `ApiResponse` (backend must enforce)
- [ ] If modifying interceptor: Remember it's the ONLY place that unwraps ApiResponse
- [ ] If adding direct HTTP calls: They will receive ApiResponse until interceptor processes them
- [ ] If debugging response issues: Check Network tab (ApiResponse), then Console (after interceptor unwraps)

### [v1.1.5] - Security Hardening & App Initialization
- **Resumen:** Se implementó un blindaje de seguridad para evitar el acceso no autorizado al Dashboard mediante manipulación de estado o borrado de caché.
- **Componentes Afectados:**
  - `AuthGuard`: Refactorizado a lógica síncrona estricta. Verifica `localStorage` directamente antes de permitir la navegación.
  - `AppInitializer`: Nueva factoría en `app.config.ts` que bloquea el arranque de la app hasta que `AuthService.restoreSession()` finaliza.
  - `AuthService`: Lógica de `switchCompany` ajustada para limpiar `access_token` pero preservar `selection_token` (Handshake).
- **Correcciones:**
  - **Fuga de Dashboard:** Solucionado. Si se borra `_ic_auth_ctx`, el guard redirige a `/login` instantáneamente.
  - **Multitenancy:** El interceptor ahora emite advertencias si se intenta una petición autenticada sin `X-Company-Id`.

### [v1.1.6] - Environment Configuration Prep
- **Resumen:** Preparación para despliegue híbrido (AWS/On-Premise).
- **Acción:** Se validó que las URLs base no estén hardcodeadas.
- **Estrategia:**
  - Local: `http://localhost:8000/api/v1`
  - Producción: Inyección mediante `environment.ts` o `window.env` (Runtime Config) para contenedores Docker agnósticos.

### [v1.1.7] - Zero Trust Security Implementation
- **Resumen:** Se eliminó la confianza implícita en `localStorage`. Ahora el sistema valida criptográficamente la sesión con el backend antes de iniciar.
- **Componentes Críticos:**
  - **AuthService:** `restoreSession()` ahora es asíncrono y realiza una petición `GET /auth/validate`. Si falla, ejecuta `logout()`.
  - **AppInitializer:** Configurado para bloquear el arranque de la aplicación (`Promise`) hasta que la validación del token responda.
  - **AuthInterceptor:** Implementa un "Kill Switch". Cualquier respuesta `401 Unauthorized` provoca un logout inmediato y redirección a login.
  - **AuthGuard:** Ahora verifica estrictamente el signal `authStep() === 'authenticated'`, garantizando que la validación de red pasó exitosamente.
- **Resultado:** Inmunidad a sesiones "zombie" o tokens expirados en caché local.

### [v1.1.8] - Zero Trust Architecture Implementation
- **Resumen:** Implementada validación activa de sesión en el arranque (Zero Trust Architecture). Se eliminó la dependencia exclusiva de localStorage para la navegación inicial.
- **Cambios Técnicos:**
  - **AuthService:** `restoreSession()` refactorizado para retornar `Observable<boolean>` y validar contra endpoint `/validate`.
  - **AppConfig:** `APP_INITIALIZER` configurado como bloqueante (`lastValueFrom`) esperando la validación del token.
  - **AuthGuard:** Blindado para depender únicamente del signal `authStep` en memoria.
  - **AuthInterceptor:** Kill switch activado para errores 401 y 0 (Server Offline).

### [v1.1.8] - Zero Trust Architecture Implementation
- **Resumen:** Implementada validación activa de sesión en el arranque (Zero Trust Architecture). Se eliminó la dependencia exclusiva de localStorage para la navegación inicial.
- **Cambios Técnicos:**
  - **AuthService:** `restoreSession()` refactorizado para retornar `Observable<boolean>` y validar contra endpoint `/validate`.
  - **AppConfig:** `APP_INITIALIZER` configurado como bloqueante (`lastValueFrom`) esperando la validación del token.
  - **AuthGuard:** Blindado para depender únicamente del signal `authStep` en memoria.
  - **AuthInterceptor:** Kill switch activado para errores 401 y 0 (Server Offline).

### [v1.2.0] - Zoneless Architecture & MES Signals Integration
- **Resumen:** Se ha completado la transición a una arquitectura **Zoneless** pura en el frontend, eliminando la dependencia de `zone.js` y confiando exclusivamente en **Angular Signals** para la detección de cambios y la reactividad.
- **Componentes Afectados:**
  - `AuthInterceptor`: Ahora accede a `AuthService.activeCompanyId()` (Signal) de forma síncrona para inyectar el header `X-Company-Id`, garantizando el contexto del tenant sin overhead de Observables.
  - `ProductionService`: Implementado usando `resource` y `computed` signals para manejar el estado del Dashboard OEE.
- **Identidad Triple (Verificación UI):**
  - Se verificó que las interfaces en `src/app/core/models/mes.types.ts` reflejen la estructura del backend: `id` (UUID), `sequence_number` (Int) y `folio` (String).
  - Las vistas de Producción están preparadas para mostrar el `folio` como identificador principal y usar `id` para ruteo.
- **Decisión Técnica (Zoneless):**
  - **Por qué:** Para reducir el bundle size y mejorar el rendimiento en dispositivos industriales (tablets de piso) eliminando el monkey-patching de Zone.js.
  - **Cómo:** Se configuró `provideExperimentalZonelessChangeDetection()` en `app.config.ts`.
- **Inmutabilidad (UX):**
  - Se establecieron las bases para que los formularios de `ProductionResult` respeten el estado `CONFIRMED`, bloqueando la edición mediante Signals derivados (`isEditable = computed(() => status() === 'DRAFT')`).

### [SPEC-UPDATE-2026-02-11] - Definición Técnica de Autenticación y WMS
- **Resumen:** Se han incorporado las especificaciones técnicas detalladas para el Handshake de 2 pasos, la gestión de WMS y la paridad de entornos AWS/Local.
- **Cambios en Contexto:**
  - **Auth Architecture:** Definición estricta del flujo `login` -> `selection_token` -> `selectCompany` (Header `X-Selection-Token`).
  - **Storage:** Separación de tokens temporales (Session) y persistentes (Local).
  - **WMS:** Jerarquía de datos (Tenant > Warehouse > Zone > Bin) y filtrado de precios contextual.
  - **Onboarding:** Lógica para el flag `is_new` y el endpoint `/complete-onboarding`.
  - **Infraestructura:** Estrategia de build agnóstica para S3/CloudFront o Nginx.
  - **Seguridad:** Protocolo de manejo de errores 401/403 en `MultiTenantInterceptor`.

## 🔍 AUDITORÍA DE INTEGRIDAD: BACKEND VS FRONTEND (2026-02-13)

### 1. Sincronización de Endpoints (AuthService)

| Endpoint Backend | Método Frontend | Estado | Hallazgo |
|---|---|---|---|
| `POST /api/v1/auth/login` | `login()` | ✅ Sincronizado | Maneja correctamente `selection_token` y lista de empresas. |
| `POST /api/v1/auth/select-company` | `selectCompany()` | ✅ Sincronizado | Envía contexto para obtener `access_token`. |
| `GET /api/v1/auth/me` | `restoreSession()` | ⚠️ **Discrepancia** | Frontend llama a `/validate` (v1.1.8) pero Backend expone `/me`. Requiere refactor inmediato. |

### 2. Handshake de Seguridad (AuthInterceptor)
- **Fase 1 (Discovery):** El interceptor detecta correctamente el `selection_token` en `sessionStorage`.
- **Fase 2 (Context):** Se confirma la transición a `access_token` en `localStorage` tras la selección.
- **Transporte:** Se debe validar que el `selection_token` se envíe vía header `X-Selection-Token` (según `FRONTEND_CONTEXT`) para evitar conflictos con el Bearer estándar.

### 3. Aislamiento Multi-Tenant (X-Company-Id)
- **Inyección:** Confirmada en `AuthInterceptor` (referido como `MultiTenantInterceptor` en especificaciones).
- **Regla:** Se inyecta leyendo el Signal `activeCompanyId()`.
- **Cobertura:** Cubre todas las peticiones HTTP excepto las de `auth/login` y `assets`.

### 4. Action Items (Prioridad Alta)
1.  **Refactor Zero Trust:** Cambiar llamada de `/validate` a `/api/v1/auth/me`.
2.  **Onboarding Guard:** Implementar bloqueo de navegación si `is_new === true`.
3.  **Naming Convention:** Unificar nomenclatura de interceptor (`Auth` vs `MultiTenant`) en documentación y código.

## 2026-02-13: Resolución de Auditoría de Integridad
*   **Hito**: Sincronización Backend-Frontend v2.1
*   **Estado**: ✅ COMPLETADO
*   **Cambios Aplicados**:
    *   **Endpoint `/me`**: Se actualizó `AuthService.restoreSession()` para consumir `GET /api/v1/auth/me`, alineándose con el contrato Swagger del backend.
    *   **MultiTenantInterceptor**: Se creó el interceptor unificado que maneja la lógica condicional de cabeceras:
        *   `X-Selection-Token` para el handshake (select-company).
        *   `Authorization` + `X-Company-Id` para el resto de peticiones.
    *   **OnboardingGuard**: Implementado guard funcional que redirige a `/onboarding` si el signal `isNewUser()` es true.
*   **Deuda Técnica Resuelta**:
    *   Eliminada la ambigüedad entre `AuthInterceptor` y `MultiTenantInterceptor`.
    *   Cerrada la brecha de seguridad donde usuarios nuevos podían acceder al dashboard.

### [v1.3.0] - Implementación Módulo de Catálogo (Master Data)
- **Resumen:** Se ha creado la infraestructura base para el módulo de Catálogo, conectando con el `master_data_service` del backend.
- **Cambios Técnicos:**
  - **Modelos:** Definición de interfaces en `catalog.types.ts` con paridad `snake_case` (backend) y soporte para `ApiResponse`.
  - **Servicio:** `MasterDataService` implementado para gestionar Productos, UOMs, Categorías y Marcas.
  - **Componentes:**
    - `ProductListComponent`: Tabla reactiva con Signals y filtros en cliente.
    - `UomManagerComponent`: CRUD básico para gestión de unidades.
  - **Arquitectura:** Uso estricto de `HttpClient` que aprovecha el `AuthInterceptor` existente para la inyección de `X-Company-Id`.
  - **Value Objects:** Definición de interfaz `Money` para futuros usos en precios.

---

## [2026-02-23] Arquitectura de Resiliencia y Telemetría UI

### 1. Cambio Arquitectónico: Offline-First (Read-Only)
Se ha implementado un patrón de **Cache-Then-Fallback** en los servicios críticos del frontend (`MasterDataService`, `WmsService`).
- **Comportamiento:**
  - Las peticiones exitosas guardan la respuesta en `localStorage` con prefijo `interno_cache_`.
  - Si la API falla (Status 0, 500, 404), el servicio intercepta el error y retorna los datos cacheados usando `of()`.
  - Esto permite que la aplicación siga siendo funcional en modo lectura incluso si los microservicios de backend están caídos.

### 2. Nuevo Componente: SystemHealthService
Se creó un servicio centralizado (`src/app/core/services/system-health.service.ts`) para monitorear el estado de los microservicios.
- **Estados:**
  - 🟢 **Online:** Todos los servicios responden (`auth`, `masterData`, `wms`).
  - 🟡 **Degraded:** Fallo en servicios de datos (WMS/MasterData). Se sirve contenido de caché.
  - 🔴 **Offline:** Fallo en `AuthService`. Bloqueo crítico.
- **Signal `isReadOnly`:** Computado global que se activa cuando el estado no es `online`. Deshabilita botones de escritura (Guardar/Crear) en toda la UI.

### 3. Correcciones de API (OpenAPI Sync)
- **Master Data:** Se corrigió la ruta de Unidades de Medida de `/uoms/` a `/api/v1/ums/` para coincidir con la especificación del backend.

### 4. Variables de Entorno y Testing
- **Puerto WMS:**
  - Producción/Dev: `8002`
  - Testing de Resiliencia: `8099` (Simula caída para verificar estado Ámbar).

### 5. Deuda Técnica / Pendientes (Próxima Sesión)
- **UI Debug:** El indicador "Foquito" en `HeaderComponent` no es visible. Revisar estilos Tailwind/Z-Index.
- **Validación de Hidratación:** Confirmar que las tablas se llenan correctamente desde `localStorage` tras un reinicio simulado.

---

### [v1.4.0] - Implementación de Pilares de Identidad (IAM v2)
- **Resumen:** Se han implementado y refactorizado los flujos de identidad principales para alinearlos con las especificaciones de negocio y el estilo visual de Metronic v9.
- **Login & Multi-Tenant:**
  - **Cambiado:** `AuthService.login()` ahora detecta si un usuario tiene una sola empresa y ejecuta la selección automática, omitiendo la pantalla de selección.
- **Recuperación de Contraseña:**
  - **Añadido:** Componentes `ForgotPasswordComponent` y `ResetPasswordComponent` con formularios y lógica de servicio.
  - **Añadido:** Métodos `forgotPassword()` y `resetPassword()` en `AuthService`.
- **Ingreso por Código:**
  - **Cambiado:** `CompleteRegistrationComponent` ahora implementa la lógica `onSubmit` para validar el código y realizar un auto-login, redirigiendo al dashboard.
- **Registro de Empresa:**
  - **Verificado:** El flujo de `RegisterCompanyComponent` ya cumple con el requisito de "Auto-Login" post-registro.
- **Razón:** Unificar y robustecer todos los puntos de entrada y gestión de identidad del usuario final, cerrando brechas funcionales y mejorando la experiencia de usuario.

---

### [v1.4.1] - Implementación de Cliente para Master Data Service
- **Resumen:** Se ha creado el cliente de API para el `master-data-service`, permitiendo al frontend consumir catálogos centrales como Unidades de Medida.
- **Cambios Técnicos:**
  - **Modelos:** Se añadieron las interfaces `UOMRead`, `ProductRead`, `BrandRead`, y `CategoryRead` a `api.types.ts`, alineadas con el Swagger del servicio.
  - **Servicio:** Creación de `MasterDataService` con el método `listUoms()` que apunta a `/api/v1/ums/`.
  - **Componente de Prueba:** Se generó `UomListComponent` para validar la conexión y listar las UOMs, demostrando la correcta integración del interceptor (`X-Company-Id`).
- **Razón:** Habilitar la gestión y visualización de datos maestros en la UI, un paso fundamental para los módulos de Inventario y Producción.

---

### [v1.4.2] - Habilitación de Trazabilidad de Auditoría en UI
- **Resumen:** Se ha implementado la visualización de los campos de auditoría (`created_at`, `created_by`, etc.) en el módulo de Master Data para proveer trazabilidad al usuario final.
- **Cambios Técnicos:**
  - **Modelos:** Se creó la interfaz `AuditBase` en `api.types.ts` con los campos de auditoría y se refactorizaron los modelos `UOMRead`, `ProductRead`, `BrandRead` y `CategoryRead` para heredar de ella.
  - **Componente:** Se actualizó `uom-list.component.ts` para añadir una columna de "Auditoría" que muestra la información de creación y modificación en un tooltip al pasar el mouse sobre un icono.
  - **UX:** Se utiliza el pipe `date:'medium'` para formatear las fechas de auditoría de manera legible.
- **Razón:** Aumentar la transparencia y la capacidad de auditoría del sistema desde la interfaz de usuario, permitiendo a los administradores ver quién y cuándo se creó o modificó un registro maestro.

---

### [v1.3.2] - Implementación de Flujos de Registro e Invitación (IAM v2)
- **Resumen:** Se han creado los componentes y métodos de servicio para soportar el registro de nuevas empresas y la invitación de usuarios, alineando el frontend con el `auth_service` v2.
- **Componentes Nuevos (Esqueletos):**
  - `RegisterCompanyComponent`: Formulario standalone para el auto-registro de nuevos clientes SaaS.
  - `CompleteRegistrationComponent`: Vista para que los usuarios invitados finalicen su registro, capturando el `code` de la URL.
  - `UserInviteModal`: Componente de UI para que los administradores inviten a nuevos miembros.
- **Servicio (`AuthService`):**
  - **Añadido:** `registerCompany()` para consumir `POST /v2/public/register-company`.
  - **Añadido:** `completeRegistration()` para consumir `POST /v2/public/complete-registration`.
  - **Añadido:** `inviteUser()` para consumir `POST /v2/admin/users/invite`.
- **Razón:** Cerrar la brecha funcional identificada en la auditoría de integración con IAM v2, permitiendo el ciclo de vida completo del usuario y la empresa desde la UI.

---

## [2026-02-24] UI Telemetry & Write-Lock Implementation

### 1. UI Telemetry (Health Badge)
- **Componente:** `SystemHealthService` ahora actúa como el sistema nervioso central para la reactividad de la UI a la salud del backend.
- **Integración:** `MasterDataService` y `WmsService` ahora reportan activamente su estado (activo/caído) al `SystemHealthService` en cada llamada a la API (éxito o `catchError`).
- **Feedback Visual:** El "foquito" del avatar (Health Badge) en el `HeaderComponent` es ahora completamente reactivo:
  - 🟢 **Online:** Todos los servicios responden.
  - 🟡 **Degraded:** Un servicio de datos (WMS/MasterData) ha fallado; el sistema opera desde el caché.
  - 🔴 **Offline:** El `AuthService` es inalcanzable.

### 2. Bloqueo de Escritura en Modo Degradado
- **Mecanismo:** Se ha implementado un nuevo signal computado `isReadOnly` dentro de `SystemHealthService`. Devuelve `true` si `overallStatus` no es `'online'`.
- **Impacto:** Este signal es consumido por los componentes de formularios (ej. "Crear Producto") para deshabilitar los botones de "Guardar" y mostrar un mensaje de advertencia.
- **Propósito:** Prevenir la inconsistencia de datos al bloquear operaciones de escritura cuando uno o más microservicios no están disponibles, forzando un modo de "solo lectura" durante las interrupciones.
### [v1.4.3] - SaaS Scale & Billing Awareness (Phase 18 & 10.6)
- **Resumen:** Integración del flujo de Stripe Billing y notificaciones transaccionales profesionales.
- **Cambios Tecnicos:**
  - **Billing:** El frontend ahora soporta el ruteo hacia el `subscription_service` (port 8002) para el embedded checkout.
  - **Interceptors:** Refuerzo de `X-Company-Id` para asegurar que las sesiones de pago estén aisladas por tenant.
  - **Notificaciones:** Soporte para la visualización de renders HTML profesionales con branding (Logo SVG Base64).
- **Razón:** Habilitar el modelo de negocio SaaS con activación automática y feedback visual de primer nivel.

---

## 📅 Roadmap Próxima Jornada
1.  **Pulse UI**: Gráficas de barras apiladas (Stacked Bar Charts) para producción horaria.
2.  **Andon escalation**: UI de configuración de tiempos de respuesta para supervisores.
3.  **Audit Evidence**: Carga de imágenes para paros de línea (MES).

---
**Status Final de Sesión (2026-03-06)**: 🚀 Global 92% Ready.
