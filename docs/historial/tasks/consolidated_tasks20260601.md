# Tareas Consolidadas — 2026-06-01

## Completadas

### Phase 166 — Auditoría Cross-File + Security Hardening ✅

**Auditoría transversal de todos los `consolidated_tasks` (Marzo–Junio 2026):**

**Falsos pendientes resueltos** (aparecían en docs pero existían en código desde antes):
- `internal_id_pattern` en `hr_tenant_configs` — existe en `tenant_settings.py` + `collaborator_service.py`
- `audit_logs` hcm_db y subscription_db — migrations `001_add_audit_logs.py` en ambos (Phase 118)
- `material_status` en WorkOrder — columna existe en `mes_service/models/work_order.py:26`
- Point-in-Time pricing — endpoint `/products/{product_id}/price-at` existe en `prices.py:817`

**Correcciones de seguridad aplicadas:**
- CORS wildcard: `kiosk_service` y `asset_manager_service` usaban `allow_origins=["*"]` — reemplazado con `setup_cors(app)`
- God Mode timing attack: `admin.py` usaba `!=` (no constante-time) — reemplazado con `hmac.compare_digest()`
- Agentes: `global_rules.md`, `Orquestator.agent.md`, `Migration.agent.md`, `Supervisor.agent.md` — "NexoSuite" → "InternoCore"

---

### Phase 165 — HARD_FK_CROSS_SERVICE 0 CRITICALs ✅

- WMS: 6 tablas mirror renombradas a `wms_*` schema
- Code Graph: `CROSS_DB_SHARED_TABLES` para `inventory_item_variants`

---

### Phase 164 — Rate Limiter + RTR DB Worker + Migration drop ✅

- `app.state.limiter` en WMS/MES/HCM/Subscription
- `purge_rtr_families.py` — DB Worker cron
- Migration `a9e3b1c0d2f4` aplicada — `refresh_tokens` DROP

---

### Phase 163 — RTR Frontend Semaphore ✅
### Phase 162 — RTR Phase C Tests + Phase D Login ✅
### Phase 159 — RTR Auditoría A+B ✅

---

## Pendientes activos (por prioridad)

### ALTA
- **POS checkout E2E**: `POST /api/v1/pos/checkout` — script `flow_pos_checkout.py` listo. Ejecutar contra stack real.

### MEDIA
- **NAIVE_DATETIME** (8 archivos): `datetime.utcnow()` → `datetime.now(timezone.utc)` en:
  - `auth_service/commands/complete_registration_command.py`
  - `auth_service/commands/invite_user_command.py`
  - `auth_service/infrastructure/repositories/sqlalchemy_refresh_token_repo.py`
  - `inventory_service/api/v1/endpoints/inventory.py`
  - `inventory_service/api/v1/endpoints/demo_reset.py`
  - `inventory_service/infrastructure/repositories/sqlalchemy_inventory_repository.py`
  - `tickets_service/services/ticket_service.py`
  - `wms_service/infrastructure/repositories/__init__.py`
- **PriceAgreement typeahead**: `GET /api/v1/products?q=` no acepta `partner_id` — no consulta PriceAgreements al buscar en typeahead
- Mobile AVD Pixel 7 API 34 — dark/light theme + flujo de venta completo
- Domain purity: `log_rotation_event()` retorna ORM model

### BAJA
- Rate limit por-endpoint `@limiter.limit()` en mutaciones críticas WMS/MES/HCM/Subscription
- RTR AWS WAF + Observabilidad (REUSE_DETECTED alertas) — pendiente cloud
- GAP-5/GAP-6 RTR (ADR + concurrent_attempt_detected)
- HCM `JobPosition` catálogo, `shift_id` bridge HCM↔MES
- WMS no desplegado en dev stack (docker-compose.dev.yml sin entrada wms_service)
- MES `routing.py` vacío — `Rout` model sin implementar
- Offline buffer SQLite mobile

## Code Graph Status (2026-06-01 Phase 166)
- 0 CRITICALs ✅
- 8 WARNINGs NAIVE_DATETIME activos
- 14 invariantes activos (Rev163 + Rev166)
