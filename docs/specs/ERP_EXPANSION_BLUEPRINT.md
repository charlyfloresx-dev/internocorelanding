# 🚀 Arquitectura de Cierre ERP: The Missing Services Blueprint

> **Status:** Blueprint / Especificaciones Técnicas
> **Last Updated:** 2026-04-13
> **Contexto:** Expansión End-to-End posterior a Phase 44 (Pricing & Contracts).

Para que Interno Core funcione End-to-End como un ERP industrial, se proyectan tres nodos clave. La ventaja es que, al haber completado la Phase 44, los datos maestros (partners, precios) y logísticos (inventory_movements) ya están estandarizados de manera inmutable bajo el `MultiTenantBase` y la unidad monetaria `Money` (Numeric 18,4).

---

## 1. 🛒 Sales Service (Order-to-Cash / O2C)
**Puerto de asignación:** `8009` | **Base de Datos:** `sales_db`

Este servicio es el encargado de orquestar la demanda del cliente y garantizar que respete las reglas comerciales (`PriceAgreements`) blindadas en la Fase 44.

### Modelos Clave (Heredan de `MultiTenantBase` y `AuditBase`):
*   `SalesOrder`: Entidad principal (Folio, Cliente/Partner, Estado).
*   `SalesOrderLine`: Detalle de productos (`product_id`, cantidad, `unit_price`, `currency`).
*   `SalesInvoice`: Emisión contable y fiscal (Timbrado SAT / Border HTS).

### Interacciones Críticas (El Handshake):
*   **Pricing Engine Sync**: Debe consultar a *Master Data* para obtener el precio Point-in-Time garantizado por la Fase 44. Ningún vendedor puede editar el `unit_price` si el flag `allow_price_override` del producto es falso.
*   **Inventory Handshake**: Cuando una `SalesOrder` pasa a estado `CONFIRMED`, dispara un draft al *WMS Service* (Outbound Picking). Hasta que el WMS no lo marca como embarcado, el stock en *Inventory Service* se considera "Reservado" (`reserved_quantity`), no restado de `available_quantity`.

---

## 2. 🏗️ Procurement Service (Procure-to-Pay / P2P)
**Puerto de asignación:** `8010` | **Base de Datos:** `procurement_db`

La puerta de entrada financiera del inventario. Aquí se cristalizan los costos y se alimenta el Nivel 0 (Compra) de Inmutabilidad.

### Modelos Clave:
*   `PurchaseOrder` (PO): Negociación con proveedores.
*   `PurchaseOrderLine`: Detalle con el costo temporal esperado.
*   `LandedCostAllocation`: **(Crucial)** Distribución pro-rata de fletes, seguros y aduanas sobre el costo base de las líneas recibidas, para calcular el verdadero costo del inventario.

### Interacciones Críticas:
*   Debe leer el *Nivel 0* de Master Data para sugerir el precio de compra histórico más reciente.
*   Cuando el *WMS* recibe la mercancía contra una PO, Procurement gatilla el recalculo del **CPP (Costo Promedio Ponderado)** en el Inventory, generando un nuevo precio de nivel 0 inmutable en Master Data si el costo varió.

---

## 3. ⚖️ Finance Service (General Ledger / Record-to-Report)
**Puerto de asignación:** `8011` | **Base de Datos:** `finance_db`

El cerebro del ERP. Toma transacciones operativas y las convierte en Partida Doble (Cargos y Abonos), respetando el `Money VO` (Numeric 18,4).

### Modelos Clave:
*   `Account`: Catálogo de Cuentas (Chart of Accounts) estandarizado por el SAT / US GAAP.
*   `JournalEntry`: Póliza contable.
*   `JournalEntryLine`: Debe (Debit) y Haber (Credit). Sumatoria siempre exacta a cero.
*   `CostCenter`: Centro de costos para segregación industrial (Línea de Producción A vs. Línea B).

### Interacciones Críticas:
*   **Suscripción Transaccional (Event-Driven)**: El Finance Service NO es invocado vía HTTP REST en el flujo de usuario. Debe consumir eventos del bus (ej. `wms.movement.confirmed` o `sales.order.invoiced`) y transformarlos silenciosamente en pólizas contables según las reglas de mapeo configuradas para el Tenant.
*   **Margin Dashboard**: Este servicio funge de backend proveyendo la vista consolidada de rentabilidad, cruzando los Costos (Nivel 0) con el Revenue de Pólizas o Facturas.

---

## 🎯 Plan de Acción Inmediato Siguiente
1.  **Dashboard de Márgenes Temprano**: Aprovechando la Phase 44, se puede cruzar la lista de Nivel 0 (Compra) y Niveles 1-10 (Venta) de `master_data_db` para alertar rentabilidad negativa antes de construir el Finance Service.
2.  **Order-to-Cash y Handshake**: Construir el Sales Service (`8009`) para materializar el impacto de la arquitectura de inmutabilidad en los pedidos de clientes y enlazarlo con las salidas del WMS (Outbounds).
