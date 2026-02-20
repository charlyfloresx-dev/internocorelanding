
# Auditoría de Integridad Frontend - NexoSuite

**Auditor:** Gemini, Senior QA & Frontend Architect
**Fecha:** 23 de Enero de 2026
**Proyecto:** NexoSuite - Módulo de Autenticación y Arquitectura Base

## 1. Resumen Ejecutivo

Este documento presenta una auditoría exhaustiva del estado actual del frontend de NexoSuite. El objetivo es identificar riesgos, brechas funcionales y el nivel de preparación para la integración con el backend v1.1. Se han analizado rutas, servicios de autenticación, componentes críticos y la estructura general de los módulos.

El análisis revela una base sólida pero con áreas críticas que requieren atención inmediata antes de intentar una conexión real. El sistema de autenticación está incompleto, y la lógica de manejo de errores no está estandarizada, lo que representa el mayor riesgo para la integración.

---

## 2. Estado de Rutas (`app-routing.module.ts`)

Se ha realizado un análisis de las rutas declaradas en el módulo principal de enrutamiento para verificar su correspondencia con componentes físicos existentes.

| Ruta (Path) | Componente Declarado | ¿Componente Existe? | Estado | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `''` | `LoginComponent` | 🟡 | **Parcial** | El componente existe, pero su lógica está incompleta. |
| `'login'` | `LoginComponent` | 🟡 | **Parcial** | Alias de la ruta raíz. |
| `'select-company'`| `TenantSelectionComponent` | 🟡 | **Parcial** | Existe, pero sin lógica de integración. |
| `'dashboard'` | `DashboardComponent` | 🔴 | **Inexistente** | Ruta declarada que apunta a un componente no creado. |
| `'production'` | `ProductionComponent`| 🔴 | **Inexistente** | Módulo declarado sin componente asociado. |
| `'inventory'` | `InventoryComponent` | 🔴 | **Inexistente** | Módulo declarado sin componente asociado. |
| `'admin'` | `AdminComponent` | 🔴 | **Inexistente** | Módulo declarado sin componente asociado. |

**Observaciones:**
- Se han identificado múltiples rutas "muertas" que apuntan a componentes inexistentes. Esto indica una planificación de la arquitectura que aún no se ha materializado en código.
- Las rutas de los módulos principales (production, inventory, admin) están definidas pero no tienen componentes funcionales.

---

## 3. Validación de Contrato (AuthService)

Se ha inspeccionado el `AuthService` para determinar su compatibilidad con el flujo de autenticación de dos tiempos definido por el backend v1.1.

- **Tiempo 1: Handshake (Login)**
    - **¿Maneja `handshakeToken`?** No. El servicio actual no tiene una propiedad o método para recibir y almacenar el `handshakeToken` temporal.
    - **¿Maneja el array de `tenants`?** No. No existe lógica para procesar la lista de empresas (tenants) devuelta tras un login exitoso.

- **Tiempo 2: Selección de Tenant (select-company)**
    - **¿Existe el método `selectCompany()`?** No. No se ha implementado el método que debería tomar el `companyId` seleccionado por el usuario y enviarlo al backend para obtener el JWT final con los roles.

**Conclusión:** El `AuthService` **no está preparado** para el flujo de autenticación v1.1. Su implementación actual es un placeholder y requiere un rediseño completo.

---

## 4. Análisis de Componentes Críticos

### LoginComponent
- **Manejo de Errores:** No se observa un manejo de errores robusto. Las llamadas a `AuthService` no procesan respuestas de error del backend. No hay implementación de un `catchError` que interprete la estructura `{status, data, message, meta}`.
- **Lógica de UI:** La lógica se limita a capturar usuario/contraseña y enviarlos a un método `login()` vacío, sin gestionar estados de carga, éxito o fracaso.

### TenantSelectionComponent
- **Estado:** Es una maqueta visual (UI) sin lógica de negocio.
- **Manejo de Estado:** No hay un mecanismo para recibir la lista de tenants desde el `AuthService` ni para notificar la selección del usuario.
- **Integración:** No hay ninguna llamada a un servicio para ejecutar el segundo paso del login (`select-company`).

---

## 5. Estado de Servicios (ApiService / Interceptor HTTP)

Se ha revisado la capa de comunicación HTTP en busca de la inyección automática de headers requeridos por el backend.

- **Interceptor HTTP:** Se ha localizado un interceptor (`AuthInterceptor`).
- **Inyección de `Authorization` Header:** El interceptor **sí inyecta** el `Authorization` header con un token JWT. Sin embargo, obtiene el token de `localStorage` de una clave (`'token'`) que nunca se establece, dado que el `AuthService` está incompleto.
- **Inyección de `X-Company-Id` Header:** **No se ha implementado** la inyección de este header. El interceptor no tiene lógica para obtener el `companyId` activo y añadirlo a las peticiones.

**Conclusión:** Aunque existe un interceptor, su configuración es disfuncional. No puede obtener el token de autenticación y no gestiona el identificador de la empresa, lo que hará que todas las peticiones a rutas protegidas fallen.

---

## 6. Semáforo de Funcionalidad de Módulos

| Módulo | Estado | Justificación |
| :--- | :--- | :--- |
| **Production** | 🔴 **Inexistente** | Declarado en el enrutamiento y logs de planificación, pero no existen ni componentes, ni servicios, ni módulos de Angular asociados. |
| **Inventory** | 🔴 **Inexistente** | Misma situación que Production. No hay artefactos de código que lo respalden. |
| **Admin** | 🟡 **Maqueta** | Existe una ruta y un componente `AdminComponent` básico, pero este solo contiene una UI estática sin conexión a datos reales (mocks) ni servicios. |

---

## 7. Predicción de Falla Inminente

**Lo primero que fallará cuando intente hacer login contra el backend real es la recepción y manejo de la respuesta del endpoint `/login`.**

**Cadena de Fallos Detallada:**

1.  **Envío Exitoso (Falso Positivo):** El usuario llenará el formulario de login. El `LoginComponent` llamará al `AuthService.login()`. La petición HTTP probablemente se enviará correctamente al backend (si la URL está bien configurada).
2.  **Fallo en el `subscribe()`:** El backend responderá con un `{ status: 'success', data: { handshakeToken: '...', tenants: [...] }, message: '...' }`. El `AuthService` actual no tiene lógica en el `subscribe` para procesar esta estructura. No sabrá qué hacer con `handshakeToken` ni con `tenants`.
3.  **No hay Redirección:** Como el servicio no puede interpretar la respuesta, nunca notificará al `LoginComponent` que el login fue exitoso. El usuario se quedará "atascado" en la pantalla de login, sin redirección a la selección de tenant.
4.  **Error Silencioso o en Consola:** En el mejor de los casos, se mostrará un error genérico en la consola del navegador. En el peor (y más probable), la promesa o el observable simplemente se completará sin ejecutar ninguna acción visible para el usuario, dando la impresión de que el botón "Login" no funciona.

El sistema fallará antes incluso de intentar usar el `handshakeToken` o de llegar a la pantalla de selección de empresa. La brecha está en el contrato de datos más fundamental del flujo de autenticación.
