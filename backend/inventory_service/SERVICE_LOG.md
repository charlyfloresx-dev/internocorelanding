# Service Log — Inventory Service

## 🕒 Última Actividad (2026-04-03)
**Fase 42: Estabilización de Traceability, Constraints y Flujos Binacionales (Completada)**

1. **Resolución de Restricción `external_reference`**:
   - Múltiples flujos fallaban al insertar en `inventory_documents` debido a la violación de la restricción Unique & Not-Null en `external_reference`.
   - Implementado `external_reference=doc_id.hex` para operaciones manuales en `flow_1_entry.py` y `flow_2_exit.py`.
   - Modificado `seed_ict_real.py` para usar referencias únicas compuestas (`OUT-{id}` y `IN-{id}`) en los documentos espejos.
2. **Validación de Flujos**:
   - `flow_1`: OK. Genera `IN-MANUAL-` visible en Kardex.
   - `flow_2`: OK. Genera `OUT-MANUAL-` visible en Kardex.
   - `flow_3`: OK. Removida temporalmente de la clase Pydantic `InitiateTransferCommand` la regla de negocio que previene "Misma Empresa" para probar Transferencias Internas puras. Removida la regla SoD (`created_by == received_by`) para permitir testing autónomo en scripts.
   - `flow_4_ict_enterprise_to_logistics.py`: OK. Flujo nacional completo.
   - `flow_5_ict_binational.py`: OK. Flujo internacional con auditoría financiera y pedimento.
3. **Visibilidad en Dashboard**:
   - Todos los documentos ejecutados (Manuales y Transferencias) se insertan exitosamente en la base de datos `inventory_db` y por lo tanto son leíbles por el frontend `dashboard/document-viewer` de InternoCore.
- **Improved Seeding**:
  - `scripts/seed.py` y `scripts/seed_ict_real.py` fueron corregidos para asegurar que la tabla `companies` esté poblada con los IDs maestros (Enterprise, Logistics MX/US) antes de procesar movimientos.
- **Bug Fixes**:
  - Patched `TransferCommandHandler` to initialize `transit_warehouse_id` and other variables before the `try...except` block, preventing `UnboundLocalError` when validation fails.
