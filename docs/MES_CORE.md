# 🏭 MES CORE (Manufacturing Execution System)

## Master Data Integration

El módulo MES ya no mantiene definiciones locales de Productos o Unidades de Medida.

### Hierarchy Update
- **Source of Truth:** `master_data_service`
- **Domain Models:** Ahora se utilizan los modelos definidos en `common.domain` y `common.enums`.
- **Inheritance:** Todas las entidades de producción (`Result`, `Downtime`, `Labor`) heredan de `MultiTenantBase` para garantizar el aislamiento por `company_id`.

### Integrity Checks
El sistema de auditoría (`integrity_scan.py`) valida que no existan registros huérfanos de compañía y que los estados de producción coincidan con los Enums globales.