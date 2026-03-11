# 🏛️ ARCHITECTURAL LOG

Registro de decisiones y evolución de la arquitectura de Interno Core.

---

### Phase 18: Master Data Service Alignment
- **Status:** ✅ Completed
- **Description:** Refactorización de `common`, ajuste de Dockerfiles, consolidación de modelos y saneamiento estructural. Ejecución de plan de remediación para eliminar "Root Pollution" y consolidar la SSOT de las entidades.

### Phase 19: Antigravity Auditor Mode
- **Status:** 🔄 In Progress
- **Description:** Ejecución de auditoría técnica sobre `master-data-service`. Se identificaron violaciones críticas de estructura de archivos ("Root Pollution") y riesgos de importación en scripts. Los modelos y servicios cumplen con la lógica de negocio híbrida.

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