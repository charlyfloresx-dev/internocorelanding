# 💰 Currency Service (Puerto 8008)

El **Currency Service** es el **motor de tipos de cambio** de Interno Core. Integra la API oficial del Banco de México (Banxico) para obtener cotizaciones en tiempo real y las distribuye al ERP, Inventory y demás servicios financieros.

---

## 🏗️ Responsabilidades del Dominio

- **Tipos de Cambio en Tiempo Real**: Conexión directa con la API de Banxico (Token oficial).
- **Monedas Soportadas**: MXN, USD, EUR y extensible a otras divisas.
- **Caché de Cotizaciones**: Almacenamiento en DB para evitar exceso de llamadas a la API externa.
- **Cotización Histórica**: Registro histórico de tipos de cambio para reportes y auditoría financiera.
- **Conversión de Valores**: Endpoint utilitario para conversión entre monedas en tiempo real.

---

## 🔗 Integraciones

| Servicio | Propósito |
|----------|-----------|
| **ERP / Finanzas** | Obtiene tipo de cambio para asientos contables en USD |
| **Inventory** | Valúa inventarios en moneda local y extranjera |
| **Subscription** | Convierte precios de suscripción según moneda del cliente |

---

## ⚙️ Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres-db:5432/currency_db
CORE_BANXICO_TOKEN=...
CORE_SECRET_KEY=...
```
