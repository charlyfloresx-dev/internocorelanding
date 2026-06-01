# Tareas Consolidadas — 2026-06-01

## Completadas

### Phase 164 — Rate Limiter Global + RTR DB Worker + Migration drop ✅

**Rate limiter WMS/MES/HCM/Subscription:**
- `app.state.limiter = limiter` + `RateLimitExceeded` handler 429 en los 4 `main.py`
- Límites globales `2000/h · 100/min` activos en todos los servicios

**Migration `a9e3b1c0d2f4` aplicada:**
- `refresh_tokens` DROP completado. Root cause del lock: PID 4864 idle-in-transaction
  (`SAVEPOINT sa_savepoint_1`) del pool de auth_service. Fix: `pg_terminate_backend(4864)`
- `alembic_version_auth = a9e3b1c0d2f4` (head confirmado)

**DB Worker `purge_rtr_families.py`:**
- Purga familias con `refresh_window_expires_at < NOW()-7d`
- `text()` SQL nativo bypasa Event Listeners ORM append-only
- Ejecutar: `docker exec interno-auth-dev python /app/scripts/purge_rtr_families.py`

---

### Phase 163 — RTR Frontend Semaphore (Angular + Flutter) ✅

- Angular: `REFRESH_ABORT` sentinel + `authReq` fix en `multi-tenant.interceptor.ts`
- Flutter: `auth_interceptor.dart` nuevo con `Completer<String>` semaphore
- Verificado en vivo: login → dashboard sin errores

---

### Phase 162 RTR — Phase C Tests + Phase D Login Integration ✅

- 10/10 integration tests PASSED contra PostgreSQL real
- `select-company` emite `{ access_token, refresh_token (RTR gen=0) }` — Phase D completa
- Colaboradores: `refresh_token: null` (sin FK users.id en HCM)

---

### Phase 159 RTR — Auditoría A+B Correcciones ✅
- B-01, Stack trace leak, B-02, GAP-1, GAP-2, GAP-3 — todos resueltos

---

## Pendientes activos (por prioridad)

### ALTA
- **POS checkout E2E**: Validar `POST /api/v1/pos/checkout` — script `flow_pos_checkout.py` listo

### MEDIA
- PriceAgreement context en typeahead `GET /products/?q=`
- Mobile AVD Pixel 7 API 34 — dark/light theme + flujo de venta
- Domain purity: `log_rotation_event()` retorna ORM model

### BAJA
- Rate limit por-endpoint específico en WMS/MES/HCM/Subscription (global activo, faltan `@limiter.limit()` en mutaciones críticas)
- RTR AWS WAF: rate-limit perimetral ALB/CloudFront + pool_size/max_overflow
- RTR Observabilidad: alerta `REUSE_DETECTED` + dashboard sesiones activas
- GAP-5: `CompanyIdMismatchError → 401` ADR · GAP-6: `concurrent_attempt_detected`
- HCM `JobPosition`, `shift_id`, WMS deploy, MES `routing.py`
- Agentes `.github/agents/` — "NexoSuite" → "InternoCore"

## Code Graph Status (2026-06-01 Phase 164)
- 0 CRITICALs — 13 servicios CLEAN
- Ecosystem: 8/8 servicios OK
- `refresh_tokens` eliminada · `alembic_version_auth = a9e3b1c0d2f4`
