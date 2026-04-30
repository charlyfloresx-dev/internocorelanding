# 📦 Inventory Service (Puerto 8006)

El **Inventory Service** es el núcleo de control de stock y movimientos de materiales de **Interno Core**. Gestiona el **Kardex industrial**, las transferencias inter-company y la valuación de inventario bajo múltiples métodos de costeo.

---

## 🏗️ Responsabilidades del Dominio

- **Maestro de Productos**: SKU, variantes, unidades de medida, código de barras.
- **Kardex de Movimientos**: Entradas, salidas, ajustes, mermas y devoluciones con trazabilidad completa.
- **Documentos de Inventario**: Órdenes de compra recibidas, traspasos, ajustes de ciclo.
- **Transferencias Inter-Company**: Movimientos entre empresas del mismo `group_id` con validación de custodia.
- **Valuación de Inventario**: Soporte para FIFO, LIFO y Costo Promedio (ERP-ready).
- **Conceptos de Movimiento (TRF-EXT, ADJ, RCV...)**: Catálogo extensible de tipos de transacción.

---

## 🔗 Integraciones

| Servicio | Propósito |
|----------|-----------|
| **Master Data** | Obtiene catálogo de productos y unidades |
| **WMS** | Sincroniza ubicaciones físicas de almacén |
| **MES** | Recibe consumos de materia prima por Orden de Producción |
| **ERP** | Exporta valoración para asientos contables |

---

## ⚙️ Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres-db:5432/inventory_db
CORE_SECRET_KEY=...
CORE_INTERNAL_API_KEY=...
```
