# InternoCore: CMMS / Assets Service

Este microservicio es responsable de la gestión de activos industriales, mantenimiento y control de herramientas dentro del ecosistema InternoCore (Computerized Maintenance Management System).

## Arquitectura y Diseño
El servicio está construido siguiendo los principios de **Clean Architecture** y **DDD (Domain-Driven Design)**:

- **WorkOrderBase (Shared Kernel)**: Las órdenes de mantenimiento (`MaintenanceWorkOrder`) heredan del modelo base en `common/models`, compartiendo el esquema unificado con Producción (MES) y Logística (WMS).
- **Weak References**: En lugar de duplicar los registros maestros, entidades como `Tool` almacenan una referencia débil (`inventory_item_id`) al microservicio de inventario, operando como una capa de metadata especializada.
- **Multitenancy Estricta**: Todas las entidades heredan de `MultiTenantBase`, garantizando el aislamiento de datos por `company_id`.

## Dominio
Las entidades principales que componen el CMMS son:
1. **Asset**: Representa maquinaria, vehículos, instalaciones o drones. Soporta jerarquías padre-hijo (ej. Motor de un Vehículo).
2. **MaintenanceWorkOrder**: Especialización de una orden de trabajo dedicada al mantenimiento predictivo, preventivo o correctivo.
3. **MaintenancePlan**: Permite definir rutinas recurrentes sobre los activos.
4. **Tool / ToolAssignment**: Gestión del "Tool Crib", controlando el préstamo y devolución de herramientas.

## Integraciones Inter-Servicio
- **Inventory Service**: 
  - Préstamos temporales (`INTERNAL_LOAN`) vía `POST /checkout`.
  - Salida definitiva de consumibles (`PICK_AND_CONSUME`) vía `POST /consume`.
- **Master Data Service**: Los estados y categorías dinámicas no se queman en código, sino que se resuelven a través de la tabla unificada `Enumeration`.

## Infraestructura y Storage
El servicio gestiona un alto volumen de evidencia fotográfica (Manuales, Reportes de Daños).
- Utiliza una estrategia híbrida S3/Local basada en la variable `STORAGE_TYPE`.
- Cuenta con un validador *pre-flight* (`StorageQuota`) para evitar el abuso del almacenamiento y controlar la facturación por uso dinámico.

## Variables de Entorno Críticas
Además de las variables estándar (`CORE_DB_...`), este servicio requiere:
- `STORAGE_TYPE`: `s3` o `local`
- `CORE_AWS_S3_BUCKET_NAME`: Nombre del bucket S3.
- `QR_SIGNING_SECRET`: Llave HMAC-SHA256 para firmar códigos QR de activos industriales sin sobrecargar tokens JWT.

## Despliegue
Este servicio está diseñado para ser desplegado como un contenedor Docker independiente, montando `common/` en tiempo de ejecución.
`docker-compose up -d cmms-service`

## Roadmap y Fases

### Phase 85: Industrial CMMS Architecture & Enumerations (Mayo 2026)
- Creación fundacional del microservicio `cmms_service`.
- Implementación de la capa de Dominio (Assets, Maintenance Plans, Tools, Work Orders).
- Refactorización de `WorkOrder` a `MaintenanceWorkOrder` heredando del `Shared Kernel` (`WorkOrderBase`).
- Integración de validación de cuotas (`StorageQuota`) para subida de evidencias.
- Adopción de la tabla `Enumeration` (Master Data) para gestión dinámica de enums industriales (`MaintenanceType`, `AssetStatus`, etc.).
- Desacoplamiento de consumibles y herramientas a través de referencias débiles (`inventory_item_id`).

### Fases Pendientes (Deltas)
- **Phase 86+**: Orquestación asíncrona de eventos (Domain Events) para la salida definitiva de consumibles (`POST /consume`) comunicando con el `inventory_service`. Integración de la UI del Kanban unificado.
