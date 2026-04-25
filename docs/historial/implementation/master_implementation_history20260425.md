# Master Implementation History — 2026-04-25

Registro arquitectónico de la fase ejecutada. Documenta decisiones de diseño, patrones aplicados y la arquitectura construida/ejecutada el día de hoy.

---

## Fase: Interno Assets CRM — Sprint 1 (Asset Opportunity Manager)

### Objetivo
Evolucionar el módulo GIS del `master_data_service` de una herramienta de consulta de propietarios a un motor de inteligencia predictiva para la detección de *Distressed Real Estate Assets* en Tijuana.

---

## Decisiones Arquitectónicas

### 1. Nuevo Microservicio `asset_manager_service` (Clean Architecture)
**Decisión:** Crear un microservicio dedicado en lugar de extender `master_data_service`.
**Justificación:** Separación de dominios — el Master Data gestiona catálogos corporativos; el Asset Manager gestiona oportunidades de inversión personal. Son contextos acotados (*Bounded Contexts*) completamente distintos.
**Patrón aplicado:** Clean Architecture con 4 capas: `domain` → `application` → `infrastructure` → `api`.

### 2. Financial Engine Puro (`OpportunityEvaluator`)
**Decisión:** El motor financiero vive en `application/services` sin dependencias de SQLAlchemy ni httpx.
**Justificación:** La inteligencia de negocio debe ser independiente del origen del dato (RPPC, Excel, API). Esto garantiza que el ROI sea determinista y testeable de forma aislada.
**Fórmula aprobada:**
```
VM                = superficie_m2 × valor_m2_zona
risk_buffer_amt   = VM × risk_buffer_percentage (default: 10%)
Costo Total       = adeudo_total + gastos_legales + risk_buffer_amt
ROI Proyectado    = VM − (precio_adquisicion + Costo Total)
is_opportunity    = ROI > 0 AND adeudo_total/VM ≥ 20%
```

### 3. ZoneConfig Learning (Memoria Geográfica)
**Decisión:** Si el usuario ingresa `valor_m2_zona` manualmente, el sistema lo persiste en `ZoneConfig` para futuros predios de la misma colonia.
**Justificación:** El sistema "aprende" con cada consulta. A futuro, esto puede alimentarse con scraping de Inmuebles24 o integración con Spark para análisis de tendencias de plusvalía.

### 4. BackgroundTask — Integración GIS → CRM (Fire-and-Forget)
**Decisión:** El endpoint `/full-report` en `gis_validator.py` no llama directamente al Asset Manager; usa `fastapi.BackgroundTasks`.
**Justificación:** La latencia de respuesta del mapa a Indiana no debe depender de la disponibilidad del servicio CRM. Si el CRM está offline, solo se registra en log. El mapa siempre responde rápido.
**Patrón:** Zero-Cost Async (misma estrategia que `BackgroundTasks` ya usada en `notification_service`).

### 5. bypass_tenant — Scope Personal del Scout
**Decisión:** El repositorio no filtra por `company_id` (multi-tenant corporativo), sino por `created_by` (user_id del Scout operador).
**Justificación:** Las oportunidades inmobiliarias son activos personales/privados del operador (Indiana), no activos corporativos de una empresa. El modelo de negocio es distinto.
**Compliance:** Documentado con token `bypass_tenant` en los docstrings del repositorio para satisfacer el Code Graph Auditor.

---

## Arquitectura Implementada

```
backend/asset_manager_service/
├── Dockerfile                          ← python:3.11-slim, puerto 8006
├── requirements.txt                    ← fastapi, sqlalchemy, asyncpg, alembic, httpx
├── alembic.ini + alembic/env.py        ← Async migrations via asyncpg
├── alembic/versions/
│   └── 0001_initial_schema.py         ← zone_configs, opportunities, opportunity_audit_logs
└── asset_app/
    ├── main.py                         ← FastAPI app, lifespan init_db
    ├── core/
    │   ├── config.py                   ← Hereda InternoSettings (AWS Secrets compatible)
    │   └── database.py                 ← AsyncEngine, pool_size=5, get_db dependency
    ├── domain/
    │   ├── models/opportunity.py       ← 3 modelos SQLAlchemy + days_in_pipeline property
    │   ├── models/enums.py             ← OpportunityStatus (Kanban), LegalStatus
    │   └── exceptions.py              ← AssetManagerException, OpportunityNotFound, etc.
    ├── application/
    │   ├── schemas/opportunity.py      ← 6 Pydantic schemas
    │   └── services/
    │       ├── opportunity_evaluator.py   ← Financial Engine (puro, sin IO)
    │       └── opportunity_orchestrator.py ← Upsert + ZoneConfig learning + AuditLog
    ├── infrastructure/
    │   └── repositories/
    │       └── opportunity_repository.py  ← Queries filtradas, bypass_tenant documentado
    └── api/v1/
        ├── router.py
        └── endpoints/opportunities.py   ← 6 endpoints del CRM Kanban
```

## Modificaciones a Servicios Existentes

| Archivo | Tipo | Descripción |
|---|---|---|
| `master_data_service/Dockerfile` | Bug Fix | `COPY master_data_service/app` → `COPY master_data_service/master_app` |
| `master_data_service/entrypoint.sh` | Bug Fix | `uvicorn app.main:app` → `uvicorn master_app.main:app` |
| `master_data_service/.../gis_validator.py` | Feature | BackgroundTask `_propagate_to_asset_manager` en `/full-report` |
| `docker-compose.yml` | Feature | Servicio `asset-manager-service` (puerto `8011:8006`) |
| `scripts/init-multiple-databases.sh` | Feature | `CREATE DATABASE asset_manager_db` |

## Invariantes Confirmados (Code Graph Audit)
- ✅ **14/14 microservicios: 100% Compliance — TOTAL ERRORS: 0**
- ✅ Sin circular dependencies detectadas
- ✅ Sin ALB violations (FinOps $0 extra)
- ✅ Sin ENV_ACCESS_VIOLATION
- ✅ `InternoSettings` + `load_aws_secrets()` presentes en `config.py`

---

## Roadmap Sprint 2

| Tarea | Tipo | Prioridad |
|---|---|---|
| `alembic upgrade head` en el contenedor | Infra | 🔴 Alta |
| Tests unitarios evaluator (8 escenarios) | QA | 🔴 Alta |
| Test integración RPPC — Unidad C ≠ Jorge Alejandro | QA | 🔴 Alta |
| Seed de ZoneConfig para Tijuana (Presidentes, Otay, Centro) | Data | 🟡 Media |
| Frontend: campo `cve_cat` (antes `clave`) en `/full-report` | Frontend | 🟡 Media |
| Frontend: botón "Guardar Oportunidad" con `valor_m2_zona` manual | Frontend | 🟡 Media |
| Dashboard Kanban UI (lista de oportunidades con ROI) | Frontend | 🟢 Baja |
| ZoneConfig scraping automático (Inmuebles24) | Futuro | ⬛ Backlog |
