# 🏭 MES Service (Port 8008)

El **MES Service (Manufacturing Execution System)** es el encargado de orquestar las operaciones en planta, capturando eventos de producción, tiempos de ciclo y eficiencia operativa (OEE).

## 🎯 Responsabilidad
- **Producción**: Registro de eventos de manufactura vinculados a órdenes de trabajo.
- **Eficiencia**: Seguimiento de tiempos activos, paros (Downtime) y labor.
- **Trazabilidad**: Ledger de producción por lote y recurso.

## 🏗️ Arquitectura Técnica
- **Separación de Capas**: Las entidades SQLAlchemy residen en `app/models/`, mientras que las validaciones y contratos Pydantic residen en `app/schemas/`.
- **Identidad**: Hereda de `MultiTenantBase` para asegurar el aislamiento de datos por empresa.
- **Auditoría**: Cumple con `AuditBase` portando `transaction_id` y marcas temporales precisas.

## 🛡️ Gobernanza
- **Zero Trust**: Filtrado mandatorio por `company_id`.
- **Optimistic Locking**: Uso de `version_id` para proteger la concurrencia en cambios de estado de órdenes.
