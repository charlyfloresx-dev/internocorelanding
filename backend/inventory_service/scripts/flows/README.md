# Inventory Service: Industrial Flows (Sentinel Ledger)
Este directorio contiene los flujos de ejecución y scripts de validación para el Ledger de Inventarios Industrial (Fase 83).

## 🚀 Cómo Ejecutar los Flujos
Todos los flujos se ejecutan dentro del contenedor del monolito para garantizar la conectividad con la base de datos y los servicios comunes.

```bash
docker exec -e PYTHONPATH=/app:/app/inventory_service:/app/inventory_service/scripts -w /app/inventory_service/scripts interno-monolith python flows/<nombre_del_flujo>.py
```

---

## 🛠️ Catálogo de Flujos

### 1. Entrada de Mercancía (`flow_1_entry.py`)
- **Documentación:** Registro inicial en dock virtual (`SYS_RECEIVING`).
- **Anexo 24:** Asigna Pedimento Aduanal y habilita trazabilidad FIFO.
- **Endpoint:** `POST /api/v1/documents` (Type: `INVENTORY_IN`).

### 2. Acomodo / Put-Away (`flow_7_putaway.py`)
- **Documentación:** Movimiento de muelle a rack definitivo.
- **Density Guard:** Valida capacidad física antes de mover.
- **Endpoint:** `POST /api/v1/relocate` (From `SYS_RECEIVING`).

### 3. Ajustes de Inventario (`flow_adjustments.py`)
- **Documentación:** Correcciones de stock (merma, hallazgo, daño).
- **Forensic Audit:** Requiere comentarios y códigos de concepto.
- **Endpoint:** `POST /api/v1/transactions` (Type: `ADJUSTMENT`).

### 4. Reubicación Atómica (`flow_relocation.py`)
- **Documentación:** Movimientos internos entre racks/ubicaciones.
- **Atomicidad:** Actualiza `current_units` en la ubicación de origen y destino simultáneamente.
- **Endpoint:** `POST /api/v1/relocate`.

---

## 🏗️ Arquitectura de los Scripts
- `_shared_ids.py`: Resuelve dinámicamente los IDs de Almacenes, Productos y Pedimentos usando los códigos estables del Seed Unificado.
- `__init__.py`: Permite la importación de módulos dentro de la carpeta.

## ⚖️ Reglas de Negocio Globales
1. **Multi-tenancy:** Todos los movimientos están filtrados por `company_id`.
2. **Density Guard:** Bloqueo duro (`ERR_LOCATION_OVERFLOW_UNITS`) si se supera la capacidad del rack.
3. **FIFO Compliance:** Las salidas y reubicaciones consumen saldos de los movimientos más antiguos primero.
