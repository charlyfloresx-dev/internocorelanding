# 🏭 MES Service — Manufacturing Execution System (Puerto 8005)

El **MES Service** es el **cerebro de la ejecución en piso** de Interno Core. Orquesta las Órdenes de Producción, controla la eficiencia de las líneas, consume recursos del WMS/Inventory y valida capacidades del HCM antes de iniciar cualquier operación.

---

## 🏗️ Responsabilidades del Dominio

- **Órdenes de Producción (WO)**: Creación, asignación, ejecución y cierre con trazabilidad completa.
- **Gestión de Líneas**: Definición de estaciones de trabajo y asignación de operadores.
- **OEE (Overall Equipment Effectiveness)**: Cálculo en tiempo real de Disponibilidad, Rendimiento y Calidad.
- **Consumo de Materiales**: Integración con Inventory Service para el Kardex de materia prima.
- **Validación de Capacidades**: Consulta al HCM (`/internal/validate-access`) antes de iniciar una WO de alto riesgo.
- **OperationTime**: Registro de tiempos de operación y set-up por proceso industrial (migrando del sistema legacy .NET).

---

## 🔗 Integraciones

| Servicio | Dirección | Propósito |
|----------|-----------|-----------|
| **HCM** | MES → HCM | Valida SkillLevel del operador antes de iniciar WO |
| **Inventory** | MES → Inv. | Reserva y consume materia prima |
| **WMS** | MES → WMS | Confirma disponibilidad física en almacén |
| **CMMS** | MES ↔ CMMS | Reporta paros no programados, solicita mantenimiento |
| **Notification** | MES → Notif. | Alertas de retrasos o paros de línea |

---

## ⚙️ Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres-db:5432/mes_db
CORE_SECRET_KEY=...
POSTGRES_SERVER=postgres-db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=mes_db
```
