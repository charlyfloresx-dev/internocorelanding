# Historial Maestro de Implementación: 2026-05-22

Este documento registra los planes de diseño aprobados y decisiones arquitectónicas tomadas durante esta jornada para la integración del módulo de tickets en **Sentinel Mobile** (Phase 125) y la resolución del consecutivo de tickets multi-tenant aislado (Phase 126).

---

## 1. Decisiones Arquitectónicas (ADRs)

### ADR-04: Mapeo y Aislamiento del Consecutivo de Tickets Multi-Tenant
- **Contexto:** En el tickets_service original, el contador de folios (`reference_code` con patrón `TKT-YYYY-NNNN`) se calculaba globalmente, y la tabla de base de datos imponía un índice único global. Esto causaba dos problemas graves:
  1. Si la empresa A creaba un ticket, el contador global incrementaba, haciendo saltar la secuencia visible para la empresa B (violación de la coherencia operacional).
  2. Los tickets pre-sembrados de demostración industrial usaban prefijos específicos (`IT-`, `SEC-`, `EXT-`). El contador sólo buscaba el patrón `TKT-`, por lo que devolvía cero y causaba colisiones al iniciar secuencias desde `0001` en lugar de continuar tras el último consecutivo.
- **Decisión:** 
  1. Reemplazar la restricción de clave única global en la columna `reference_code` por una clave única compuesta `(company_id, reference_code)`. Esto garantiza aislamiento multitenancy total de folios a nivel de PostgreSQL.
  2. Modificar la función `_generate_ref_code` del repositorio para filtrar y contar los tickets de la empresa actual (`company_id`) creados en el año en curso, sin importar el prefijo (`%-2026-%`).
- **Consecuencias:** Cada tenant ahora mantiene de forma limpia y continuada su propio consecutivo desde el punto en el que se encuentre (incluyendo los pre-sembrados), garantizando la integridad funcional y visual del módulo.

---

## 2. Implementación Ejecutada

### Phase 125 — Sentinel Mobile Ticket Integration & Support Drawer Sync
- **Modelos de Datos (`ticket_models.dart`)**: Modelos `Ticket`, `TicketCreateRequest` y `TicketComment` creados para mapear los payloads del backend.
- **Capa de Repositorio (`ticket_repository.dart`)**: Consumo HTTP integrado vía `Dio` e inyección de dependencias `GetIt`. Inyección automática de `company_id` local desde `SharedPreferences` para aislar el multitenancy con cero fricción operacional.
- **Gestión de Estados (`tickets_bloc.dart`)**: Eventos y estados inyectados globalmente en la jerarquía de la app móvil para actualización en tiempo real de las bandejas `/mine` del operador.
- **Interfaces Modernas de Alto Contraste ("Uber-Style")**:
  - `tickets_screen.dart`: Listado dinámico con estadísticas rápidas (pendientes vs cerrados) y estados vacíos.
  - `create_ticket_screen.dart`: Formulario express minimalista con asunto, prioridad y descripción.
  - `ticket_chat_screen.dart`: Chat fluido con burbujas alineadas para operador vs supervisor, cabecera de metadatos y auto-scroll.

### Phase 126 — Multi-Tenant Isolated Ticket Consecutive Number Fix
- **Migración Alembic (`002_ref_code_composite.py`)**: 
  - Remoción segura de la clave única global `tickets_reference_code_key` sobre `tickets(reference_code)`.
  - Creación del nuevo índice único compuesto `tickets_company_id_reference_code_key` sobre `tickets(company_id, reference_code)`.
  - Ejecutada exitosamente dentro del contenedor `interno-tickets-dev` contra PostgreSQL.
- **Actualización de Modelos ORM (`ticket.py`)**:
  - Remoción de `unique=True` en la definición de la columna `reference_code`.
  - Inyección de la restricción `UniqueConstraint("company_id", "reference_code")` en `__table_args__` del modelo `Ticket`.
- **Refactorización del Algoritmo de Folios (`ticket_repository.py`)**:
  - `_generate_ref_code` ahora busca tickets mediante el patrón `%-{current_year}-%` y filtra por `company_id`.
  - Detecta correctamente que la empresa pre-sembrada con 7 tickets debe emitir el siguiente como `TKT-2026-0008`, manteniendo la continuidad impecable.

---

## 3. Verificación Final (Phase 125-126)

| Prueba / Auditoría | Resultado |
|---|---|
| Code Graph (`generate_code_graph.py`) | ✅ 100% de cumplimiento en los 14 servicios (0 errores). |
| Ping Maestro (`validate_ecosystem.ps1`) | ✅ 8/8 microservicios OK y Gateway respondiendo. |
| Migración base de datos en contenedor | ✅ Aplicada con éxito (`002_ref_code_composite` upgrade head). |
| Esquema PostgreSQL real (`\d tickets`) | ✅ Restricción compuesta `tickets_company_id_reference_code_key` activa. |
| Coherencia de Consecutivo por Empresa | ✅ Lógica y restricciones alineadas para aislamiento de secuencias. |
