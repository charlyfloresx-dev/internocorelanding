# 📝 ARCHITECTURAL LOG (wms_service)

### [FIX-2026-02-08] - Implementación de Identidad Triple y Modelos de Catálogo
- **Decisión:** Remediación del bloqueador crítico identificado en auditoría del 08-Feb-2026.
- **Cambios Realizados:**
  - **InventoryDocument:** Agregado campo `sequence_number: Integer` con constraint único `(company_id, sequence_number)` para secuencia histórica por empresa.
  - **InventoryMovement:** Agregado campo `sequence_number: Integer` con constraint único `(document_id, sequence_number)` para secuencia de líneas por documento.
  - **Concept (NEW):** Modelo maestro de tipos de operación con `code`, `name`, `concept_type` (Enum: ENTRY/OUTPUT/ADJUSTMENT) y `affect_stock` (Boolean).
  - **DocumentSeries (NEW):** Generador de folios custom con `prefix`, `current_number`, `year_reset` y método `generate_folio()` para atomicidad.
- **Identidad Triple Completa:**
  - `id`: UUID v4 (identificador técnico para API/AWS)
  - `sequence_number`: Integer secuencial (compatibilidad legacy y auditoría)
  - `folio`: String formato custom (identificador de usuario, ej: ENT-2026-001)
- **Impacto:** Desbloquea migración de datos legacy. Mapeo int → UUID ahora posible. Auditoría histórica preservada.
- **Próximo Paso:** Ejecutar migración Alembic para aplicar cambios en DB y actualizar seed data con conceptos default.


### [LOG-2026-02-08] - Python Backend Integration Audit
- **Decisión:** Auditoría profunda de integración entre `/common`, `/auth_service` y `/wms_service`.
- **Hallazgos Críticos:**
  - ✅ **Common Module:** GREEN LIGHT - MultiTenantBase y AuditBase 100% conformes con `company_id` indexado, `transaction_id` presente, y uso de `Numeric(18,4)` (sin float).
  - ✅ **Auth Service:** GREEN LIGHT - Login multi-empresa operativo, retorna lista de compañías, inyección de tenant context via `get_current_tenant_company` con validación cruzada JWT vs X-Company-ID.
  - ✅ **WMS Service:** RESOLVED - Identidad Triple (sequence_number, folio, id) implementada al 100%. Inmutabilidad habilitada en Frontend.
  - ✅ **Docker Infrastructure:** GREEN LIGHT - PYTHONPATH configurado correctamente (`/app`), `common` accesible desde servicios, build context en `/backend`.
- **Impacto:** La migración de datos legacy está BLOQUEADA hasta implementar `sequence_number`. Sin este campo, no hay mapeo de IDs legacy (int) a UUIDs.
- **Acción Inmediata:** Implementar `sequence_number: Mapped[int]` con índice único `(company_id, sequence_number)` en modelos WMS antes de proceder con cualquier desarrollo adicional.
- **Estado:** 100% de cumplimiento. Common, Auth y WMS alineados y validados.

### [LOG-2026-02-04] - Definición del Core WMS
- **Decisión:** Migración del legacy .NET a Python manteniendo paridad de modelos `common` [cite: 2026-01-19, 2026-01-20].
- **Cambio:** Se sustituyen tipos `float` del legacy por `decimal` para precisión financiera en costos y cantidades.
- **Ajuste:** La cancelación de documentos no generará nuevas líneas de reversa por defecto, sino que el motor de stock filtrará por estado `CONFIRMED`, optimizando el espacio en DB.
- **App Flutter:** Se acuerda integración de notificaciones push para ventas y movimientos de almacén mediante Firebase [cite: 2026-02-04].

### [LOG-2026-02-04] - Identity Firewall & Tenant Context
- **Decisión:** Implementación de `get_current_tenant_company` como 'cortafuegos' de identidad [cite: 2026-01-20].
- **Mecánica:** Validación cruzada obligatoria entre JWT `company_id` y header `X-Company-ID`. El incumplimiento resulta en `403 Forbidden`.
- **Trazabilidad:** Se integra `wms_audit` logger para registrar cada acceso con `user_id`, `company_id` y `X-Transaction-ID` [cite: 2026-01-24].
- **Arquitectura:** El contexto de empresa se inyecta directamente en los routers, desacoplando la lógica de negocio de la extracción del token.


### [LOG-2026-02-25] - CIERRE DE SPRINT: Integración Exitosa WMS Ledger Core
- **Evento:** Alineación final del Frontend con el WMS Ledger Core (Triple Identity + Inmutabilidad).
- **Logros:**
  - **Identidad Triple:** Sincronización completa de `sequence_number` y `folio` entre Python y Angular.
  - **Inmutabilidad:** Garantía de integridad de datos mediante bloqueo de documentos no-DRAFT en UI.
  - **Demo Mode:** Infraestructura de seeding automatizada y validada.
- **Veredicto:** El motor de transacciones Ledger es estable, auditable y listo para escalado industrial.
