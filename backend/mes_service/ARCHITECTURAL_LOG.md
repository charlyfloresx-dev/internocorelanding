# Architectural Log - mes_service

## AL-001: Estándar de Microservicio (FastAPI) - 2026-02-14
**Estado:** Aceptado
**Contexto:** Necesitamos inicializar el servicio MES siguiendo el `MANIFEST.md`.
**Decisión:** Se adopta FastAPI con SQLAlchemy 2.0 y soporte para Multitenancy.
**Consecuencia:** Estructura de carpetas estandarizada y herencia obligatoria de `MultiTenantBase`.

## AL-002: Identidad Triple en Ledger - 2026-02-14
**Estado:** Aceptado
**Contexto:** El MES requiere trazabilidad total de cada pieza.
**Decisión:** Cada escaneo se registra como una transacción inmutable en el `ManufacturingLedger` con ID de recurso, ID de resultado de producción y SKU.

## AL-003: Alineación con Common DNA - 2026-02-14
**Estado:** Aceptado
**Contexto:** Evitar duplicidad de middleware y lógica de base.
**Decisión:** Uso de `MultiTenantBase` de `common` y `InternoCoreGlobalMiddleware`. Los modelos ahora incluyen Optimistic Locking automático.

## AL-005: Jerarquía de Turnos Dinámicos - 2026-02-14
**Estado:** Aceptado
**Contexto:** La operación requiere horarios distintos por línea y soporte para medianoche.
**Decisión:** Implementar `ShiftService` con resolución jerárquica: `Recurso > Facility > Empresa`. 
- **Midnight Support:** Lógica circular en `ShiftService.is_time_in_shift`.
- **Automatización:** Los `ResourceResult` heredan el turno activo al momento de su creación.

## AL-006: Motor de Escalación Síncrono - 2026-02-14
**Estado:** Aceptado
**Contexto:** Los paros de máquina deben ser atendidos en < 5 min.
**Decisión:** Un Background Worker (`worker.py`) basado en `APScheduler` evalúa cada 5 min los paros `OPEN`.
- **Consumo:** Utiliza `async_session_local` para estabilidad en procesos largos.
- **Escalación:** Incrementa `escalation_level` y registra `last_escalation_at` para evitar spam.

## AL-007: Resiliencia (No-Stop Policy) - 2026-02-14
**Estado:** Aceptado
**Contexto:** No detener la producción por falta de sincronización o material.
**Decisión:** `ScannerService` integra `WMSClient` asíncrono.
- **Informativo:** Si el WMS reporta falta de stock, devuelve un `warning` pero persiste la transacción en el Ledger.
- **Trazabilidad:** Inclusión de `sequence_number` autoincremental por turno para Identidad Triple.

## AL-008: KPIs de Mantenimiento (NF E 60-182) - 2026-02-14
**Estado:** Aceptado
**Decisión:** Implementar MTTR (Mean Time To Repair) y MTBF (Mean Time Between Failures) en `KPIService`.
- **MTTR:** Basado en la diferencia entre `start_at` y `closed_at` de `Downtime`.
- **MTBF:** Relación entre `Uptime` (Total - Paros) y el conteo de fallas del periodo.

## AL-009: Sincronización Híbrida (Edge Buffer) - 2026-02-14
**Estado:** Aceptado
**Contexto:** Sincronizar instancias On-Premise con la Nube Multi-tenant.
**Decisión:** Crear endpoint `POST /mes/sync` para procesamiento masivo de transacciones.
- **Idempotencia:** De-duplicación obligatoria mediante `local_txn_id`.
- **Backfilling:** Inserción con `created_at` original del Edge para preservar la veracidad de los KPIs históricos.
- **Tenant Isolation:** Validación cruzada de `company_id` en cada transacción del lote.
