# 🌐 Contexto para el Agente Frontend: Interno Core

## 1. Naturaleza del Sistema
- **SaaS Multitenant:** El sistema maneja múltiples empresas en una sola base de datos. Cada petición debe incluir el contexto de la empresa seleccionada tras el login.
- **Motor Ledger (Libro Mayor):** El frontend no "edita" registros de inventario o producción directamente. Envía comandos para crear borradores (`DRAFT`) o confirmar transacciones (`CONFIRMED`) que son inmutables.

## 2. La Identidad Triple (Crucial para UI/UX)
El frontend debe ser capaz de manejar y mostrar tres identificadores distintos para cada documento (Inventario o Manufactura):
1.  **UUID (ID Técnico):** Se usa para todas las llamadas a la API (`/documents/{uuid}`). Es invisible para el usuario final pero vital para el ruteo.
2.  **Sequence Number (Auditoría):** Un entero consecutivo por empresa (1, 2, 3...). Se usa en reportes internos de auditoría.
3.  **Folio (Comercial):** El identificador amigable y personalizable (ej: `ALM-2026-0001`). Es el campo principal de búsqueda para el usuario.

## 3. Lógica de Negocio en el Cliente
- **Estados de Documento:** Implementar un flujo visual de estados: `DRAFT` (editable), `CONFIRMED` (solo lectura, inmutable) y `CANCELLED` (solo lectura, tachado visual).
- **Optimistic Locking:** Las pantallas de actualización de stock deben manejar el campo `version_id` para evitar que dos usuarios sobrescriban el stock al mismo tiempo.
- **Validación de Stock:** Aunque el backend valida, el frontend debe consultar el `InventorySnapshot` para alertar preventivamente si el usuario intenta retirar más material del disponible.

## 4. Instrucciones Técnicas de Integración
- **Arquitectura de Autenticación (Handshake de 2 Pasos):**
    1.  **Login (Fase 1):** `AuthService.login(credentials)` captura el `selection_token` (temporal) y la lista de empresas.
        - *Storage:* El `selection_token` se guarda en memoria o `sessionStorage`.
    2.  **Selección de Empresa (Fase 2):** `AuthService.selectCompany(companyId)` envía el `selection_token` en el header `X-Selection-Token`.
        - *Nota:* El `selection_token` debe vivir en `sessionStorage` hasta el logout definitivo para permitir el cambio de contexto entre empresas de la misma cuenta.
        - *Respuesta:* Retorna el `access_token` final (JWT).
        - *Persistencia:* Guardar `access_token`, `company_id` y `role_names` en `localStorage`.
    3.  **Guard de Selección:** Implementar `CanActivate` que redirija al selector si existe `selection_token` pero no `access_token`.

- **Selector de Empresas (UI/UX):**
    - **Interfaz:** Rejilla de tarjetas con logo, nombre y roles.
    - **Onboarding (`is_new`):** Si `is_new: true`, redirigir al "Welcome Wizard". Al finalizar, llamar a `POST /complete-onboarding` con header `X-Company-Id`.

- **Manejo de Moneda:** Usar los componentes de `MoneyMixin` del backend para mostrar precios y costos, respetando la precisión decimal definida.
- **Consumo de API:**
    - `GET /inventory/snapshot`: Usar para búsquedas rápidas de existencias y visualización de almacenes.
    - `POST /documents`: Crear documentos en estado borrador.
    - `POST /documents/{id}/confirm`: Acción crítica que dispara la actualización física del inventario.

## 5. Reglas de Interfaz (UX)
- **No Edición Post-Confirmación:** Una vez que un documento es confirmado, todos los campos de entrada de datos en el formulario deben quedar deshabilitados (`readonly`).
- **Formatos de Folio:** No asumir un formato fijo para los folios; deben mostrarse tal cual los entrega el `FolioService`, ya que cada empresa tiene sus propios prefijos.

## 6. Stack Tecnológico y Arquitectura (Angular 19+)
- **Core Framework:** Angular 19.1.0 en modo **Zoneless** (sin `zone.js`) para máximo rendimiento.
- **Gestión de Estado:** Uso exclusivo de **Angular Signals** (`signal`, `computed`, `effect`) para reactividad granular y filtros en tiempo real.
- **Estilos:** **Tailwind CSS** configurado globalmente (`src/index.css`). Colores corporativos: Primary `#0A4F70`.
- **Ruteo:** `HashLocationStrategy` habilitado para compatibilidad en entornos locales/S3.
- **Arquitectura de Componentes:** **Standalone Components** por defecto.

## 7. Seguridad y Networking (Zero Trust)
- **Interceptores:**
  - `MultiTenantInterceptor` (Core):
    - Inyecta `Authorization: Bearer <access_token>`.
    - Inyecta `X-Company-Id` en **cada petición** (obligatorio para filtrado backend).
  - `ApiInterceptor`: Desenvuelve el objeto `ApiResponse` (`{ status, data, ... }`) y maneja errores HTTP vía `ErrorMapper`.
  - **Manejo de Errores Global:**
    - `401 Unauthorized`: Limpiar storage y redirigir a `/login`.
    - `403 Forbidden`: Mostrar "Access Denied" amigable (token válido, rol insuficiente).
