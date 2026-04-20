# 🏛️ ARCHITECTURAL LOG

Registro de decisiones y evolución de la arquitectura de Interno Core.

### Phase 43: Root Governance & Event Kiosk Engine
- **Status:** ✅ Completed (2026-04-13)
- **Description:** Implementación del estándar **Zero Root Pollution** mediante la reubicación de scripts operativos a `scripts/` y logs a `logs/`. Migración de la documentación de arquitectura a `docs/architecture/`. Consolidación del motor universal de eventos con soporte para Quórum de N-Aprobadores e integración de MinIO local para baja latencia On-Premise.

---

### Phase 18: Master Data Service Alignment
- **Status:** ✅ Completed
- **Description:** Refactorización de `common`, ajuste de Dockerfiles, consolidación de modelos y saneamiento estructural. Ejecución de plan de remediación para eliminar "Root Pollution" y consolidar la SSOT de las entidades.

### Phase 19: Antigravity Auditor Mode
- **Status:** ✅ Completed
- **Description:** Auditoría técnica completa sobre `master-data-service`. Saneamiento de estructura de archivos y eliminación de riesgos de importación. Los modelos y servicios cumplen con la lógica de negocio híbrida.

### Phase 19.1: Product Catalogs Implementation
- **Status:** ✅ Completed
- **Description:** Implementación completa de los módulos de Categorías y Marcas en `master_data_service`, siguiendo el patrón de catálogos híbridos.

### Phase 19.2: Master Data Standardization Protocol
- **Status:** ✅ Completed
- **Description:** Definición de reglas estrictas para `master-data-service`: Herencia de `common`, soporte de `company_id` nullable (Híbrido), y estandarización de respuestas `ApiResponse`.

### Phase 20: On-Premise Sync (Edge Buffer)
- **Status:** ⏳ Pending
- **Description:** Implementación de endpoint `POST /sync` y lógica de idempotencia para sincronización Edge-to-Cloud.

### Phase 21: Final Security Audit
- **Status:** ⏳ Pending
- **Description:** Auditoría de filtrado automático por `company_id` en repositorios y aislamiento de DTOs.

### Phase 10.5 & 10.6: Notification Resilience & Templating
- **Status:** ✅ Completed
- **Description:** Centralization of notification delivery logic using a Factory pattern for providers. Implementation of a Jinja2 templating system for standardized, multi-tenant HTML communication. Integrated Resend as the primary email carrier.

### Phase 25.3: Master Data Consolidation & Audit Pro
- **Status:** ✅ Completed
- **Description:** Consolidación de modelos de Master Data (Product, Warehouse, MovementConcept, UOMConversion) basándose en análisis de legado .NET. Implementación de motor de auditoría inmutable mediante event listeners de SQLAlchemy. Reparación de salud de contenedores y seeding crítico de datos operativos.