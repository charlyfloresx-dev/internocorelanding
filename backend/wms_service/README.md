# 🏬 WMS Service — Warehouse Management System (Puerto 8007)

El **WMS Service** gestiona la **logística física** de los almacenes de Interno Core. Controla ubicaciones, recepciones, despachos y la trazabilidad de materiales en el espacio físico, siendo el complemento espacial del Inventory Service.

---

## 🏗️ Responsabilidades del Dominio

- **Maestro de Almacenes**: Definición de bodegas, zonas, pasillos, racks y ubicaciones.
- **Recepciones (GR)**: Goods Receipt vinculado a Órdenes de Compra del ERP.
- **Despachos (GI)**: Goods Issue para órdenes de producción, ventas y transferencias.
- **Gestión de Lotes (Batches)**: Trazabilidad FIFO por lote/número de serie.
- **Picking y Putaway**: Lógica de asignación de ubicación óptima.
- **Inventario Cíclico**: Conteos periódicos y ajustes de diferencias.

---

## 🔗 Integraciones

| Servicio | Propósito |
|----------|-----------|
| **Inventory** | Sincroniza saldos contables con la realidad física |
| **MES** | Confirma disponibilidad antes de consumo en producción |
| **Master Data** | Catálogo de productos y unidades de medida |

---

## ⚙️ Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres-db:5432/wms_db
CORE_SECRET_KEY=...
CORE_INTERNAL_API_KEY=...
```
