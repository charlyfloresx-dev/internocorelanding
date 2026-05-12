# InternoCore: Plan de Implementación de Auditoría Multitenant (Muro de Hierro)

Este plan está diseñado específicamente para la arquitectura híbrida de InternoCore, priorizando el backend en Python (FastAPI/SQLAlchemy) que interactúa con la base de datos compartida.

## Fase 1: Reconocimiento Estático y Tooling (Semanas 1-2)
**Objetivo:** Establecer las herramientas automatizadas y mapear la superficie de riesgo en el código base.

1.  **Configuración de Análisis de Código Estático (SAST)**
    *   **Acción:** Configurar reglas personalizadas en Semgrep o Ruff para el backend de Python.
    *   **Regla Crítica:** Detectar el uso de `text()`, `.execute()`, o `conn.execute()` provenientes de SQLAlchemy sin la presencia de parámetros `company_id` o `tenant_id`.
    *   **Regla de Modelos:** Alertar si un nuevo modelo en `backend/common/models` hereda directamente de `Base` en lugar de `MultiTenantBase` (a menos que esté explícitamente en una whitelist).

2.  **Mapeo de Puntos de Inyección Raw SQL**
    *   **Acción:** Realizar un escaneo manual (`grep_search` o búsqueda en IDE) de todos los repositorios (WMS, HCM, Inventory) buscando consultas crudas, especialmente en módulos de reportes (ej. Anexo 24).
    *   **Entregable:** Inventario de Consultas Manuales con estado de cumplimiento (Pasa/Falla).

## Fase 2: Auditoría del "ADN" y Propagación de Contexto (Semanas 3-4)
**Objetivo:** Validar que el `MultiTenantBase` y la sesión de base de datos impongan el aislamiento por diseño.

1.  **Auditoría de SQLAlchemy `with_loader_criteria`**
    *   **Acción:** Revisar la inicialización de `SessionLocal` o el middleware de persistencia en `backend/common/infrastructure/database.py`.
    *   **Criterio de Éxito:** Debe existir un evento (`@event.listens_for(AsyncSession, "do_orm_execute")`) que inyecte `with_loader_criteria` para interceptar todas las lecturas de clases que heredan de `MultiTenantBase` y aplique el filtro del tenant de forma transparente (el "Muro de Hierro").

2.  **Validación de `ContextVars` (Async Context)**
    *   **Acción:** Revisar el middleware de FastAPI (ej. `InternoCoreGlobalMiddleware`).
    *   **Criterio de Éxito:** El `company_id` extraído del JWT debe almacenarse en un `contextvars.ContextVar`. Se debe verificar obligatoriamente que el middleware llame a `request_context.reset(token_ctx)` en el bloque `finally` para evitar cruces de sesión entre peticiones asíncronas bajo alta concurrencia.

3.  **Inmutabilidad de `company_id` en Escritura y `before_flush`**
    *   **Acción:** Auditar los DTOs, schemas de Pydantic y el ciclo de vida de SQLAlchemy.
    *   **Criterio de Éxito:** Se debe implementar un evento `@event.listens_for(AsyncSession, "before_flush")` (o equivalente en `Session`) que fuerce la asignación de `company_id` directamente desde el `request_context` en cada operación de `INSERT` o creación de entidades que heredan de `MultiTenantBase`, ignorando y sobreescribiendo cualquier valor que el cliente envíe en el JSON. Además, un `UPDATE` masivo generado por SQLAlchemy no debe modificar esta columna.

## Fase 3: Auditoría Forense y Edge Cases Industriales (Semana 5)
**Objetivo:** Validar la seguridad en cruces de datos complejos y trazabilidad.

1.  **Auditoría de `AuditBase` e Inmutabilidad Forense**
    *   **Acción:** Verificar que `SecurityAuditLog` y `AuditLog` capturen siempre el `company_id`. Confirmar que no existan endpoints o roles (ni siquiera God Mode) con capacidad de ejecutar `DELETE` sobre estas tablas.

2.  **Auditoría de Caché (Redis) y Almacenamiento (S3)**
    *   **Acción:** Inspeccionar la estructura de claves en el módulo de caché. Todas deben seguir el patrón `tenant:{uuid}:...`.
    *   **Acción:** Auditar el gestor de documentos. Las rutas de S3/Local Storage deben iniciar con el UUID de la empresa.

## Fase 4: Pruebas Dinámicas y Penetración (DAST) (Semana 6)
**Objetivo:** Intentar vulnerar activamente el aislamiento en un entorno de pruebas idéntico a producción (Staging).

1.  **Ejecución de "Tenant Hopping"**
    *   **Acción:** Con un token válido de "Empresa A", realizar llamadas a la API intentando acceder a IDs de productos, órdenes o usuarios conocidos de la "Empresa B".
    *   **Criterio de Éxito:** El sistema debe responder estrictamente `404 Not Found` (preferible) o `403 Forbidden` sin filtrar metadata.

2.  **Inyección de Identificadores Cruzados (IDOR)**
    *   **Acción:** En un payload de creación (POST), inyectar manualmente `"company_id": "UUID_DE_OTRA_EMPRESA"`.
    *   **Criterio de Éxito:** El backend debe ignorar silenciosamente ese valor o rechazar el payload (422/400), utilizando siempre el contexto seguro inyectado en el servidor.

## Fase 5: Hardening de Defensa en Profundidad (Semana 7-8)
**Objetivo:** Aplicar las mitigaciones técnicas basadas en los hallazgos de las fases anteriores.

1.  **Implementación de Row Level Security (RLS) en PostgreSQL**
    *   **Acción:** Generar scripts de migración (Alembic) para activar RLS en todas las tablas sensibles (`inventory_transactions`, `work_orders`, etc.).
    *   **Acción:** Configurar el hook de SQLAlchemy para ejecutar `SET app.current_tenant = :tenant_id` al tomar una conexión del pool.

2.  **Restricciones a Nivel de Base de Datos**
    *   **Acción:** Asegurar que los constraints lógicos existan físicamente (ej. `CHECK (company_id IS NOT NULL)` y claves únicas que incluyan `company_id`).

3.  **Re-Certificación (El Sello Final)**
    *   **Acción:** Ejecutar nuevamente las pruebas de Tenant Hopping (Fase 4). Si todas pasan sin exposición de datos, se emite el certificado interno de cumplimiento multitenant.
