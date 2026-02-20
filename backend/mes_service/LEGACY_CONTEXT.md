# Legacy Context: Interno.Core.MES

Este documento consolida la lógica de negocio y los modelos de datos de los proyectos legacy .NET (`Interno.Production`, `Interno.DJO`, `Interno.Outset`) para servir de referencia al microservicio `mes_service`.

---

## 1. Modelos de Datos Core (`Interno.Production.Models`)

### A. Result (`Result.cs`)
Es la cabecera de la producción por turno/recurso.
- **Campos Clave:** `Date`, `ResourceCode`, `ShiftId`, `Actual` (Producción), `OEE`, `Availability`, `Efficiency`, `FirstPassYield`.
- **Lógica de Tiempos:**
  - `AvailableTime`: Tiempo total del turno - descansos.
  - `ProductiveTime`: Tiempo real de producción (calculado).
  - `OperativeTime`: Paros programados + Paros operativos + Tiempo de producción.

### B. Downtime (`Downtime.cs`)
Registro de paros.
- **Campos Clave:** `IssueId`, `ResultId`, `Status` (OPEN, CLOSED), `Created` (Start), `ClosedDate` (End).
- **MTTR:** Se calcula como `ClosedDate - Created`.

### C. Labor (`Labor.cs`)
Rastreo de personal en línea.
- **Campos Clave:** `EmployeeNumber`, `ResourceCode`, `Start`, `End`, `ResultId`.
- **Transcurred:** Tiempo activo del empleado en la línea.

### D. Resource (`Resource.cs`)
Definición de línea/celda. Hereda de `Warehouse`.
- **Campos Clave:** `Code`, `Name`, `Capacity`, `BreakGroupId`.

---

## 2. Lógica de Negocio y KPIs (Audit de `ResultController.cs`)

### Motor de Gráfica (OEE/HourByHour)
El método `GetGraphic` es el corazón del cálculo de eficiencia horaria:
1. **Inicialización:** Genera slots de horas basados en el `Shift`. Soporta cambios de turno (e.g. Turno 2 que cruza medianoche).
2. **Descuento de Descansos (`Breaks`):** La lógica granular (líneas 148-163) ajusta cada slot de hora:
   - Si una hora coincide con el inicio de un descanso, el tiempo disponible de esa hora disminuye.
   - Si una hora coincide con el fin, el tiempo disponible se recalcula basándose en lo que resta para completar la hora.
3. **Cálculo de Metas:** Distribuye la `PlanQty` entre las horas disponibles usando el `StandardTime` (`OperationTime.SetTime`). Si no hay `OperationTime`, hace una división equitativa.
4. **Validaciones de Plan:** `PostResult` exige campos de fechas críticas: `ShippingDate`, `WHSDate`, `SMKTDate`.

### Integración DJO/Procurement (`ProcurementController.cs`)
- **STBL (Shortage to Build):** Cruza la producción declarada con el inventario de componentes (BOM Explosion) para identificar qué detiene la producción de un ensamble.
- **OTD (On-Time Delivery):** Mide el cumplimiento de la fecha `PromisedDate` contra la fecha real de recibo en Ledger.
- **Interno.Outset:** Contiene una implementación simplificada de `HourByHour.cs`, sugiriendo una evolución o versión ligera para terminales de borde (Edge).

---

## 4. Observaciones y Recomendaciones para `mes_service`
1. **Identidad Triple:** El legacy usa `ResourceCode` y `ResultId`. En el nuevo servicio, esto se mapeará a `resource_id` y `resource_result_id` (UUIDs).
2. **Cálculos en Python:** La lógica de `GetGraphic` debe portarse al `KPIService` de Python, optimizando las consultas de agregación.
3. **Resiliencia:** El legacy no parece tener un "Buffer" explícito; la nueva implementación con `local_txn_id` es una mejora sustancial sobre el modelo anterior.

---

## 🏁 Estado de la Implementación (2026-02-14)
- [x] **Mapeo de Modelos:** El 100% de los campos críticos de `Result`, `Downtime`, `Labor` y `Resource` han sido portados a SQLAlchemy con el ADNc de Interno Core.
- [x] **Motor de KPIs:** La lógica de `GetGraphic` ha sido implementada en `KPIService.get_resource_graphic`.
- [x] **Aislamiento Multi-Empresa:** Validado mediante la herencia del `common.models.base_models.MultiTenantBase`.
