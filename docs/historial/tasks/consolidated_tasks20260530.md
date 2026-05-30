# Tareas Consolidadas — 2026-05-30

## Completadas

### Phase 161 — MES StandardTime sequence_number ✅
- Migración `011_st_sequence_number`: ADD COLUMN nullable → backfill ROW_NUMBER()*10 → NOT NULL
- Modelo `StandardTime.sequence_number: Mapped[int]` con `server_default='10'`
- Endpoints actualizados (schemas + order_by); nuevo `GET /route/{item_code}`
- 4 nuevos tests: defaults, custom values, route ordering, update — 14/14 GREEN
- Angular: columna badge teal, campo sequence_number en formulario, visualización ruta `10·CORTE → 20·SOLDADURA`

### Fix — master_data_service seed self-healing default_tax_rate ✅
- `companies_to_seed` ahora incluye `"tax"` explícito por empresa (Planta US = 0.0)
- Corrección automática en cada startup: `elif Decimal(str(existing.default_tax_rate)) != co["tax"]`
- Descubierto y corregido: migración `g001_add_company_internal_id_pattern.py` faltaba desde Phase 118

### Auditoría de Seguridad Phase A RTR ✅
- Revisión formal del domain model de auth_service Phase 159 RTR
- Todos los puntos críticos APROBADOS: `@dataclass(frozen=True)`, `hmac.compare_digest()`, 7 excepciones, índices, FKs CASCADE
- 3 gaps documentados en CLAUDE.md §13 y SERVICE_LOG auth_service (todos bloqueados hasta Phase 159 RTR)

## Pendientes activos (por prioridad)

### ALTA — Bloqueada
- **POS checkout end-to-end** (`flow_pos_checkout.py`): bloqueado por auth_service Phase 159 RTR

### MEDIA
- Rate limit por endpoint en WMS, MES, HCM, Subscription
- PriceAgreement context en typeahead `GET /products/?q=`
- Mobile AVD (Pixel 7 API 34) — dark/light theme + flujo de venta
- **auth_service RTR GAP-1**: `TokenFamily.family_salt` sin validador hex en `__post_init__`
- **auth_service RTR GAP-2**: `version_counter` no mapeado a ORM locking — confirmar en handler

### BAJA
- HCM `JobPosition` catálogo propio
- HCM `shift_id` en Collaborator → bridge HCM↔MES
- **auth_service RTR GAP-3**: `RefreshTokenRotationAudit` hereda soft-delete de MultiTenantBase
- **auth_service seed**: `default_tax_rate` Planta US en hard reset
- WMS no desplegado
- Agentes `.github/agents/` con nombre "NexoSuite" antiguo
- MES `routing.py` vacío

## Code Graph Status
- Total errores: 1 (WARNING, auth_service — MISSING_TENANT_FILTER en sqlalchemy_refresh_token_repo.py — RTR en progreso)
- 12/13 servicios: 100% compliance
- 0 CRITICALs en el ecosistema