- **Inicialización:** `APP_INITIALIZER` bloquea el arranque de la app hasta validar la sesión contra el backend (`/auth/validate`).
- **RBAC:** El `SidebarComponent` y `NavigationService` filtran menús dinámicamente basados en los roles/permisos del JWT.

## 8. Estructura de Directorios (Blueprint)
- `src/app/core`: Singletons, Interceptores, Guards, Servicios Globales (`AuthService`), Modelos SSOT (`domain.types.ts`, `api.types.ts`).
- `src/app/modules`: Vistas por dominio (`Auth`, `Inventory`, `Production`, `System`).
- `src/app/shared`: Componentes reutilizables (UI Kit), Pipes, Directivas.

## 9. Protocolo de Actualización de Logs (Obligatorio)
Instrucción: Cada vez que realices un cambio, corrección o nueva funcionalidad en el frontend, debes actualizar los archivos de control siguiendo estas reglas estrictas.

### 1. Actualización de CHANGELOG.md
Debes registrar el cambio bajo la fecha actual utilizando el formato Keep a Changelog:
- **Añadido:** Para nuevas señales (Signals), componentes standalone o servicios.
- **Cambiado:** Para actualizaciones en la lógica de interceptores o esquemas de Tailwind.
- **Corregido:** Para bugs en la gestión de estados o ruteo.

### 2. Sincronización en ENGINEERING_LOG.md
Este archivo es para decisiones técnicas profundas. Si cambias la forma en que el `AuthInterceptor` maneja el `X-Company-Id`, debes documentar el "por qué" técnico aquí.

### 3. Verificación de la "Identidad Triple" en la UI
Si modificas una vista de tabla o formulario (Inventario/Producción), confirma en el log que se están mostrando y manejando correctamente los tres IDs:
- **Técnico (UUID):** Para navegación interna.
- **Secuencia (Integer):** Para ordenamiento de auditoría.
- **Folio (String):** Como etiqueta principal para el usuario.

### 4. Validación de Inmutabilidad (UX)
Al modificar componentes de formulario, debes dejar constancia en el log de que has implementado la regla de **No Edición Post-Confirmación**:
- *Ejemplo de log:* "Se aplicó `[readonly]` al formulario `InventoryDetail` cuando el estado del documento es `CONFIRMED`".

## 10. Guardianes de Arquitectura (Strict Rules)
Estas reglas son innegociables para mantener la integridad del sistema:
1.  **Zoneless First:** Queda prohibido el uso de `zone.js`. Toda detección de cambios debe ser vía **Signals** o `markForCheck`.
2.  **Tenant Context:** Verificar que cualquier nuevo servicio que consuma la API pase por el `AuthInterceptor` para llevar el header `X-Company-Id`.
3.  **Inmutabilidad Reactiva:** Todo componente de formulario debe implementar el signal derivado `isEditable` (computed) basado en el estado del documento (`DRAFT` vs `CONFIRMED`).
4.  **Identidad Triple en UI:**
    - **Folio (String):** Etiqueta visible principal.
    - **Secuencia (Int):** Criterio de ordenamiento en tablas.
    - **UUID (ID):** Exclusivo para ruteo y API.

## 11. Especificaciones Módulo WMS (Warehouse Management)
- **Jerarquía de Datos:** Tenant (Company) > Warehouse > Zone > Bin.
- **Contexto de Almacén:**
    - Permitir cambio de almacén sin re-login.
    - Refresco en tiempo real de stocks y precios al cambiar de almacén.
- **Filtro de Precios:** Los precios visualizados deben estar condicionados por la intersección Empresa + Almacén.
- **Dynamic UI:** Formularios de entrada/salida adaptativos según roles (Admin, Picker) del `access_token`.

## 12. Paridad Local vs AWS
- **Environments:** `environment.ts` (Localhost:8000) vs `environment.prod.ts` (AWS ALB).
- **Build Strategy:** Assets compilados para ser servidos por S3 + CloudFront (AWS) o Nginx (On-Premise).

## 13. Manejo de Idiomas (i18n)
- **Resolución de Claves:** Las etiquetas se resuelven mediante la clave recibida del API (`translation_key`).
- **Diccionarios Locales:** El frontend mantiene archivos JSON en `src/assets/locales/` que mapean estas claves.
- **Mecanismo de Fallback:** Si la clave no existe en el diccionario local, se debe mostrar el valor del campo `name` como respaldo (fallback).

## 14. Autenticación de Planta (Shopfloor Login)
Diseñado para entornos industriales donde el uso de teclado es limitado.
- **Activación:** Se conmuta mediante el toggle de modo en el `LoginComponent`.
- **Mecanismos de Captura:**
    - **QR/Barcode:** Integración con `html5-qrcode` para escaneo vía cámara.
    - **RFID (HID Protocol):** `HostListener` global para capturar ráfagas de teclado de lectores RFID externos sin requerir foco en un campo específico.
- **Flujo Técnico:** 
    1. Se captura el `identity_token` (UUID o Código Operario).
    2. Se envía al backend vía `AuthService.login({ identity_token })`.
    3. Si es exitoso, sigue el flujo estándar de selección de empresa o entrada directa si solo tiene un tenant.
- **UX Industrial:** Uso de animaciones de feedback inmediato, fuentes monoespaciadas (`JetBrains Mono`) para datos técnicos y Material Icons.