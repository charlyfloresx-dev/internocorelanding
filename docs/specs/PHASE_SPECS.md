# 📋 Especificaciones Técnicas de Fases (InternoCore)

Detalle de ejecución para las fases de arquitectura pendientes.

## ✅ Phase 119: inventory_item_variants SSOT Migration + Point-in-Time Document Reprint
**Estado:** ✅ COMPLETO — 2026-05-20
**Objetivo:** Mover `inventory_item_variants` de `inventory_db` a `master_data_db` para habilitar typeahead con JOIN directo y eliminar el anti-patrón `has_variants_table`. Implementar endpoint de reimpresión de documentos con precios al momento de creación (soft-close query).

### Acciones Realizadas
1. **Migración master_data** (`002_add_inventory_item_variants.py`): Tabla `inventory_item_variants` creada en `master_data_db` con guard `_table_exists`.
2. **Migración inventory** (`002_drop_inventory_item_variants.py`): DROP de la tabla en `inventory_db`. Migración one-way (downgrade = `pass`).
3. **ORM + CRUD en master_data_service**: Modelo `ItemVariant`, endpoints GET/POST/DELETE con foto upload y guard `Security(require_scope)`.
4. **Repository Refactor**: `get_products` y `get_product_by_sku` reescritos con ORM LEFT JOIN. Cuando match es por variante: `sku = variant.internal_sku`, nombre enriquecido, precio = `variant.unit_price`.
5. **Proxy HTTP en inventory_service**: 3 endpoints de variantes convertidos a thin proxy `httpx` hacia master_data_service.
6. **Point-in-Time Reprint**: `GET /api/v1/inventory/documents/{folio}` con `MasterDataClient.get_product_price_at_date()`. Soft-close query en `GET /prices/products/{id}/price-at`.
7. **Seed Cleanup**: `seed.py` inventory, `unified_industrial_seed.py` y `flows/seed_variants.py` actualizados para apuntar a `master_data_db`.

### Verificación
```
GET /api/v1/products/?q=MPN-GAR → "Turbocharger Assembly (Garrett MPN-GAR-701)" | 1200 MXN ✅
Code Graph: 0 errores | Ecosystem: 8/8 OK
```

---

## ✅ Phase 118: Polymorphic Department Ticket Assignments & Visibility Filters
**Estado:** ✅ COMPLETO — 2026-05-20
**Objetivo:** Permitir asignación de tickets a departamentos completos (`assigned_department_id`), reseteo inteligente de asignaciones individuales en re-triaje, y visibilidad segmentada para operadores de piso.

### Acciones Realizadas
1. **Modelo `Ticket`** (`ticket.py`): Campo `assigned_department_id` (UUID, index, nullable) añadido.
2. **Schemas Pydantic** (`ticket_dto.py`): `TicketCreate`, `TicketUpdate`, `TicketRead`, `TicketTriage` actualizados.
3. **Triaje inteligente** (`ticket_service.py`): En `REASSIGN` con `assigned_department_id`, limpieza atómica de `assigned_to_id`, `collaborator_id`, `external_contact_id`.
4. **Filtro de visibilidad** (`ticket_repository.py`): `list_by_visibility` acepta `department_id` — operadores ven tickets de su área en `/mine`.
5. **Migración Alembic** (`001_add_assigned_department_id.py`): Columna y índice en `tickets_db`.

---

## ✅ Phase 117: Namespace Scope Matching Security Bridge (Collaborator Auth stabilized)
**Estado:** ✅ COMPLETO — 2026-05-20
**Objetivo:** Resolver el bloqueo 403 Forbidden en el flujo de autorización de colaboradores de planta al consultar endpoints de Datos Maestros (`/warehouses`, `/concepts`) integrando resolución de namespaces de seguridad.

### Acciones Realizadas
1. **Resolución de Namespaces de Seguridad (`dependencies.py`)**: Implementado un comparador inteligente de scopes en `common.security.dependencies.require_scope`. Ahora, un scope granular en la base de datos y token del colaborador (ej: `master_data.product.read`) satisface automáticamente la validación gruesa exigida por el endpoint (ej: `master_data:read`).
2. **Soporte para Permisos `manage`**: El comparador interpreta automáticamente el sufijo `.manage` como un super-permiso que cubre tanto acciones de lectura (`read`) como escritura (`write`).
3. **Remediación de Identidad en Planta (`internal_id` Discrepancy)**: Identificado que el intento fallido de autenticación del operador Carlos Ramírez en el panel web se debió a un desajuste de ID (`003709` vs el valor correcto `003709A` en la base de datos HCM). Al usar la credencial correcta `003709A` o `301`, la autenticación y posterior consumo de catálogos responde con **`200 OK`**.
4. **Limpieza de Archivos**: Eliminados scripts temporales de depuración (`debug_roles.py`, `test_scope_fix.py`) para mantener el espacio de trabajo limpio.
5. **Validación Automatizada**: El validador del ecosistema local (`validate_ecosystem.ps1`) y el generador de gráfico de código (`generate_code_graph.py`) reportan **100% de cumplimiento y 0 errores**.

---

## ✅ Phase 94: Industrial Mobile POS Cockpit Stabilization (Moto g04s)
**Estado:** ✅ COMPLETO — 2026-05-10
**Objetivo:** Finalizar la estabilización industrial del POS móvil sobre el hardware Moto g04s, logrando una interfaz de usuario premium, ultra-rápida y a prueba de fallos con estética minimalista sólida.

