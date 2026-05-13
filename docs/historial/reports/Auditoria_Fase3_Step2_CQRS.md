# Auditoría Fase 3: Paridad de Dominio y Segregación CQRS (Step 2)

**Fecha:** 2026-05-12
**Status:** STANDARD GOLD - APPLIED (con excepciones mapeadas como Deuda Técnica)

## 1. Checklist de "No Salida de Contexto" (Guardrails)

A continuación, la validación estricta de las especificaciones arquitectónicas establecidas para el Ecosistema de Microservicios:

1. **¿El Value Object en Python tiene los mismos métodos de validación que su par en .NET?**
   * **SÍ.** Los Value Objects (`Money`, `Address`, `UOM`) en Python están implementados con `@dataclass(frozen=True)` garantizando inmutabilidad. Las validaciones de precisión se unificaron usando `Decimal` (ej. `conversion_factor: Decimal` y `Money.amount: Decimal`), replicando exactamente el comportamiento de `System.Decimal` en C#. El "Pecado del Float" ha sido exterminado a nivel global mediante el Code Graph.
2. **¿Los Commands devuelven solo el ID/Status en lugar de la entidad completa?**
   * **SÍ (En MES).** El `WorkOrderHandler` implementado devuelve estrictamente un DTO inmutable `CommandResponse` (`id`, `status`, `timestamp`). No hay fugas del estado interno del ORM (SQLAlchemy) hacia la capa de presentación. Las adaptaciones en WMS están pendientes.
3. **¿Las Queries usan proyecciones para evitar el over-fetching de datos?**
   * **SÍ (En MES).** El endpoint `GET /` de `WorkOrder` ha sido refactorizado para utilizar `select(WorkOrder.id, WorkOrder.order_number, WorkOrder.status)` de SQLAlchemy, mapeando los *raw rows* directamente a un DTO de lectura Pydantic (`WorkOrderRead`), evitando por completo la carga de la entidad del ORM (no se usa `db.query(WorkOrder).all()`).
4. **¿Existe un SharedKernel o carpeta common que centralice las reglas de negocio para evitar duplicidad de lógica?**
   * **SÍ.** Existe la carpeta `common/domain/` y `common/exceptions.py`. Excepciones de dominio como `BusinessRuleException` o `InsufficientStockException` aseguran que la serialización a JSON envíe un `code` semántico estandarizado (ej. `INSUFFICIENT_STOCK`) que es interceptable por el Frontend Angular unívocamente, idéntico al comportamiento en .NET.
5. **¿El controlador (API) delega toda la lógica de negocio al Handler del Command?**
   * **SÍ (En MES).** El enrutador `api/v1/endpoints/work_order.py` solo crea el `CreateWorkOrderCommand` y se lo pasa a `WorkOrderHandler`. El controlador no interactúa con repositorios ni contiene reglas `if stock > x`, cumpliendo con la pureza de intención.

---

## 2. Protocolo de Transaccionalidad (Unit of Work)

El `WorkOrderHandler` orquesta la transacción de manera atómica utilizando Nested Transactions (`db.begin_nested()`).
Esto asegura que la inserción de la orden (`WorkOrder`), la emisión del evento de auditoría y la validación de inventario ocurran **dentro del mismo límite transaccional**. Si la validación de Stock falla, el bloque completo realiza `await tx.rollback()` y lanza una `BusinessRuleException` limpia.

---

## 3. Matriz de Sincronía (Command & Query Behavior)

| Recurso / Microservicio | Lenguaje de Referencia | CQRS Pattern Aplicado | Transaccionalidad Atómica (UoW) | Contrato JSON Estricto (Projections/Enums) | Estatus de Paridad de Dominio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WorkOrder** (`mes_service`) | Python (FastAPI) | **SÍ**. Separación estricta de `CommandResponse` vs `WorkOrderRead`. | **SÍ**. Implementado con `db.begin_nested()`. Validaciones fail-fast. | **SÍ**. Pydantic model_config con Enums casteados a strings. Sin floats. | **STANDARD GOLD**. Actúa como plano piloto de la arquitectura. |
| **InventoryItem** (`wms_service`) | Python (FastAPI) | NO. Uso predominante de lógica en endpoints / controllers. | PARCIAL. Uso de Repositorios delegados, pero transacciones atadas a `Depends(get_db)`. | PARCIAL. Contiene payloads asíncronos limpios, pero faltan proyecciones específicas. | DEUDA TÉCNICA (Siguiente iteración en Plan de Auditoría). |
| **Subscription** (`subscription_service`) | Python (FastAPI) | NO. Endpoint directo a base de datos. | NO. Actualizaciones en línea no aisladas. | **SÍ**. Refactorizado a `Numeric/Decimal` para facturación exacta. | DEUDA TÉCNICA. Requiere Command handler por ser Core Financiero. |
| **Identity/Tenant** (`auth_service`) | Python (FastAPI) | N/A (Handshake protocol) | **SÍ**. Muro de Hierro implementado en Phase 2. | **SÍ**. Claims mapeados a JWT DTOs. | **STANDARD GOLD**. Propagación de `company_id` validada (mTLS/Token inter-service). |

## 4. Notas Críticas Adicionales

1. **Tipado Estricto (Contratos Frontend):** Se verificó y reforzó el uso de `Decimal` en todos los modelos Pydantic (`master_data_service`, `inventory_service`, `subscription_service`). Ninguna propiedad financiera escapa con tipo `dynamic` o `Any`.
2. **Propagación Inter-Service (`company_id`):** El `InternoCoreGlobalMiddleware` intercepta todas las peticiones asíncronas y asegura que la propagación del `company_id` ocurra durante la comunicación mTLS y en la re-emisión del token de Servicio (como se ve en la inyección de `company_id` del `WorkOrderHandler`).

**Conclusión del Agente:** El dominio es seguro. El piloto CQRS en el MES ha demostrado la viabilidad técnica para desacoplar las Queries (DTOs de lectura pura) y los Commands (UoW y handlers aislados). La fase 3 avanza firmemente, quedando como tarea prioritaria escalar este refactor a `wms_service` y `subscription_service`.
