# Service Log — Inventory Service

## 🕒 Última Actividad (2026-04-15)
**Integridad Industrial y "The Density Guard" (Completada)**

1. **The Density Guard (Control de Capacidad)**:
   - Implementado modelo `InventoryLocation` para definir capacidad física (`max_capacity`) por Rack/Bin.
   - Añadida validación en tiempo real en `InventoryTransactionService` que bloquea movimientos si exceden la capacidad (Ocupación = Suma de saldos FIFO).
   - Expuesto endpoint `/locations/{code}/density` para monitoreo preventivo desde Handhelds.
2. **Optimización de Búsqueda (Registry Cache)**:
   - Creado endpoint `/search/products/quick-catalog` para hidratación instantánea del frontend ($O(1)$ lookup).
   - Implementada limpieza de escaneos (método `getNumber` rescatado de legacy) para eliminar sufijos basura.
3. **Módulo de Put-Away (Handheld)**:
   - Desarrollada interfaz industrial para re-ubicación de mercancía (DOCK -> RACK).
   - Implementado flujo de "3 Scans" con retroalimentación auditiva (Beeps) y validación de ubicación.
   - Vinculación automática de `pedimento_id` para asegurar el cumplimiento del Anexo 24 en traslados internos.
4. **Estabilización de Reportes Anexo 24**:
   - Refactorizada la capa de respuesta de `/customs/balances` para evitar el doble envoltorio (double-wrap) de `ApiResponse`.

## 🕒 Última Actividad (2026-04-15)
**Escalabilidad Industrial y Cumplimiento Anexo 24 (Completada)**

1. **Paginación y Búsqueda en Auditoría**:
   - Modificado `IInventoryRepository` y `SQLAlchemyInventoryRepository` para soportar `limit`, `offset` y `query`.
   - Implementado cálculo de `total_count` mediante subconsultas para reportes de cumplimiento.
   - Optimizado el endpoint `/balances` para retornar metadata de paginación industrial.
2. **Estabilización de Dominio**:
   - Unificadas implementaciones de `get_customs_balances` eliminando shims y placeholders.
   - Reforzada la lógica de cálculo de días de vencimiento (Risk Aging) con soporte para zonas horarias.
**Enriquecimiento Forense de Documentos (Completada)**

1. **Resolución de Nombres de Terceros (Partners)**:
   - Modificado `InventoryTransactionService` y el endpoint `/documents` para realizar búsquedas activas en `master-data-service` durante la creación del documento.
   - Si el campo `external_entity` contiene un UUID, el servicio ahora lo resuelve a un nombre comercial (ej. "COCA-COLA FEMSA MÉXICO") antes de persistirlo.
   - Implementado patrón de resiliencia: Si el servicio externo falla, se mantiene el ID original para evitar pérdida de datos.
2. **Infraestructura de comunicación (IMasterDataClient)**:
   - Agregada capacidad `get_partner` al cliente interno para facilitar la resolución de nombres en otros módulos.
   - Reforzada la resolución de nombres de almacenes físicos.


## 🕒 Última Actividad (2026-04-09)
**Depuración de Flujos y Enriquecimiento de Catálogos (Completada)**

1. **Correcciones en Flujos de Scripts**:
   - **`flow_2_exit.py`**: Corregido el signo de la cantidad a negativo (`-20.0`) para asegurar que el balance de stock se descuente correctamente en el ledger.
   - **`flow_3_internal_transfer.py`**: Implementada la Segregación de Funciones (SoD). El flujo ahora utiliza un segundo usuario (`USER_B_ID`) para la recepción, cumpliendo con la validación de seguridad `ERR_SELF_RECEIPT_NOT_ALLOWED` re-activada en el handler.
2. **Carga de Datos Maestros (Seeding)**:
   - Creado `scripts/flows/seed_variants.py`.
   - Registrados 5 Números de Parte industriales (ECM, Turbo, Brake Disc, Injectors, Dampers) con un total de 15 variantes (Bosch, Denso, Garrett, Brembo, etc.).
   - Asegurada la compatibilidad con `MultiTenantBase` y el esquema de auditoría de `inventory_db`.
3. **Validación Técnica**:
   - Ejecución exitosa de los 6 flujos tras las correcciones.
   - Validación de conectividad local a la DB a través del puerto mapeado `5433`.
   - Confirmada la persistencia de movimientos (`inventory_movements`) y documentos (`inventory_documents`) con trazabilidad completa.

## 🕒 Última Actividad (2026-04-09 12:30 PM)
**Flujo de Aprovisionamiento Masivo (Completado)**
1. **`flow_6_purchase_variants.py`**:
   - Implementada lógica de compra masiva. Registradas 100 unidades de cada una de las 15 variantes (1,500 unidades totales) en el almacén principal de Tijuana.
   - Generado folio `PURCHASE-` vinculado a una Orden de Compra externa simulada (`PO-`).
   - Verificado el cálculo de `total_amount` en USD en la cabecera del documento.
   - Activado el escalonamiento de capas FIFO (`available_quantity`) para futuras salidas.

