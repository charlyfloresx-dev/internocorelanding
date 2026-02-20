# 📦 WMS Service (Warehouse Management System)

## 1. Propósito y Alcance
El microservicio **WMS** es el responsable de gestionar el ciclo de vida físico y operativo de los materiales y productos. Su función principal es garantizar la integridad del stock mediante un modelo de **Libro Mayor (Ledger)**, donde cada cambio en la existencia debe estar respaldado por un documento auditable e inmutable una vez confirmado.

## 2. Pilares de Arquitectura
Este servicio hereda y respeta estrictamente el ADN de InternoCore:
- **Clean Architecture & CQRS:** Separación de comandos de escritura y proyecciones de lectura.
- **ADN InternoCore:** Uso obligatorio de `BaseEntity` (identidad UUID), `AuditBase` (auditoría automática) y `MultiTenantBase` (`company_id` mandatorio).
- **Inmutabilidad y Auditoría:** Los documentos confirmados no se borran ni editan. La cancelación genera un contra-asiento o estado inválido, preservando la trazabilidad.

## 🏛️ Fuente Única de Verdad (SSOT)
- **Modelo Ledger:** Cada movimiento de inventario es una transacción en el "Libro Mayor" de almacén.
- **Multitenancy Enterprise:** Aislamiento profundo de datos por `company_id`.
- **Folios Custom:** Cada empresa gestiona su propia serie de folios operativos.

## 🚀 Conceptos Clave
- **Documento (Aggregate Root):** Define la operación (Compra, Venta, Ajuste, Transferencia).
- **Concepto:** Determina el impacto (Entrada/Salida) y la afectación de stock.
- **Stock Snapshot:** Balance actual por producto/almacén para consultas de alta velocidad.
