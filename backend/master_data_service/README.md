# 📋 Master Data Service (Puerto 8003)

El **Master Data Service** es el **catálogo centralizado** de Interno Core. Es la única fuente de verdad para productos, unidades de medida, categorías y configuraciones maestras que todos los demás microservicios consumen.

---

## 🏗️ Responsabilidades del Dominio

- **Productos y SKUs**: Catálogo unificado con soporte de variantes (talla, color, material).
- **Unidades de Medida (UoM)**: Conversiones y equivalencias.
- **Categorías y Familias**: Árbol de clasificación de productos para reportes y análisis.
- **Proveedores (Vendors)**: Maestro de proveedores compartido con el ERP.
- **Clientes (Customers)**: Base de clientes para CRM y facturación.
- **Centros de Costo**: Estructura organizacional para imputación contable.
- **Configuración Multi-Tenant**: Configuraciones específicas por `company_id`.

---

## 🔗 Integraciones

| Servicio | Propósito |
|----------|-----------|
| **Inventory** | Consume catálogo de productos y UoM |
| **WMS** | Consume catálogo para recepciones y despachos |
| **MES** | Consume BOM (Bill of Materials) por Orden de Producción |
| **ERP / Currency** | Consume centros de costo y catálogo de monedas |

---

## ⚙️ Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres-db:5432/master_data_db
CORE_SECRET_KEY=...
CORE_INTERNAL_API_KEY=...
```