### Acciones Realizadas
1. **Industrial Minimalist Aesthetic**: Refactorización completa de la UI eliminando transparencias y glassmorphism. Uso de colores sólidos de alto contraste (#000000, #111111) y radios de 8px/12px para máxima visibilidad en planta.
2. **Hardware Optimization (Moto g04s)**: Forzado de resolución SD (480x640) y throttling de 1.5s en cámara para estabilizar el GPU Mali bajo carga.
3. **Zero-Trust QR Provisioning**: Implementación del flujo de auto-configuración via QR, inyectando identidad de tenant y credenciales sin intervención manual.
4. **Real-time Telemetry**: Integración de `battery_plus` con banners reactivos para estados críticos de energía.
5. **Sanitized Error Governance**: Refactorización de gestión de excepciones de Dio para mostrar mensajes industriales legibles (ej: "CREDENCIALES INVÁLIDAS").

---

## ✅ Phase 78: Master Data Industrialization (SideDrawer Migration)
**Estado:** ✅ COMPLETO — 2026-05-01
**Objetivo:** Finalizar la migración de todos los formularios de catálogos maestros a la arquitectura unificada SideDrawer, asegurando paridad de UI y estabilidad de tipos.

### Acciones Realizadas
1. **Industrial UI Upgrade**: Refactorización de `WarehouseFormComponent` y `ConceptFormComponent` al estándar premium (Glassmorphism, Sticky Footer).
2. **Type Stabilization**: Resolución de errores `DrawerOptions` en `PartnerCatalogComponent` y otros módulos.
3. **Template Repair**: Corrección de errores de sintaxis y visibilidad (`private` vs `public`) en componentes de catálogo.
4. **SideDrawer Integration**: Migración completa de `ConceptCatalogComponent` al servicio reactivo de SideDrawer.

---

## ✅ Phase 76: Escalación Dinámica Multi-tenant & Soporte AI
**Estado:** ✅ COMPLETO — 2026-05-01
**Objetivo:** Implementar la matriz de escalación dinámica, el worker de monitoreo de SLAs y la integración de soporte AI en el Tickets Service.

### Acciones Realizadas
1. **Escalation Matrix**: Implementación de `EscalationRule` con fallback jerárquico por área (`Producción`, `Almacén`, `Soporte`).
2. **EscalationWatcher**: Creación de un worker funcional para el escaneo de SLAs y disparo de eventos de escalación.
3. **AI Support Center**: Integración de lógica de auto-respuesta AI para tickets de tipo `SUPPORT`.
4. **Compliance Audit**: Alcanzado 100% de cumplimiento en el `tickets_service` mediante `bypass_tenant` explícito.

---

## ✅ Phase 75: Tickets Service — Remediación Crítica & Expansión Operacional
**Estado:** ✅ COMPLETO — 2026-05-01
**Objetivo:** Fortalecer la integridad financiera del servicio de tickets y expandir el modelo de dominio para cubrir flujos industriales complejos.

### Acciones Realizadas
1. **Financial Precision**: Migración de `float` a `Numeric(18, 8)` en estimaciones de costo para evitar descuadres.
2. **Inter-service Security (HMAC)**: Implementación de validación HMAC-SHA256 en el endpoint `/internal`.
3. **Audit Standardization**: Integración de `AuditService.track()` en todos los comandos de tickets.
4. **Domain Expansion**: Implementación de 4 nuevos tipos de ticket industriales y jerarquía de escalación self-referential.

---

## ✅ Phase 74: Bloqueo Reactivo por Suscripción & SaaS Integrity
**Estado:** ✅ COMPLETO — 2026-04-30
**Objetivo:** Imponer bloqueos de seguridad reactivos basados en el estado de la suscripción (`PAST_DUE`, `RESTRICTED`, `UNPAID`) en todo el ecosistema.

### Acciones Realizadas
1. **L7 Degradation Engine**: Motor de bloqueo estructurado sincronizado entre `auth`, `subscription` e `inventory`.
2. **JWT Enrichment**: Inyección de claims `status` y `readonly` en el JWT final para hidratación de UI.
3. **Reactive UI Signals**: Implementación de signals `isReadOnly()` y `isUnpaid()` en Angular 19 para bloqueo sensorial.
4. **Code Graph Invariants**: Integración de `SUBSCRIPTION_GUARD_VIOLATION` para detección de fugas de paywall.

---

## ✅ Phase 73: HCM Microservice Migration & Industrial Auth Stabilization
**Estado:** ✅ COMPLETO — 2026-04-30
**Objetivo:** Migrar la lógica de RRHH al microservicio `hcm_service`, estabilizar el handshake de autenticación industrial (RFID/PIN) y unificar la configuración para despliegue en AWS.

### Acciones Realizadas
1. **HCM Extraction**: Creación de `hcm_service` bajo Clean Architecture con base de datos aislada `hcm_db`.
2. **Industrial Auth Restored**: Implementación de la verificación de RFID y PIN en `hcm_service` con soporte para descubrimiento de tenants.
3. **Identity JWT Enrichment**: Inyección de claims operativos (`full_name`, `internal_id`, `is_supervisor`, `wid`) en el token final para eliminar dependencias en el borde.
4. **Config Unified**: Centralización de `CORE_HR_RFID_SALT` y credenciales internas en el `.env` raíz.
5. **AWS Log Compliance**: Eliminación de emojis y caracteres especiales en logs para compatibilidad con CloudWatch.

---

## ✅ Fase 71: Financial & Forensic Traceability (Ledger Stabilization)
**Estado:** ✅ COMPLETO — 2026-04-27
**Objetivo:** Implementar la trazabilidad total del sistema mediante un Ledger Forense inmutable y corregir la valuación monetaria en documentos de inventario.

### Acciones Realizadas
1. **Immutable Forensic Ledger**: Implementado motor de auditoría SQLAlchemy que captura snapshots (Old vs New) en cada transacción.
2. **Audit UI**: Creación de la pantalla de Auditoría Forense con visor JSON de cambios.
3. **Financial Valuation Bridge**: Corrección del mapeo de atributos monetarios para asegurar visibilidad de costos en USD/MXN.
4. **Notification Persistence**: Resolución de bugs en el estado de lectura de notificaciones (Read Status).

---

## ✅ Fase 58: AWS Budget Pivot (ALB to App Runner)
**Estado:** ✅ COMPLETO — 2026-04-20
**Objetivo:** Reducir el costo operativo de ~$30/mes a <$5/mes mediante la eliminación del ALB y la transición a AWS App Runner y CloudFront con OAC.

### Acciones Realizadas
1. **Infraestructura Zero-Cost**: Eliminación de ALB, Target Groups e IPs públicas vinculadas.
2. **App Runner Migration**: Preparado `apprunner.yaml` para despliegue de bajo costo del `auth_service`.
3. **Frontend OAC**: Despliegue en S3 privado con CloudFront OAC para mayor seguridad y menor costo de transferencia.

---

## ✅ Fase 57: GIS Integration & Tijuana Cadastral Mapping
**Estado:** ✅ COMPLETO — 2026-04-18
**Objetivo:** Integrar validación catastral oficial y scraping de propietarios legales del IMPLAN Tijuana.

### Acciones Realizadas
1. **ArcGis Provider**: Implementado cliente para consultas espaciales al servidor oficial de Tijuana.
2. **Legal Owner Scraping**: Implementado motor de scraping para el portal de pagos de Tijuana con manejo de sesiones ASP.NET.
3. **Address ValueObject**: Evolución del modelo de dirección para incluir metadata catastral binacional.

---

## ✅ Fase 55: Industrial AWS Deployment (auth_service)
**Estado:** ✅ COMPLETO — 2026-04-17
**Objetivo:** Desplegar el primer microservicio (Auth) a AWS ECS Fargate con persistencia real en RDS y balanceo de carga ALB.

### Acciones Realizadas
1. **ECS Fargate Provisioning**: Creación de clúster, task definitions y servicios con balanceo nativo.
2. **Secret Management**: Implementación de inyección de secretos vía Shell-CLI para garantizar reactividad de Pydantic.
3. **Frontend Production Build**: Corrección de reemplazo de environments en Angular para apuntar al ALB.
4. **CDN Orchestration**: Despliegue en S3 con invalidación de CloudFront automática.

---

## ✅ Fase 44: Infrastructure Convergence & Media Assets
+**Estado:** ✅ COMPLETO — Sincronizado con v4.3.0
+**Objetivo:** Centralizar la configuración AWS (SSM), unificar el almacenamiento multi-tenant (S3) y habilitar la gestión de activos visuales para RH e Inventarios.
+
+### Acciones Realizadas
+1. **Desacoplamiento de Almacenamiento**:
+   - Implementado `StorageProvider` en `common` con soporte para S3 (Boto3) y almacenamiento Local.
+   - Generación automática de URLs pre-firmadas para acceso seguro a activos desde el frontend.
+2. **Estrategia SSM Low-Cost**:
+   - Implementado script de migración deduplicada `/interno-core/global/` vs `/interno-core/{service}/`.
+   - Configurado LocalStack (v1.4.0) para emular Parameter Store sin costos de licenciamiento Pro.
+3. **RH Media Integration**:
+   - Actualizado modelo `Collaborator` con `photo_path`.
+   - Implementado upload opcional con jerarquía segregada: `{company_id}/hr/collaborators/{colab_id}.jpg`.
+4. **Frontend Asset Normalization**:
+   - Creado `imageInterceptor` para inyectar dinámicamente el dominio de assets (`environment.assetsUrl`).
+   - Implementado Pipe `secureImage` para manejo de placeholders y rutas relativas.
+5. **Gobernanza de Raíz**:
+   - Limpieza de scripts operativos a `backend/tests/integration/infrastructure/`.
+
+### Validación
+- [x] Los archivos subidos a LocalStack se guardan con el prefijo de la empresa (Isolation).
+- [x] El API de RH retorna una URL pre-firmada válida que el navegador puede renderizar.
+- [x] Los parámetros globales de base de datos se leen correctamente desde el Parameter Store simulado.
+- [x] El interceptor de Angular normaliza rutas relativas a `http://momentos.com` en desarrollo.
+
 ---

## ✅ Fase 48: Industrial Integrity & Performance (Registry Cache)
**Estado:** ✅ COMPLETO — Sincronizado con v4.1.0
**Objetivo:** Eliminar la latencia de escaneo para catálogos masivos y blindar la capacidad física del almacén mediante validación volumétrica activa.

### Acciones Realizadas
1. **The Density Guard (Control de Capacidad)**:
   - Implementado modelo `InventoryLocation` para definir capacidad física (`max_capacity`) por Rack/Bin.
   - Añadida validación en tiempo real en `InventoryTransactionService` que bloquea movimientos si exceden la capacidad.
   - Ocupación calculada dinámicamente mediante la suma de saldos FIFO (`available_quantity`) en la ubicación.
2. **Registry Cache ($O(1)$ Lookup)**:
   - Implementado `InventoryRegistryService` en Angular que hidrata el catálogo completo en memoria al inicio.
   - Eliminada la latencia de red en validaciones de SKU durante el proceso de Put-away y Entrada Manual.
3. **UX Industrial en Handheld**:
   - Integración de barra de densidad visual (Semáforo Verde/Ámbar/Rojo) en el flujo de re-ubicación.
   - Implementación de feedback auditivo preventivo (Beep de 110Hz) para alertas de desbordamiento de rack.
4. **Higiene de Datos (Legacy Port)**:
   - Re-implementación del método `getNumber` (rescatado de .NET legacy) para limpiar caracteres basura de escaneos de códigos de barras (ej. saltos de línea o sufijos de hardware).
5. **Estabilización de Tipos**: Resolución de errores de compilación TS en servicios core y estandarización de mappers de respuesta.

### Validación
- [x] El handheld bloquea instantáneamente el paso a Step 3 si la ubicación destino está llena.
- [x] La búsqueda de 10,000+ SKUs en modo manual se resuelve en <5ms (Caché local).
- [x] El sistema permite registrar ubicaciones con capacidad configurada o ilimitada (default).
- [x] Los caracteres "basura" del escáner son eliminados automáticamente sin intervención del operador.

---

## ✅ Fase 49: Cycle Count & Audit Sheets (Auditoría Total)
**Estado:** ✅ COMPLETO — Sincronizado con v4.2.0
**Objetivo:** Cerrar el ciclo de integridad permitiendo reconciliaciones físicas ciegas (Blind Count) y exportación de hojas de auditoría que respeten la trazabilidad del Anexo 24.

### Acciones Realizadas
1. **Módulo Cycle Count (Conteo Ciego)**:
   - Implementado `CycleCountComponent` con flujo industrial de 3 pasos:
     - **Paso 1**: Escaneo y bloqueo de ubicación (RACK-X-XX).
     - **Paso 2**: Conteo ciego — el operador escanea SKUs sin ver cantidades teóricas. Solo ve "Items contados: N".
     - **Paso 3**: Análisis de discrepancias con tabla comparativa (Teórico vs Contado vs Diferencia).
   - Validación de SKU instantánea contra `InventoryRegistryService` ($O(1)$).
   - Ajuste de cantidad por item con controles +/- en pantalla.
2. **Exportación de Auditoría**:
   - Endpoint `GET /warehouses/{id}/audit-export` que genera CSV con encoding UTF-8-BOM.
   - Columnas: Ubicación, SKU, Descripción, Pedimento, Cantidad Teórica, Físico_Check (columna vacía).
   - Botón "Hoja de Conteo" integrado en `StockLevelComponent` con beep de confirmación (880Hz).
3. **Seguridad de Ajustes (Supervisor Override)**:
   - Discrepancias mayores al 5% requieren rol `supervisor` o `admin` para confirmar.
   - Banner de "Autorización Requerida" bloquea el botón de confirmación para operadores estándar.
4. **UX Industrial**:
   - Acceso directo desde Dashboard (card "Auditoría Spot") y menú lateral (Inventarios + WMS).
   - Hotkeys: F2 (Finalizar/Confirmar), Escape (Reiniciar flujo).
   - Estadísticas de sesión (Conteos Hoy / Discrepancias) persistidas en localStorage.
   - `sanitizeScannerInput()` — higiene de datos de escáner portado del legacy .NET.

### Validación
- [x] El operador no puede ver cantidades teóricas durante el conteo (Modo Ciego).
- [x] Los SKUs se validan contra el Registry Cache antes de añadirlos al conteo.
- [x] Las discrepancias >5% bloquean la confirmación para usuarios sin rol supervisor.
- [x] La hoja de auditoría CSV se descarga con encoding BOM para compatibilidad Excel.
- [x] La ruta `/inventory/cycle-count` es accesible desde el sidebar y el dashboard.

---


## ✅ Fase 46: Industrial Logistics Scalability & Anexo 24 Compliance
**Estado:** ✅ COMPLETO — Sincronizado con v4.0.0
**Objetivo:** Garantizar la estabilidad y el rendimiento del núcleo logístico ante volúmenes de datos industriales (10,000+ SKUs) y cumplir con la normativa de auditoría Anexo 24.

### Acciones Realizadas
1. **Paginación Servidor-Nativa**: Implementación de `limit` y `offset` en el motor de agregación de saldos aduanales (Inventory Service).
2. **Búsqueda Industrial (Search-First)**: Desarrollo de filtros globales por SKU, Pedimento y Nombre de Producto integrados en la capa de persistencia SQLAlchemy.
3. **Módulo de Put-Away (Handheld)**:
    - Desarrollo de interfaz para re-ubicación de mercancía (de `DOCK-01` a RACK definitivo).
    - Flujo "3 Scans": Origen (Pallet/Lote) -> Destino (Ubicación Rack) -> Confirm [F2].
    - Retroalimentación: Industrial Beep (200Hz) en errores de validación.
4. **Resiliencia de Sesión**:
    - Parche defensivo en `auth-service` para evitar bloqueos por atributos faltantes (`full_name`).
    - Motor de "Resilient Parsing" en Frontend para manejar respuestas de microservicios con doble envoltorio.
5. **Optimización de Interfaz (Handheld UX)**:
    - Rediseño de `StockLevelComponent` para soportar navegación paginada.
    - Implementación de **Debounce Técnico (300ms)** en buscadores para optimizar escaneo secuencial en Handhelds.
    - Implementación de indicadores visuales de riesgo IEPS/Compliance basados en Aging de pedimentos.
6. **Arquitectura de Respuesta**: Estandarización de `ApiResponse` para incluir `total_count` y metadatos de paginación global.

### Validación
- [x] El sistema carga datasets de prueba masivos sin degradación de memoria en el navegador.
- [x] El buscador localiza registros específicos instantáneamente entre miles de filas.
- [x] El flujo de Put-Away sincroniza correctamente los cambios de ubicación en el ledger inmutable.
- [x] La sesión del operador persiste tras refrescar el navegador (F5) en el handheld.
- [x] El reporte de saldos refleja correctamente el saldo residual por pedimento (FIFO compliance).

---
**Estado:** âœ… COMPLETO â€” Sincronizado con v2.0.0
**Objetivo:** Implementar la infraestructura tÃ©cnica para transferencias entre empresas distintas (binacionales MX <-> US), garantizando el aislamiento de datos y la detecciÃ³n automÃ¡tica de necesidades fiscales.

### Acciones Realizadas
1. **SeparaciÃ³n de Entidades Legales**: RefactorizaciÃ³n de seeds para crear empresas independientes (Logistics MX y US) con `company_id` Ãºnicos.
2. **GeolocalizaciÃ³n TÃ©cnica**: InclusiÃ³n de `country_code` en los modelos de `Company` y `Warehouse` para eliminar ambigÃ¼edades geogrÃ¡ficas.
3. **LÃ³gica de Destino Inteligente**: ImplementaciÃ³n de bloqueo "Definido por Receptor" para transferencias externas (Inter-company).
4. **Filtrado Multi-inquilino**: RestricciÃ³n estricta de almacenes de origen basados en el contexto de la sesiÃ³n activa (`X-Company-ID`).
5. **Estabilidad del Dashboard**: CorrecciÃ³n de bucles de polling y creaciÃ³n de un Circuit Breaker para operaciÃ³n offline.

### ValidaciÃ³n
- [x] Los almacenes de EE.UU. (Otay/San Diego) aparecen correctamente como "Externos" al estar en una entidad legal diferente.
- [x] El sistema detecta cruces de frontera y activa la visualizaciÃ³n de requisitos de Pedimento.
- [x] Los selectores de origen respetan el aislamiento de datos entre MX y US.
- [x] El Dashboard de telemetrÃ­a es estable y no genera sobrecarga de red.

---

## âœ… Fase 33.3: Mission Control Refinement & Gatekeeper Implementation
**Estado:** âœ… COMPLETO â€” Sincronizado con UI v1.8.1
**Objetivo:** Eliminar simulaciones, implementar Gatekeepers de configuraciÃ³n y habilitar visibilidad de documentos espejo.

### Acciones
1. **Gatekeeper de PreparaciÃ³n**: Implementar `GetCompanyInventoryReadinessHandler` que bloquea el Dashboard si faltan catÃ¡logos (UOM, Productos, Precios).
2. **Switch de Datos Reales**: Migrar `InventoryService` (Frontend) a `HttpClient` puro conectado al Ledger Inmutable.
3. **Visibilidad de TrÃ¡nsito**: Implementar seÃ±ales computadas para `physicalWarehouses` y `transitWarehouses` en la UI.
4. **Mirror Records**: Integrar badges "Espejo ICT" para documentos entrantes de otras compaÃ±Ã­as (`ICT-IN-*`).

### ValidaciÃ³n
- [x] El Dashboard muestra error/alerta clara si la empresa no tiene UOMs o Productos cargados.
- [x] Los folios `ICT-IN` muestran el badge pulsante de "Espejo".
- [x] Las transacciones se guardan en el ledger real (Base de datos PostgreSQL).

---

## âœ… Fase 44: Industrial Pricing & B2B Agreements
**Estado:** âœ… COMPLETO â€” Sincronizado con v3.0.0
**Objetivo:** Evolucionar el maestro de precios a una arquitectura multitenant inmutable (Point-in-Time) de 11 niveles (0-10) y habilitar contratos comerciales B2B (Price Agreements) con importador masivo industrial.

### Acciones Realizadas
1. **Inmutabilidad Soft-Close**: RedefiniciÃ³n del motor de persistencia. Los precios no se editan; se sellan (`valid_until = now()`) y se inserta una nueva versiÃ³n.
2. **JerarquÃ­a Binacional**: Soporte para Niveles 1-10 (Venta) y Nivel 0 (Costo de ReposiciÃ³n/Compra) reservado estricto.
3. **Price Agreements (B2B)**: ImplementaciÃ³n del modelo de acuerdos vinculados a Partners (Clientes/Proveedores), con precedencia sobre listas generales.
4. **Control Tower Import**: Dashboard masivo en Angular 18 con Drag & Drop, validaciÃ³n atÃ³mica y reporte forense de errores.
5. **Alembic Inmutable**: Despliegue de esquema versionado para `price_agreements` sin pÃ©rdida de integridad en logs existentes.

### ValidaciÃ³n
- [x] El importador masivo rechaza SKUs inexistentes y reporta la lÃ­nea exacta del CSV.
- [x] Una actualizaciÃ³n de precio crea un nuevo registro con UUID distinto, manteniendo el anterior como historial.
- [x] El nivel 0 se identifica correctamente como costo de compra en los generadores de plantillas.
- [x] El refresco automÃ¡tico del catÃ¡logo tras cerrar el importador funciona correctamente (Signals sync).

---

## ðŸ“� Fase 33.5: Price Evolution & Fiscal Catalogs (Legacy Reference)
**Estado:** âœ… FUSIONADO EN FASE 44

---

## âœ… Fase 33.3: Seed Refactoring & Docker Compatibility
**Estado:** âœ… COMPLETO
**Objetivo:** Estandarizar el patrÃ³n de resoluciÃ³n de paths en todos los scripts de seeds para compatibilidad Docker/Local.

### Acciones Realizadas
1. **PatrÃ³n unificado**: `if os.getcwd() not in sys.path: sys.path.insert(0, os.getcwd())`.
2. **Scripts corregidos**: `inventory_service/scripts/seed.py`, `verify_seed.py`, `reset_db.py`.
3. **ValidaciÃ³n**: Los 3 seeds (auth, master_data, inventory) corren sin errores dentro de sus contenedores.

---

## âœ… Fase 19: Antigravity Auditor Mode
**Estado:** âœ… COMPLETO
**Objetivo:** Verificar la integridad de los datos maestros tras el Seed.

### Acciones
1. Ejecutar `python -m app.scripts.integrity_scan`.
2. Generar reporte `integrity_scan_report.md`.

### ValidaciÃ³n (Criterios de Ã‰xito)
- âœ… NingÃºn `company_id` es NULL en tablas heredadas de `MultiTenantBase`.
- âœ… Todos los campos `status` coinciden con los enums en `common/enums.py`.

---

## ðŸŒ� Fase 20: SincronizaciÃ³n On-Premise (Edge Buffer)
**Estado:** â�³ Pendiente
**Objetivo:** Permitir que el sistema funcione On-Premise y se sincronice con AWS.

### Acciones
1. **Endpoint de SincronizaciÃ³n:** Crear `POST /api/v1/sync` en los microservicios.
2. **Idempotencia:** Implementar lÃ³gica para evitar duplicados si se reintenta la sincronizaciÃ³n (Batch Idempotency).

### ValidaciÃ³n
- âœ… Los datos creados en el ambiente On-Premise aparecen en AWS tras la ejecuciÃ³n del script de sync.

---

## ðŸ”’ Fase 21: Final Security Audit
**Estado:** â�³ Pendiente
**Objetivo:** Garantizar que un inquilino (Tenant) no vea datos de otro.

### Acciones
1. **AuditorÃ­a de Repositorios:** Revisar `common/repository.py` para asegurar que todo query incluya automÃ¡ticamente el filtro `.filter(Model.company_id == current_company_id)`.
2. **Aislamiento de DTOs:** Validar que los esquemas de respuesta no expongan campos sensibles o de otros tenants.

---

## ðŸ�›ï¸� Fase 25: Master Data Consolidation & Audit Pro
**Estado:** âœ… COMPLETO
**Objetivo:** Unificar datos maestros con legado .NET e implementar auditorÃ­a inmutable distribuida.

### Acciones
1. **Modelado Core:** Integrar campos de `Item` legacy y banderas forenses en `Product`.
2. **Infraestructura Warehouse:** Desbloquear gestiÃ³n de almacenes y conceptos de movimiento multitenant.
3. **Audit Engine:** Implementar listeners de SQLAlchemy para snapshots automÃ¡ticos de transacciones.
4. **Resiliencia:** Patchear `inventory_service` con `curl` y preparar trazabilidad por lotes.

### ValidaciÃ³n
- âœ… Los logs de auditorÃ­a capturan el 100% de los cambios en Master Data.
- âœ… El seeder puebla correctamente UOMs y conversiones globales.

---

## ðŸ›¡ï¸� Fase 28: God Mode & Privileged Access
**Estado:** âœ… COMPLETO
**Objetivo:** Implementar herramientas de rescate tÃ©cnico sin violar el aislamiento multitenant.

### Acciones
1. **Bypass de Tenant:** Implementar flag en `BaseRepository`.
2. **Volatilidad UI:** Configurar Angular Signals para la llave maestra.
3. **AuditorÃ­a Forense:** Taggear logs con `[GOD_MODE]` y registrar `trace_id`.

---

## ðŸ“¦ Fase 30: Inter-Company Orchestration
**Estado:** âœ… COMPLETO
**Objetivo:** Implementar transferencias de inventario entre tenants vinculadas y seguras.

### Acciones
1. **Comandos Duales:** Desarrollar comandos de Egreso e Ingreso atÃ³micos.
2. **VinculaciÃ³n Forense:** Implementar `TransactionPairId` en modelos de movimiento.
3. **Consistencia Distribuida:** Configurar Sagas y Outbox para notificaciones inter-tenant.

---

## ðŸ“ˆ Fase 31: Mission Control & Dashboard Stabilization
**Estado:** âœ… COMPLETO
**Objetivo:** Proveer visibilidad total del inventario en tiempo real con datos de alta fidelidad.

### Acciones
1. **SincronizaciÃ³n UTC:** Asegurar que todo el pipeline de datos (Seed -> DB -> Handler) use UTC para evitar desfases en grÃ¡ficas.
2. **Seeding de Alta Fidelidad:** Generar volÃºmenes densos de datos para validar el performance del Dashboard y visualizaciÃ³n de tendencias.
3. **Alertas CrÃ­ticas:** Configurar umbrales de seguridad para disparar indicadores visuales (Rojo/Amarillo) en la UI.
4. **Metadata Sync:** Vincular nombres de productos y almacenes entre servicios para coherencia visual.

### ValidaciÃ³n
- âœ… Las grÃ¡ficas horarias muestran actividad continua sin huecos inesperados.
- âœ… Los indicadores de variaciÃ³n porcentual reflejan cambios reales en el stock del Ãºltimo ciclo.
- âœ… La trazabilidad `X-Trace-ID` es visible en los logs de los endpoints del dashboard.

---

## âœ… Fase 34: ICT Infrastructure & Real Data Seeding
**Estado:** âœ… COMPLETO
**Objetivo:** Estabilizar la infraestructura de transferencias inter-company con datos reales, auditorÃ­a matemÃ¡tica y acciones de ciclo de vida en UI.

### Acciones
1. **AuditorÃ­a de WAC**: Crear `verify_wac_integrity.py` para validar la precisiÃ³n decimal (4 dÃ­gitos) del costo promedio tras ingresos ICT.
2. **Seeding Real**: Implementar `seed_ict_real.py` para poblar ciclos de transferencia entre empresas reales (TIJ-SDY) en Postgres.
3. **Acciones de Lifecycle**: Desarrollar los botones y modales de "Confirmar RecepciÃ³n" y "Reclamar Stock" en el Dashboard de Inventarios.
4. **Trazabilidad de Referencia**: Exponer `external_reference` en los DTOs de documentos para vincular lÃ³gicamente ICTs con movimientos de almacÃ©n.

### ValidaciÃ³n
- [x] El script de auditorÃ­a confirma un WAC de $20.00 exactos tras la recepciÃ³n de prueba.
- [x] La UI permite completar el flujo de recepciÃ³n manual ajustando cantidades.
- [x] Se previene el "Reclamo" de stock si la transferencia ya fue entregada (regla de integridad).

---

## ðŸ�—ï¸� Fase 35: Legacy Integration & Industrial Resilience
**Estado:** âœ… COMPLETO
**Objetivo:** Auditar e integrar la lÃ³gica crÃ­tica del legado frontend en la nueva arquitectura, garantizando resiliencia industrial y monitoreo de salud.

### Acciones
1. **AuditorÃ­a del Legado**: AnÃ¡lisis tÃ©cnico de `frontend_legacy` y creaciÃ³n de `docs/legacy_audit.md` con estrategia de 4 fases.
2. **Contexto de Identidad**: DefiniciÃ³n de la "Identidad Triple" (UUID/Sequence/Folio) y reglas SSOT en `FRONTEND_CONTEXT.md`.
3. **Nervio Central de Salud**: ImplementaciÃ³n de `SystemHealthService` para monitoreo reactivo de microservicios (Auth, Inventory, MasterData).
4. **MÃ³dulo ProducciÃ³n (MES)**: MigraciÃ³n de `ProductionService` con KPIs reactivos (OEE, Downtime) y creaciÃ³n del `ProductionDashboardComponent` con estÃ©tica Neon-Industrial.
5. **Bloqueo de Escritura**: ImplementaciÃ³n de lÃ³gica `isReadOnly` global basada en el estado de salud del clÃºster y estatus de suscripciÃ³n.

### ValidaciÃ³n
- [x] El Dashboard de ProducciÃ³n muestra KPIs reales y grÃ¡ficas horarias sincronizadas.
- [x] El Badge de salud en el layout principal cambia dinÃ¡micamente entre Online/Degraded/Offline.
- [x] El sistema bloquea acciones de escritura si los servicios crÃ­ticos no responden.
- [x] Las rutas de producciÃ³n estÃ¡n integradas en el menÃº lateral y protegidas por RBAC.

---

## ðŸŒŽ Fase 36: Frontend Internationalization (i18n) & Localization
**Estado:** âœ… COMPLETO
**Objetivo:** Reemplazar todas las cadenas de texto estÃ¡ticas en espaÃ±ol con un sistema de traducciÃ³n dinÃ¡mico basado en claves, garantizando paridad total inglÃ©s/espaÃ±ol y estandarizaciÃ³n de mensajes del sistema.

### Acciones
1. **Infraestructura i18n**: Implementar `TranslationService` (Signal-based) y `TranslatePipe` (pure: false) para actualizaciones de UI instantÃ¡neas.
2. **LocalizaciÃ³n de MÃ³dulos**: Migrar a claves de traducciÃ³n en:
   - `AuthModule`: Inicio de sesiÃ³n (Admin/Planta), escÃ¡ner QR/RFID y recuperaciÃ³n de contraseÃ±a.
   - `InventoryDashboard`: MÃ©tricas, grÃ¡ficas y historial de movimientos.
   - `ProductCatalog`: Listado maestro, acciones y filtros.
   - `UserManagement`: AdministraciÃ³n de roles, matriz de permisos e invitaciones.
   - `MainLayout`: NavegaciÃ³n, selector de contexto y temas.
3. **EstandarizaciÃ³n de Mensajes**: Centralizar mensajes de Ã©xito, error y avisos de sistema en `en.json` y `es.json`.
4. **Resiliencia de CompilaciÃ³n**: Depurar plantillas de Angular para eliminar errores de sintaxis (bloqueadores de `esbuild`) durante la migraciÃ³n masiva.

### ValidaciÃ³n
- [x] El selector de idioma en el header cambia toda la interfaz sin recargar la pÃ¡gina.
- [x] Las notificaciones (Toasts) muestran mensajes dinÃ¡micos basados en el idioma activo.
- [x] No hay cadenas de texto en espaÃ±ol "quemadas" (hardcoded) en los archivos `.ts` o `.html` de los mÃ³dulos migrados.
- [x] El bundle de producciÃ³n se genera sin errores de etiquetas duplicadas o mal cerradas.
- [x] Soporte para fallbacks: El sistema muestra texto por defecto si una clave de traducciÃ³n no existe en el JSON.

---

## âœ… Fase 37: Dashboard Operational Hardening & UI/UX Polish
**Estado:** âœ… COMPLETO â€” Sincronizado con UI v1.9.0
**Objetivo:** Estabilizar la visualizaciÃ³n de datos en el Mission Control, mejorar la resiliencia ante fallos de red y refinar la estÃ©tica minimalista para dispositivos de alta densidad (iPad Pro).

### Acciones
1. **Minimalismo en Header**: RediseÃ±o del selector de tenant a un estilo "Catalog-style" (transparente, sin bordes) con elevaciÃ³n de z-index (`z-20`) para evitar oclusiones.
2. **Resiliencia Industrial**: ImplementaciÃ³n de `Promise.allSettled()` en la carga de catÃ¡logos y uso de cabeceras `X-Silent-Error` para suprimir alertas de "Fallo CrÃ­tico" en errores no fatales de metadatos (CategorÃ­as/Marcas).
3. **Mapeo de IconografÃ­a**: ActualizaciÃ³n del motor de renderizado de iconos para soportar mÃºltiples convenciones de nombres del backend (`IN/OUT`, `ENTRY/EXIT`, `ENTRADA/SALIDA`).
4. **OptimizaciÃ³n Visual**: CalibraciÃ³n de tamaÃ±os de fuente de tÃ­tulos ("Mission Control") para garantizar simetrÃ­a visual en tablets y pantallas de alta resoluciÃ³n.
5. **Flujos de Salida Premium**: ImplementaciÃ³n de navegaciÃ³n directa al Mission Control desde la pantalla de Ã©xito de movimientos, cerrando el ciclo operativo.

### ValidaciÃ³n
- [x] El selector de empresa es minimalista y funcional, sin interferencias de capas (z-index).
- [x] Un error 500 en la carga de categorÃ­as ya no bloquea el dashboard ni muestra alertas alarmantes de SRE.
- [x] Los movimientos generados en tiempo real muestran iconos direccionales correctos (flechas verde/rojo).
- [x] La navegaciÃ³n post-confirmaciÃ³n devuelve al usuario al panel principal de forma fluida y profesional.

---

## ðŸ“¸ Fase 42: Event Kiosk Ecosystem & Universal Engine
**Estado:** âœ… COMPLETO
**Objetivo:** Desplegar un ecosistema especializado para eventos locales (Mini-PCs) con procesamiento de imagen industrial y pagos hÃ­bridos.

### Acciones
1. **Universal Engine**: MigraciÃ³n del flujo "Boda" a un quÃ³rum de $N$ aprobadores configurables.
2. **Identidad FÃ­sica**: ImplementaciÃ³n de `device_id` para garantizar integridad en los votos de moderaciÃ³n.
3. **Hardware Integration**: Daemon de impresiÃ³n asÃ­ncrono para CUPS con recorte proporcional y marcas de agua vÃ­a Pillow.
4. **Resiliencia Offline**: Servidor DNS interno (`dns_server.py`) y automatizaciÃ³n del puerto 53 para operaciÃ³n sin internet.
5. **Seguridad SSL**: ImplementaciÃ³n de certificados locales para el dominio `momentos.com`.

### ValidaciÃ³n
- [x] Flujo E2E validado: Upload -> Match -> Checkout -> Print Spool.
- [x] Los dispositivos mÃ³viles cargan las fotos vÃ­a HTTPS local (Secure Proxy).
- [x] El Cash Ledger rastrea fondo inicial, gastos y discrepancias de cierre.

---

## ðŸ�›ï¸� Fase 43: Root Governance & Zero Pollution Enforcement
**Estado:** âœ… COMPLETO
**Objetivo:** Estandarizar la estructura del repositorio eliminando la contaminaciÃ³n de archivos en la raÃ­z y consolidando directorios tÃ©cnicos.

### Acciones
1. **IdentificaciÃ³n de Clutter**: LocalizaciÃ³n de scripts, logs y reportes fuera de lugar.
2. **MigraciÃ³n de Archivos**:
   - `/scripts`: Scripts operativos (.ps1, .py, .sh).
   - `/logs`: Reportes de auditorÃ­a y archivos de salida (.txt).
   - `/docs/architecture`: DocumentaciÃ³n maestra y bitÃ¡coras arquitectÃ³nicas.
   - `/docker`: OrquestaciÃ³n y archivos compose adicionales.
3. **RefactorizaciÃ³n de Rutas**: ActualizaciÃ³n de `run_kiosk.ps1` y `modo_offline.ps1` para operar desde la nueva estructura.
4. **DocumentaciÃ³n de Arranque**: CreaciÃ³n de la `GuÃ­a de Arranque Local` (Modo ERP vs Kiosk).

### ValidaciÃ³n
- [x] La raÃ­z contiene < 10 archivos maestros.
- [x] Los scripts de automatizaciÃ³n funcionan correctamente con rutas relativas a `/scripts`.
- [x] El Master Index apunta a las nuevas ubicaciones.
---

## ? Fase 45: Industrial Identity & Discovery-First Auth
**Estado:** ? COMPLETO — Sincronizado con v3.1.0
**Objetivo:** Estabilizar la identidad física para entornos industriales mediante IDs alfanuméricos, validación Regex por Tenant y un flujo de login por descubrimiento ('Backend-Driven') que elimina la exposición de IDs de empresa.

### Acciones Realizadas
1. **Migración Alfanumérica**: Conversión de internal_id de Integer a String(50) en todo el ecosistema (DB, SQLAlchemy, Pydantic). Soporta formatos industriales como 003709A.
2. **Handshake de Descubrimiento**: Implementación de login dinámico. El sistema busca RFID/PIN globalmente y devuelve un selection_token si el usuario pertenece a múltiples empresas, delegando la selección al usuario.
3. **Estandarización AWS (CORE_)**: Homologación de todas las variables de entorno bajo el prefijo CORE_ en 11 microservicios, facilitando la integración con AWS Secrets Manager.
4. **Middleware Unificado**: Fusión de la seguridad de tenant y técnica en el InternoCoreGlobalMiddleware (común), eliminando redundancias y centralizando la gestión de rutas públicas.
5. **Validación por Patrón**: Implementación de HrTenantConfig para aplicar Regex específicos por empresa (ej. 6 dígitos + 1 letra para Enterprise).

### Validación
- [x] El sistema acepta y valida IDs como 003709A sin errores de tipo de dato.
- [x] El login de Kiosk funciona sin enviar company_id desde el frontend (Descubrimiento puro).
- [x] Los escaneos con caracteres invisibles (\n, \r) son limpiados automáticamente vía .strip().
- [x] El middleware centralizado bloquea accesos cruzados entre tenants de forma efectiva.

---

## 🛡 Phase 45.1: Pricing Stabilization & B2B Immortality
**Estado:** ✅ COMPLETED
**Objetivo:** Estabilizar el motor de precios B2B y garantizar la integridad referencial de los acuerdos comerciales mediante inmutabilidad absoluta y validación de tipos complejos.

### Acciones Realizadas
1. **Inmutabilidad B2B**: Implementación del patrón "Soft-Close & Insert" en acuerdos de precios. Cada cambio genera una nueva versión con trazabilidad completa.
2. **Mapeo de Tipos Complejos**: Resolución de colisiones Pydantic/SQLAlchemy para objetos de valor `Money` mediante mappers explícitos en la capa API.
3. **Tabbed Pricing UI**: Refactorización del dashboard de precios en el frontend para soportar Listas de Precios vs Acuerdos B2B en una interfaz unificada y resiliente.
4. **Resiliencia de Divisas**: Corrección de inyección de dependencias en `currency-service` que causaba errores 500 al consultar tasas de cambio activas.
5. **Testing Automatizado**: Incorporación de suite de pruebas de integración para el ciclo de vida de precios y acuerdos.

### Validación
- [x] El modal de precios carga sin errores de validación de esquemas (500 fix).
- [x] Los acuerdos B2B se guardan con historial completo (valid_until automático).
- [x] La interfaz muestra alertas amarillas dinámicas para datos productivos faltantes.
- [x] Los endpoints de moneda responden correctamente con los mercados de divisas sincronizados.
