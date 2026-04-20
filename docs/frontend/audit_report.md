# Auditoría Técnica: Frontend Legacy Interno Core

Este reporte documenta los hallazgos de la auditoría técnica realizada sobre el directorio `frontend/legacy` para facilitar la migración a la arquitectura Zero Trust en `temp_future`.

## 1. Clasificación de Hallazgos

### Apto para Migración Directa
*   **Modelos Base**: `ProductRead`, `UOMRead`, `BrandRead` y `CategoryRead` de `catalog.types.ts` tienen una estructura madura y 90% de paridad con `backend/common`.
*   **Enums de Negocio**: `ConceptType` y `DocumentStatus` son idénticos a los requeridos por el backend.
*   **Utilidades de Estilo**: Las configuraciones de Tailwind para `industrial-card` y `input-industrial` pueden migrarse al nuevo `app.css`.

### Requiere Adaptación a Clean Architecture
*   **Lógica de Validación Forense**: El cálculo de `isWeightMismatch` en `InventoryDocumentEditor` es vital pero debe extraerse a una utilidad pura o un validador reactivo antes de incluirse en `movement-form`.
*   **Auth Handshake (T1/T2)**: El flujo ya existe en `AuthService`, pero debe simplificarse eliminando la lógica de restauración manual de `localStorage` en favor de Signals reactivos puros.
*   **Multi-tenant Interceptor**: Debe unificarse el casing del header a `X-Company-ID` y eliminar los logs de consola en producción.

### Deuda Técnica a Eliminar
*   **Simulación Acoplada**: El uso de `ApiSimulationService` dentro de `InventoryService` debe ser eliminado. Las peticiones deben ir directo al `HttpClient`.
*   **Redundancia de CompanyID**: El servicio de inventario pasa el `company_id` explícitamente en cada método. En `temp_future`, esto es responsabilidad exclusiva del `MultiTenantInterceptor`.
*   **Componentes Monolíticos**: El `InventoryDocumentEditorComponent` (~600 líneas) debe dividirse en:
    *   `DocumentHeaderComponent`
    *   `ItemTableComponent` (con lógica de `ExcelNavigation`)
    *   `DocumentFooterComponent`

## 2. Lógica de Inventarios (Domain Discovery)

| Concepto | Regla de Oro Extraída |
| :--- | :--- |
| **Idempotencia** | Se debe generar un `Client-Request-ID` al instanciar el componente para evitar duplicidad por reintentos. |
| **Validación de Masa** | `Tolerance = 0.0001`. Error si `abs((Qty * UOM_Factor) - Weight) > Tolerance`. |
| **Transferencias** | El almacén origen y destino **no pueden ser el mismo** y deben pertenecer al contexto de la empresa activa. |

## 3. Inventario de Modelos (Comparativa)

| Modelo Legacy | Estado en temp_future | Acción |
| :--- | :--- | :--- |
| `User` | Implementado | Sincronizado. |
| `Money` | Implementado | Refactorizado como Value Object. |
| `ProductRead` | Pendiente | Migrar con `AuditBase`. |
| `ExcelNavigation` | Pendiente | Migrar como Directiva compartida. |

## 4. Hardcoded Values Detectados
*   **URLs**: Varias referencias a `http://localhost:8000` en servicios de bajo nivel.
*   **Ubicaciones**: Valor por defecto `'TIJ-ALMACEN-01'` en el editor de documentos.
*   **Roles**: Referencias literales a `'ADMIN'` y `'OPERATOR'` en guardias antiguos.
