# Audit Implementation Plan: Phase 3 (Domain Parity & CQRS)
**Date:** 2026-05-12
**Status:** In Progress
**Objective:** Ecosistema de Microservicios y Sincronía de Dominio (Paridad de Value Objects y Auditoría CQRS).

## 1. Paridad de Value Objects y Domain Exceptions (Cimientos)
- [x] Auditar y fortificar la precisión de `Money` (Decimal, ROUND_HALF_UP, composite_values).
- [x] Auditar inmutabilidad de `Address` (dataclass frozen) e inyectar validación estricta de Regex para Códigos Postales.
- [x] Homologar mapa de Excepciones para asegurar el contrato JSON (`code`, `message`, `meta.details`).
- [x] Validar serialización de Enums (String Enum compatibility).

## 2. Exterminio de Primitivos Inseguros (P0 - "Pecado del Float")
*Detonado tras hallazgo en Step 1.*
- [x] **Master Data Service**: Refactorizar `last_price` de `float` a `Decimal` en `product.py` schema y en el SQLAlchemy repository casting.
- [x] **Inventory Service**: Refactorizar `unit_price`, `last_purchase_price` y `replacement_price` a `Decimal` en `inventory.py` y `pos.py`.
- [x] **Subscription Service**: Refactorizar la columna de base de datos de SQLAlchemy de `Mapped[float]` a `Mapped[Decimal] = mapped_column(Numeric(18, 4))` en `subscription.py`.
- [x] **Validación Unitaria**: Generar prueba en `backend/tests/test_precision_p0.py` confirmando la inmunidad al error `0.1 + 0.2 = 0.30000000000000004`.
- [x] **Code Graph Enforcement**: Actualizar `generate_code_graph.py` para detectar y bloquear el uso de `: float` o `Mapped[float]` en directorios `/models/` y `/schemas/`.

## 3. Auditoría CQRS y Segregación
- [ ] Auditar flujos de *Commands* (Escritura) en MES/WMS para verificar Atomicidad (Unit of Work).
- [ ] Auditar flujos de *Queries* (Lectura) para asegurar que se utilicen proyecciones sin rastros de lógica de base de datos o side-effects.
- [ ] Verificación de Invariantes: Ningún Command debe devolver entidades complejas, solo el Status y el ID. Las Queries nunca deben alterar el estado del sistema.
