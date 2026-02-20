# 🏗️ Blueprint de Construcción: Interno.Core.MES

Este microservicio se rige por la **Regla de Oro de Piso**: *"Si el sistema se cae, la línea no se detiene"*.

---

## 1. Modelado de Datos (Identidad Triple & Multitenancy)

Basado en el **Ledger de Manufactura**, el esquema debe soportar transacciones inmutables.

### Entidades Principales (`models.py`)

| Entidad | Propósito | Campos Clave |
| :--- | :--- | :--- |
| **Resource** | La unidad física (Línea/Célula). | `id`, `code`, `capacity_per_hour`, `is_active`, `company_id`. |
| **ResourceResult** | El "Contenedor de Turno". | `resource_id`, `shift_id`, `start_time`, `end_time`, `status` (OPEN/CLOSED). |
| **ManufacturingLedger** | El libro mayor de piezas. | `resource_result_id`, `sku`, `qty`, `transaction_type` (SCAN/ADJ), `external_folio`. |
| **Downtime** | Registro de paros "arrastrados". | `resource_result_id`, `reason_id`, `start_at`, `closed_at`, `admin_closed_at`, `status`, `escalation_level`. |
| **Labor** | Quién está en la línea. | `resource_result_id`, `user_id`, `clock_in`, `clock_out`, `is_active`. |

---

## 2. El Motor de Escaneo (Parsing Pipeline)

El `ScannerService` no solo recibe texto; debe transformar inputs crudos en transacciones del Ledger usando **Pattern Matching**.

### Lógica del Parser:
- **Individual:** `^ENO[A-Z0-9]+$` $\rightarrow$ $Qty = 1$ (Uso de Serial único).
- **Multi-conteo:** `^(\d+)\*(.+)$` $\rightarrow$ Split por `*`. El primer grupo es $Qty$, el segundo es el $SKU$.
- **Contenedor (Qty Bin):** Si el `CatalogService` indica que el SKU es "Box", el sistema dispara la cantidad estándar definida en el maestro de materiales.

> [!IMPORTANT]
> **Regla de Labor (Labor Guard):**
> Antes de persistir en el Ledger, el servicio debe validar:
> `IF count(Labor.is_active == True) == 0 AND NOT grace_period_active THEN REJECT_SCAN("No hay personal registrado en línea")`.
> - **Periodo de Gracia:** Se permite un margen de 10 minutos durante cambios de turno para evitar bloqueos operativos.
> 
> **Gestión Granular de Descansos (Audit Log Decisión):**
> El tiempo disponible de cada slot de hora en el KPI Dashboard debe ser ajustado por los descansos definidos en el `BreakGroup`. No es un descuento global al final del turno, sino una reducción del tiempo productivo de la hora específica donde ocurre el descanso.

---

## 3. Motor de KPIs (Real-Time Engine)

Cada vez que entra un registro al Ledger o se abre/cierra un Downtime, se recalculan los componentes del OEE en tres niveles de granularidad: **Hora actual**, **Turno completo** y **Tendencia Histórica**.

### Fórmulas Implementadas:
- **Disponibilidad ($A$):**
  $$A = \frac{\text{ShiftDuration} - \text{TotalDowntime}}{\text{ShiftDuration}}$$
- **Eficiencia ($E$):**
  $$E = \frac{\sum (Qty \times StdTime)}{\text{TotalLaborHours}}$$
- **Meta Ajustada:**
  $$\text{MetaActual} = \text{MetaTeórica} \times \left( \frac{\text{LaborActivo}}{\text{LaborPlaneado}} \right)$$

### Métricas de Mantenimiento (NF E 60-182):
- **MTTR (Mean Time To Repair):**
  $$\text{MTTR} = \frac{\sum (\text{ClosedAt} - \text{StartAt})}{\text{Count}(\text{Failures})}$$
- **MTBF (Mean Time Between Failures):**
  $$\text{MTBF} = \frac{\text{Uptime}}{\text{Count}(\text{Failures})}$$

---

## 4. Estrategia de Resiliencia: "The Edge Buffer"

Para el funcionamiento On-Premise, implementaremos un mecanismo de sincronización asíncrona.

- **Identificador Único Local (`local_txn_id`):** El cliente (Frontend/Edge) genera un UUID para cada escaneo.
- **Idempotencia en AWS:** El endpoint `/api/v1/mes/sync` recibirá lotes de transacciones. Si el `local_txn_id` ya existe en el `ManufacturingLedger`, el servidor lo ignora (prevención de duplicados).
- **Estado de Sincronización:** El Ledger tendrá un flag `is_synced: bool`.

---

## 5. Lifecycle del Downtime (Responsabilidad del Issue)

A diferencia de un sistema SCADA simple, el MES de Interno Core rastrea la gestión del paro:

1. **OPEN:** Se detecta el paro. El Andon se pone en **ROJO**.
2. **RESPONDED:** Un técnico escanea su gafete. Inicia el conteo de **MTTR** (Mean Time To Repair).
3. **TECHNICAL_CLOSE:** La máquina vuelve a producir. El impacto en Disponibilidad se detiene.
4. **ADMIN_CLOSE:** El supervisor valida la causa raíz. El registro sale del dashboard de "Issues Pendientes".

---

## 6. Integración de Salida (Eventos)

El MES no es una isla; debe notificar a otros microservicios mediante el `EventPublisher`:

- **Evento `production.declared` (Backflush):**
  - **Por Caja (Batch):** Si el ítem se declara por contenedor.
  - **Unitario (Serie):** Si el ítem tiene número de serie, se genera un movimiento por cada pieza vinculado al documento/folio.
  - **Por Orden:** Si no tiene serie, se puede declarar por cantidad de piezas terminadas.
- **Evento `downtime.exceeded`:** Si un paro > 15 min, el `infra_service` envía un correo/alerta de escalamiento.
- **Evento `label.request`:** Envía el comando ZPL al `infra_service` para imprimir la etiqueta física.

---

## 🛠️ Especificaciones de API (Endpoints MVP)

| Método | Endpoint | Acción |
| :--- | :--- | :--- |
| **POST** | `/resourceresult/open` | Inicia un nuevo turno/día para un recurso. |
| **POST** | `/scan` | Procesa un input de scanner, aplica parser y registra en Ledger. |
| **POST** | `/downtime/open` | Registra el inicio de un paro. |
| **PATCH** | `/downtime/{id}/close` | Cierre técnico por parte del operador/técnico. |
| **PATCH** | `/downtime/{id}/admin-close` | Cierre administrativo con validación de supervisor y causa raíz. |
| **GET** | `/dashboard/oee/{resource_id}` | Retorna el tacómetro de OEE en tiempo real. |
